# stdlib
import re

# 3rd party
import click
import pytest
from coincidence.regressions import AdvancedFileRegressionFixture
from consolekit.testing import CliRunner, Result
from consolekit.tracebacks import handle_tracebacks
from dom_toml.parser import BadConfigError
from domdf_python_tools.paths import PathPlus, in_directory
from pyproject_examples import valid_buildsystem_config, valid_pep621_config
from pyproject_examples.example_configs import COMPLETE_A, COMPLETE_A_WITH_FILES, COMPLETE_B, COMPLETE_PROJECT_A

# this package
from pyproject_parser.__main__ import CustomTracebackHandler, check, reformat
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


exceptions = pytest.mark.parametrize(
		"exception",
		[
				pytest.param(FileNotFoundError("foo.txt"), id="FileNotFoundError"),
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
		exception,
		file_regression,
		cli_runner: CliRunner,
		):

	@click.command()
	def demo():

		with handle_tracebacks(False, CustomTracebackHandler):
			raise exception

	result: Result = cli_runner.invoke(demo, catch_exceptions=False)
	result.check_stdout(file_regression)
	assert result.exit_code == 1


@exceptions
def test_traceback_handler_show_traceback(exception, cli_runner: CliRunner):

	@click.command()
	def demo():

		with handle_tracebacks(True, CustomTracebackHandler):
			raise exception

	with pytest.raises(type(exception), match=re.escape(str(exception))):
		cli_runner.invoke(demo, catch_exceptions=False)


@pytest.mark.parametrize("exception", [EOFError(), KeyboardInterrupt(), click.Abort()])
def test_handle_tracebacks_ignored_exceptions_click(
		exception,
		cli_runner: CliRunner,
		):

	@click.command()
	def demo():

		with handle_tracebacks(False, CustomTracebackHandler):
			raise exception

	result: Result = cli_runner.invoke(demo, catch_exceptions=False)

	assert result.stdout.strip() == "Aborted!"
	assert result.exit_code == 1


@pytest.mark.parametrize("exception", [EOFError, KeyboardInterrupt, click.Abort, SystemExit])
def test_handle_tracebacks_ignored_exceptions(exception, ):

	with pytest.raises(exception):  # noqa: PT012
		with handle_tracebacks(False, CustomTracebackHandler):
			raise exception
