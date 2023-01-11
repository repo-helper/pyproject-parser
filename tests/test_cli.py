# stdlib
import json
import re
import subprocess
import warnings
from typing import Optional, Type

# 3rd party
import click
import pytest
from coincidence.regressions import AdvancedDataRegressionFixture, AdvancedFileRegressionFixture
from consolekit.testing import CliRunner, Result
from consolekit.tracebacks import handle_tracebacks
from dom_toml.parser import BadConfigError
from domdf_python_tools.paths import PathPlus, in_directory
from pyproject_examples import valid_buildsystem_config, valid_pep621_config
from pyproject_examples.example_configs import (
		COMPLETE_A,
		COMPLETE_A_WITH_FILES,
		COMPLETE_B,
		COMPLETE_PROJECT_A,
		MINIMAL_CONFIG
		)

# this package
from pyproject_parser.__main__ import check, info, reformat
from pyproject_parser.cli import ConfigTracebackHandler
from tests.test_dumping import COMPLETE_UNDERSCORE_NAME, UNORDERED


@pytest.mark.parametrize(
		"toml_string",
		[
				pytest.param(COMPLETE_A, id="COMPLETE_A"),
				pytest.param(COMPLETE_A_WITH_FILES, id="COMPLETE_A_WITH_FILES"),
				pytest.param(COMPLETE_B, id="COMPLETE_B"),
				pytest.param(COMPLETE_PROJECT_A, id="COMPLETE_PROJECT_A"),
				pytest.param(UNORDERED, id="UNORDERED"),
				pytest.param(COMPLETE_UNDERSCORE_NAME, id="COMPLETE_UNDERSCORE_NAME"),
				]
		)
@pytest.mark.parametrize("show_diff", [True, False])
def test_reformat(
		tmp_pathplus: PathPlus,
		toml_string: str,
		cli_runner: CliRunner,
		advanced_file_regression: AdvancedFileRegressionFixture,
		show_diff: bool,
		):
	(tmp_pathplus / "pyproject.toml").write_clean(toml_string)
	(tmp_pathplus / "README.rst").write_clean("This is the README")
	(tmp_pathplus / "LICENSE").write_clean("This is the LICENSE")

	if show_diff:
		args = ["--no-colour", "--show-diff"]
	else:
		args = []

	with in_directory(tmp_pathplus):
		result: Result = cli_runner.invoke(reformat, args=args, catch_exceptions=False)

	assert result.exit_code == 1

	advanced_file_regression.check_file(tmp_pathplus / "pyproject.toml")
	result.check_stdout(advanced_file_regression, extension=".diff")

	# Should be no changes
	with in_directory(tmp_pathplus):
		result = cli_runner.invoke(reformat, args=args, catch_exceptions=False)

	assert result.exit_code == 0

	advanced_file_regression.check_file(tmp_pathplus / "pyproject.toml")
	assert result.stdout == "Reformatting 'pyproject.toml'\n"


@pytest.mark.parametrize("toml_string", [*valid_pep621_config, *valid_buildsystem_config])
def test_check(
		toml_string: str,
		tmp_pathplus: PathPlus,
		cli_runner: CliRunner,
		):
	(tmp_pathplus / "pyproject.toml").write_clean(toml_string)

	with in_directory(tmp_pathplus):
		result: Result = cli_runner.invoke(check, catch_exceptions=False)

	assert result.exit_code == 0
	assert result.stdout == "Validating 'pyproject.toml'\n"


@pytest.mark.parametrize(
		"toml_string",
		[
				pytest.param(
						'[project]\nname = "foo"\nversion = "1.2.3"\n[project.optional-dependencies]\n"dev_test" = []\n"dev-test" = []',
						id="duplicate_extra_1",
						),
				pytest.param(
						'[project]\nname = "foo"\nversion = "1.2.3"\n[project.optional-dependencies]\n"dev-test" = []\n"dev_test" = []',
						id="duplicate_extra_2",
						),
				pytest.param(
						'[project]\nname = "foo"\nversion = "1.2.3"\n[project.optional-dependencies]\n"dev.test" = []\n"dev_test" = []',
						id="duplicate_extra_3",
						),
				]
		)
def test_check_extra_deprecation(
		toml_string: str,
		tmp_pathplus: PathPlus,
		cli_runner: CliRunner,
		advanced_file_regression: AdvancedFileRegressionFixture,
		):
	(tmp_pathplus / "pyproject.toml").write_clean(toml_string)
	cli_runner.mix_stderr = False

	with in_directory(tmp_pathplus), warnings.catch_warnings():
		warnings.simplefilter("error")
		result: Result = cli_runner.invoke(check, catch_exceptions=False)

	assert result.exit_code == 1
	assert result.stdout == "Validating 'pyproject.toml'\n"
	advanced_file_regression.check(result.stderr)


@pytest.mark.parametrize(
		"toml_string",
		[
				pytest.param(
						'[project]\nname = "foo"\nversion = "1.2.3"\n[project.optional-dependencies]\n"dev_test" = []\n"dev-test" = []',
						id="duplicate_extra_1",
						),
				pytest.param(
						'[project]\nname = "foo"\nversion = "1.2.3"\n[project.optional-dependencies]\n"dev-test" = []\n"dev_test" = []',
						id="duplicate_extra_2",
						),
				pytest.param(
						'[project]\nname = "foo"\nversion = "1.2.3"\n[project.optional-dependencies]\n"dev.test" = []\n"dev_test" = []',
						id="duplicate_extra_3",
						),
				]
		)
def test_check_extra_deprecation_warning(
		toml_string: str,
		tmp_pathplus: PathPlus,
		cli_runner: CliRunner,
		advanced_file_regression: AdvancedFileRegressionFixture,
		):
	(tmp_pathplus / "pyproject.toml").write_clean(toml_string)

	args = ["pyproject-parser", "check"]

	with in_directory(tmp_pathplus):
		process = subprocess.run(
				args,
				stderr=subprocess.STDOUT,
				stdout=subprocess.PIPE,
				)
	assert process.returncode == 0

	advanced_file_regression.check(process.stdout.decode("UTF-8"))


@pytest.mark.parametrize(
		"toml_string, match",
		[
				pytest.param(
						"[build-system]\nrequires = []\nfoo = 'bar'",
						r"Unknown key in '\[build-system\]': 'foo'",
						id="build-system",
						),
				pytest.param(
						"[project]\nname = 'whey'\nfoo = 'bar'\nbar = 123\ndynamic = ['version']",
						r"Unknown keys in '\[project\]': 'bar' and 'foo",
						id="project",
						),
				pytest.param(
						"[coverage]\nomit = 'demo.py'\n[flake8]\nselect = ['F401']",
						"Unexpected top-level key 'coverage'. Only 'build-system', 'project' and 'tool' are allowed.",
						id="top-level",
						),
				pytest.param(
						"[build_system]\nbackend = 'whey'",
						"Unexpected top-level key 'build_system'. Did you mean 'build-system'",
						id="top_level_typo_underscore",
						),
				pytest.param(
						"[Build-System]\nbackend = 'whey'",
						"Unexpected top-level key 'Build-System'. Did you mean 'build-system'",
						id="top_level_typo_caps",
						),
				]
		)
def test_check_error(
		toml_string: str,
		tmp_pathplus: PathPlus,
		match: str,
		cli_runner: CliRunner,
		):
	(tmp_pathplus / "pyproject.toml").write_clean(toml_string)

	with pytest.raises(BadConfigError, match=match), in_directory(tmp_pathplus):
		cli_runner.invoke(check, catch_exceptions=False, args=["-T"])


@pytest.mark.parametrize(
		"toml_string",
		[
				pytest.param(
						"[build-system]\nrequires = []\nfoo = 'bar'",
						id="build-system",
						),
				pytest.param(
						"[project]\nname = 'whey'\nfoo = 'bar'\nbar = 123\ndynamic = ['version']",
						id="project",
						),
				pytest.param(
						"[coverage]\nomit = 'demo.py'\n[flake8]\nselect = ['F401']",
						id="top-level",
						),
				pytest.param(
						"[build_system]\nbackend = 'whey'",
						id="top_level_typo_underscore",
						),
				pytest.param(
						"[Build-System]\nbackend = 'whey'",
						id="top_level_typo_caps",
						),
				pytest.param(
						'[project]\nname = "???????12345=============☃"\nversion = "2020.0.0"', id="bad_name"
						),
				pytest.param('[project]\nname = "spam"\nversion = "???????12345=============☃"', id="bad_version"),
				pytest.param(
						f'{MINIMAL_CONFIG}\nrequires-python = "???????12345=============☃"',
						id="bad_requires_python"
						),
				pytest.param(f'{MINIMAL_CONFIG}\nauthors = [{{name = "Bob, Alice"}}]', id="author_comma"),
				]
		)
def test_check_error_caught(
		toml_string: str,
		tmp_pathplus: PathPlus,
		cli_runner: CliRunner,
		advanced_file_regression: AdvancedFileRegressionFixture,
		):
	(tmp_pathplus / "pyproject.toml").write_clean(toml_string)
	cli_runner.mix_stderr = False

	with in_directory(tmp_pathplus):
		result: Result = cli_runner.invoke(check)

	assert result.exit_code == 1
	assert result.stdout == "Validating 'pyproject.toml'\n"
	advanced_file_regression.check(result.stderr)


exceptions = pytest.mark.parametrize(
		"exception",
		[
				pytest.param(
						FileNotFoundError(2, "No such file or directory", "foo.txt"),
						id="FileNotFoundError",
						),
				pytest.param(
						FileNotFoundError(2, "No such file or directory", PathPlus("foo.txt")),
						id="FileNotFoundError_path"
						),
				pytest.param(
						FileNotFoundError(2, "No such file or directory", PathPlus("foo.txt"), -1, "bar.md"),
						id="FileNotFoundError_path_move_etc"
						),
				pytest.param(
						FileNotFoundError(2, "The system cannot find the file specified", "foo.txt"),
						id="FileNotFoundError_win",
						),
				pytest.param(
						FileNotFoundError(2, "The system cannot find the file specified", PathPlus("foo.txt")),
						id="FileNotFoundError_path_win"
						),
				pytest.param(
						FileNotFoundError(
								2,
								"The system cannot find the file specified",
								PathPlus("foo.txt"),
								-1,
								"bar.md",
								),
						id="FileNotFoundError_path_move_etc_win"
						),
				pytest.param(FileExistsError("foo.txt"), id="FileExistsError"),
				pytest.param(Exception("Something's awry!"), id="Exception"),
				pytest.param(ValueError("'age' must be >= 0"), id="ValueError"),
				pytest.param(TypeError("Expected type int, got type str"), id="TypeError"),
				pytest.param(NameError("name 'hello' is not defined"), id="NameError"),
				pytest.param(SyntaxError("invalid syntax"), id="SyntaxError"),
				pytest.param(BadConfigError("Expected a string value for 'name'"), id="BadConfigError"),
				pytest.param(KeyError("name"), id="KeyError"),
				pytest.param(AttributeError("type object 'list' has no attribute 'foo'"), id="AttributeError"),
				pytest.param(ImportError("No module named 'foo'"), id="ImportError"),
				pytest.param(ModuleNotFoundError("No module named 'foo'"), id="ModuleNotFoundError"),
				]
		)


@exceptions
def test_traceback_handler(
		exception: Exception,
		advanced_file_regression: AdvancedFileRegressionFixture,
		cli_runner: CliRunner,
		):

	@click.command()
	def demo():  # noqa: MAN002

		with handle_tracebacks(False, ConfigTracebackHandler):
			raise exception

	result: Result = cli_runner.invoke(demo, catch_exceptions=False)
	result.check_stdout(advanced_file_regression)
	assert result.exit_code == 1


@exceptions
def test_traceback_handler_show_traceback(exception: Exception, cli_runner: CliRunner):

	@click.command()
	def demo():  # noqa: MAN002

		with handle_tracebacks(True, ConfigTracebackHandler):
			raise exception

	with pytest.raises(type(exception), match=re.escape(str(exception))):
		cli_runner.invoke(demo, catch_exceptions=False)


@pytest.mark.parametrize("exception", [EOFError(), KeyboardInterrupt(), click.Abort()])
def test_handle_tracebacks_ignored_exceptions_click(
		exception: Exception,
		cli_runner: CliRunner,
		):

	@click.command()
	def demo():  # noqa: MAN002

		with handle_tracebacks(False, ConfigTracebackHandler):
			raise exception

	result: Result = cli_runner.invoke(demo, catch_exceptions=False)

	assert result.stdout.strip() == "Aborted!"
	assert result.exit_code == 1


@pytest.mark.parametrize("exception", [EOFError, KeyboardInterrupt, click.Abort, SystemExit])
def test_handle_tracebacks_ignored_exceptions(exception: Type[Exception]):

	with pytest.raises(exception):  # noqa: PT012
		with handle_tracebacks(False, ConfigTracebackHandler):
			raise exception


@pytest.mark.parametrize(
		"path",
		[
				pytest.param(None, id="all"),
				"build-system",
				"build-system.requires",
				pytest.param("build-system.requires.[0]", id="first_build_requirement"),
				"project",
				"project.authors",
				pytest.param("project.authors.[0]", id="first_author"),
				pytest.param("project.keywords.[3]", id="fourth_keyword"),
				"project.urls.Source Code",  # Written as `python3 -m pyproject_parser info project.urls."Source Code"`
				"tool.whey.base-classifiers"
				]
		)
@pytest.mark.parametrize("indent", [None, 0, 2, 4])
def test_info(
		path: str,
		tmp_pathplus: PathPlus,
		cli_runner: CliRunner,
		advanced_data_regression: AdvancedDataRegressionFixture,
		advanced_file_regression: AdvancedFileRegressionFixture,
		indent: Optional[int],
		):
	(tmp_pathplus / "pyproject.toml").write_clean(COMPLETE_A)

	if path is None:
		args = []
	else:
		args = [path]

	if indent:
		args.append("--indent")
		args.append(str(indent))

	with in_directory(tmp_pathplus):
		result: Result = cli_runner.invoke(info, catch_exceptions=False, args=args)

	print(result.stdout)
	assert result.exit_code == 0
	output = json.loads(result.stdout)

	if isinstance(output, str):
		advanced_file_regression.check(output, extension=".md")
	else:
		advanced_data_regression.check(output)
		advanced_file_regression.check(result.stdout, extension=".json")

	if path is None:
		args = []
	else:
		args = [path]

	if indent:
		args.append("-i")
		args.append(str(indent))

	with in_directory(tmp_pathplus):
		result = cli_runner.invoke(info, catch_exceptions=False, args=args)

	print(result.stdout)
	assert result.exit_code == 0
	output = json.loads(result.stdout)

	if isinstance(output, str):
		advanced_file_regression.check(output, extension=".md")
	else:
		advanced_data_regression.check(output)
		advanced_file_regression.check(result.stdout, extension=".json")


@pytest.mark.parametrize(
		"path",
		[
				"project.readme",
				"project.readme.file",
				"project.readme.text",
				"project.license",
				"project.license.file",
				"project.license.text",
				]
		)
@pytest.mark.parametrize("check_readme", [0, 1])
@pytest.mark.parametrize("indent", [None, 0, 2, 4])
@pytest.mark.parametrize("resolve", [True, False])
def test_info_readme_license(
		path: str,
		check_readme: int,
		tmp_pathplus: PathPlus,
		cli_runner: CliRunner,
		advanced_data_regression: AdvancedDataRegressionFixture,
		advanced_file_regression: AdvancedFileRegressionFixture,
		monkeypatch,
		resolve: bool,
		indent: Optional[int],
		):

	monkeypatch.setenv("CHECK_README", str(check_readme))

	(tmp_pathplus / "pyproject.toml").write_clean(COMPLETE_A_WITH_FILES)
	(tmp_pathplus / "README.rst").write_clean("This is the README")
	(tmp_pathplus / "LICENSE").write_clean("This is the LICENSE")

	args = [path]

	if resolve:
		args.append("--resolve")
	elif indent:
		args.append("--indent")
		args.append(str(indent))

	with in_directory(tmp_pathplus):
		result: Result = cli_runner.invoke(info, catch_exceptions=False, args=args)

	print(result.stdout)
	assert result.exit_code == 0
	output = json.loads(result.stdout)

	if isinstance(output, str):
		advanced_file_regression.check(output, extension=".md")
	else:
		advanced_data_regression.check(output)
		advanced_file_regression.check(result.stdout, extension=".json")

	args = [path, "-f", (tmp_pathplus / "pyproject.toml").as_posix()]

	if resolve:
		args.append("-r")
	elif indent:
		args.append("-i")
		args.append(str(indent))

	result = cli_runner.invoke(info, catch_exceptions=False, args=args)

	print(result.stdout)
	assert result.exit_code == 0
	output = json.loads(result.stdout)

	if isinstance(output, str):
		advanced_file_regression.check(output, extension=".md")
	else:
		advanced_data_regression.check(output)
		advanced_file_regression.check(result.stdout, extension=".json")
