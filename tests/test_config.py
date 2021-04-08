# stdlib
import re
from textwrap import dedent
from typing import Type

# 3rd party
import dom_toml
import pytest
from coincidence.regressions import AdvancedDataRegressionFixture
from dom_toml.parser import BadConfigError
from domdf_python_tools.compat import PYPY37
from domdf_python_tools.paths import PathPlus, in_directory

# this package
from pyproject_parser import BuildSystemParser, PEP621Parser, PyProject
from tests.example_configs import (
		AUTHORS,
		CLASSIFIERS,
		COMPLETE_A,
		COMPLETE_B,
		COMPLETE_PROJECT_A,
		DEPENDENCIES,
		ENTRY_POINTS,
		KEYWORDS,
		MAINTAINERS,
		MINIMAL_CONFIG,
		OPTIONAL_DEPENDENCIES,
		UNICODE,
		URLS
		)

valid_pep621_config = [
		pytest.param(MINIMAL_CONFIG, id="minimal"),
		pytest.param(f'{MINIMAL_CONFIG}\ndescription = "Lovely Spam! Wonderful Spam!"', id="description"),
		pytest.param(f'{MINIMAL_CONFIG}\nrequires-python = ">=3.8"', id="requires-python"),
		pytest.param(f'{MINIMAL_CONFIG}\nrequires-python = ">=2.7,!=3.0.*,!=3.2.*"', id="requires-python_complex"),
		pytest.param(KEYWORDS, id="keywords"),
		pytest.param(AUTHORS, id="authors"),
		pytest.param(MAINTAINERS, id="maintainers"),
		pytest.param(CLASSIFIERS, id="classifiers"),
		pytest.param(DEPENDENCIES, id="dependencies"),
		pytest.param(OPTIONAL_DEPENDENCIES, id="optional-dependencies"),
		pytest.param(URLS, id="urls"),
		pytest.param(ENTRY_POINTS, id="entry_points"),
		pytest.param(UNICODE, id="unicode"),
		pytest.param(COMPLETE_PROJECT_A, id="COMPLETE_PROJECT_A"),
		pytest.param(COMPLETE_A, id="COMPLETE_A"),
		pytest.param(COMPLETE_B, id="COMPLETE_B"),
		]

bad_pep621_config = [
		# pytest.param(
		# 		'[project]\nname = "spam"',
		# 		BadConfigError,
		# 		"The 'project.version' field must be provided.",
		# 		id="no_version"
		# 		),
		pytest.param(
				'[project]\n\nversion = "2020.0.0"',
				BadConfigError,
				"The 'project.name' field must be provided.",
				id="no_name"
				),
		pytest.param(
				'[project]\ndynamic = ["name"]',
				BadConfigError,
				"The 'project.name' field may not be dynamic.",
				id="dynamic_name"
				),
		pytest.param(
				'[project]\nname = "???????12345=============☃"\nversion = "2020.0.0"',
				BadConfigError,
				"The value for 'project.name' is invalid.",
				id="bad_name"
				),
		pytest.param(
				'[project]\nname = "spam"\nversion = "???????12345=============☃"',
				BadConfigError,
				re.escape("Invalid version: '???????12345=============☃'"),
				id="bad_version"
				),
		pytest.param(
				f'{MINIMAL_CONFIG}\nrequires-python = "???????12345=============☃"',
				BadConfigError,
				re.escape("Invalid specifier: '???????12345=============☃'"),
				id="bad_requires_python"
				),
		pytest.param(
				f'{MINIMAL_CONFIG}\nauthors = [{{name = "Bob, Alice"}}]',
				BadConfigError,
				r"The 'project.authors\[0\].name' key cannot contain commas.",
				id="author_comma"
				),
		pytest.param(
				f'{MINIMAL_CONFIG}\nmaintainers = [{{name = "Bob, Alice"}}]',
				BadConfigError,
				r"The 'project.maintainers\[0\].name' key cannot contain commas.",
				id="maintainer_comma"
				),
		pytest.param(
				f'{MINIMAL_CONFIG}\nkeywords = [1, 2, 3, 4, 5]',
				TypeError,
				r"Invalid type for 'project.keywords\[0\]': expected <class 'str'>, got <class 'int'>",
				id="keywords_wrong_type"
				),
		pytest.param(
				f'{MINIMAL_CONFIG}\nclassifiers = [1, 2, 3, 4, 5]',
				TypeError,
				r"Invalid type for 'project.classifiers\[0\]': expected <class 'str'>, got <class 'int'>",
				id="classifiers_wrong_type"
				),
		pytest.param(
				f'{MINIMAL_CONFIG}\ndependencies = [1, 2, 3, 4, 5]',
				TypeError,
				r"Invalid type for 'project.dependencies\[0\]': expected <class 'str'>, got <class 'int'>",
				id="dependencies_wrong_type"
				),
		pytest.param(
				f'{MINIMAL_CONFIG}\nreadme = "README.rst"',
				FileNotFoundError,
				"No such file or directory: 'README.rst'",
				id="missing_readme_file",
				marks=pytest.mark.skipif(PYPY37, reason="Message differs on PyPy 3.7")
				),
		pytest.param(
				f'{MINIMAL_CONFIG}\nlicense = {{file = "LICENSE.txt"}}',
				FileNotFoundError,
				"No such file or directory: 'LICENSE.txt'",
				id="missing_license_file",
				marks=pytest.mark.skipif(PYPY37, reason="Message differs on PyPy 3.7")
				),
		pytest.param(
				f'{MINIMAL_CONFIG}\nreadme = "README.rst"',
				FileNotFoundError,
				r"No such file or directory: .*PathPlus\('README.rst'\)",
				id="missing_readme_file",
				marks=pytest.mark.skipif(not PYPY37, reason="Message differs on PyPy 3.7")
				),
		pytest.param(
				f'{MINIMAL_CONFIG}\nlicense = {{file = "LICENSE.txt"}}',
				FileNotFoundError,
				r"No such file or directory: .*PathPlus\('LICENSE.txt'\)",
				id="missing_license_file",
				marks=pytest.mark.skipif(not PYPY37, reason="Message differs on PyPy 3.7")
				),
		]

valid_buildsystem_config = [
		pytest.param('[build-system]\nrequires = []', id="requires_nothing"),
		pytest.param('[build-system]\nrequires = ["whey"]', id="requires_whey"),
		pytest.param('[build-system]\nrequires = ["setuptools", "wheel"]', id="requires_setuptools"),
		pytest.param('[build-system]\nrequires = ["whey"]\nbuild-backend = "whey"', id="complete"),
		pytest.param(
				'[build-system]\nrequires = ["whey"]\nbuild-backend = "whey"\nbackend-path = ["../foo"]',
				id="backend_path"
				),
		pytest.param(
				'[build-system]\nrequires = ["whey"]\nbuild-backend = "whey"\nbackend-path = ["../foo", "./bar"]',
				id="backend_paths"
				),
		]

bad_buildsystem_config = [
		pytest.param(
				'[build-system]\nbackend-path = ["./foo"]',
				BadConfigError,
				"The 'build-system.requires' field must be provided.",
				id="no_requires"
				),
		pytest.param(
				'[build-system]\nrequires = [1234]',
				TypeError,
				r"Invalid type for 'build-system.requires\[0\]': expected <class 'str'>, got <class 'int'>",
				id="requires_list_int"
				),
		pytest.param(
				'[build-system]\nrequires = "whey"',
				TypeError,
				"Invalid type type for 'build-system.requires': expected <class 'collections.abc.Sequence'>, got <class 'str'>",
				id="requires_str"
				),
		pytest.param(
				'[build-system]\nrequires = ["whey"]\nbackend-path = [1234]',
				TypeError,
				r"Invalid type for 'build-system.backend-path\[0\]': expected <class 'str'>, got <class 'int'>",
				id="backend_path_list_int"
				),
		pytest.param(
				'[build-system]\nrequires = ["whey"]\nbackend-path = "whey"',
				TypeError,
				"Invalid type type for 'build-system.backend-path': expected <class 'collections.abc.Sequence'>, got <class 'str'>",
				id="backend_path_str"
				),
		]


@pytest.mark.parametrize("toml_config", valid_pep621_config)
def test_pep621_class_valid_config(
		toml_config: str,
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		):

	(tmp_pathplus / "pyproject.toml").write_clean(toml_config)

	with in_directory(tmp_pathplus):
		config = PEP621Parser().parse(dom_toml.load(tmp_pathplus / "pyproject.toml")["project"])

	advanced_data_regression.check(config)


@pytest.mark.parametrize("filename", ["README.rst", "README.md", "INTRODUCTION.md", "readme.txt"])
def test_pep621_class_valid_config_readme(
		filename: str,
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		):

	(tmp_pathplus / "pyproject.toml").write_lines([
			"[project]",
			'name = "spam"',
			'version = "2020.0.0"',
			f'readme = {filename!r}',
			])
	(tmp_pathplus / filename).write_text("This is the readme.")

	with in_directory(tmp_pathplus):
		config = PEP621Parser().parse(dom_toml.load(tmp_pathplus / "pyproject.toml")["project"])

	advanced_data_regression.check(config)


@pytest.mark.parametrize(
		"readme",
		[
				pytest.param('readme = {file = "README.rst"}', id="rst_file"),
				pytest.param('readme = {file = "README.md"}', id="md_file"),
				pytest.param('readme = {file = "README.txt"}', id="txt_file"),
				pytest.param(
						'readme = {text = "This is the inline README README.", content-type = "text/x-rst"}',
						id="text_content_type_rst"
						),
				pytest.param(
						'readme = {text = "This is the inline markdown README.", content-type = "text/markdown"}',
						id="text_content_type_md"
						),
				pytest.param(
						'readme = {text = "This is the inline README.", content-type = "text/plain"}',
						id="text_content_type_plain"
						),
				]
		)
def test_pep621_class_valid_config_readme_dict(
		readme,
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		):

	(tmp_pathplus / "pyproject.toml").write_lines([
			"[project]",
			'name = "spam"',
			'version = "2020.0.0"',
			readme,
			])
	(tmp_pathplus / "README.rst").write_text("This is the reStructuredText README.")
	(tmp_pathplus / "README.md").write_text("This is the markdown README.")
	(tmp_pathplus / "README.txt").write_text("This is the plaintext README.")
	(tmp_pathplus / "README").write_text("This is the README.")

	with in_directory(tmp_pathplus):
		config = PEP621Parser().parse(dom_toml.load(tmp_pathplus / "pyproject.toml")["project"])

	advanced_data_regression.check(config)


@pytest.mark.parametrize(
		"readme, expected",
		[
				pytest.param("readme = {}", "The 'project.readme' table cannot be empty.", id="empty"),
				pytest.param(
						"readme = {fil = 'README.md'}",
						"Unknown format for 'project.readme': {'fil': 'README.md'}",
						id="unknown_key",
						),
				pytest.param(
						'readme = {text = "This is the inline README."}',
						"The 'project.readme.content-type' key must be provided when 'project.readme.text' is given.",
						id="text_only"
						),
				pytest.param(
						'readme = {content-type = "text/x-rst"}',
						"The 'project.readme.content-type' key cannot be provided on its own; "
						"Please provide the 'project.readme.text' key too.",
						id="content_type_only"
						),
				pytest.param(
						'readme = {charset = "cp1252"}',
						"The 'project.readme.charset' key cannot be provided on its own; "
						"Please provide the 'project.readme.text' key too.",
						id="charset_only"
						),
				pytest.param(
						'readme = {charset = "cp1252", content-type = "text/x-rst"}',
						"The 'project.readme.content-type' key cannot be provided on its own; "
						"Please provide the 'project.readme.text' key too.",
						id="content_type_charset"
						),
				pytest.param(
						'readme = {text = "This is the inline README", content-type = "application/x-abiword"}',
						"Unrecognised value for 'project.readme.content-type': 'application/x-abiword'",
						id="bad_content_type"
						),
				pytest.param(
						'readme = {file = "README"}', "Unrecognised filetype for 'README'", id="no_extension"
						),
				pytest.param(
						'readme = {file = "README.doc"}',
						"Unrecognised filetype for 'README.doc'",
						id="bad_extension"
						),
				pytest.param(
						'readme = {file = "README.doc", text = "This is the README"}',
						"The 'project.readme.file' and 'project.readme.text' keys are mutually exclusive.",
						id="file_and_readme"
						),
				]
		)
def test_pep621_class_bad_config_readme(
		readme: str,
		expected: str,
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		):

	(tmp_pathplus / "pyproject.toml").write_lines([
			"[project]",
			'name = "spam"',
			'version = "2020.0.0"',
			readme,
			])

	with in_directory(tmp_pathplus), pytest.raises(BadConfigError, match=expected):
		PEP621Parser().parse(dom_toml.load(tmp_pathplus / "pyproject.toml")["project"])


@pytest.mark.parametrize("filename", ["LICENSE.rst", "LICENSE.md", "LICENSE.txt", "LICENSE"])
def test_pep621_class_valid_config_license(
		filename: str,
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		):

	(tmp_pathplus / "pyproject.toml").write_lines([
			f'[project]',
			f'name = "spam"',
			f'version = "2020.0.0"',
			f'license = {{file = "{filename}"}}',
			])
	(tmp_pathplus / filename).write_text("This is the license.")

	with in_directory(tmp_pathplus):
		config = PEP621Parser().parse(dom_toml.load(tmp_pathplus / "pyproject.toml")["project"])

	advanced_data_regression.check(config)


def test_pep621_class_valid_config_license_dict(
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		):

	(tmp_pathplus / "pyproject.toml").write_lines([
			f'[project]',
			f'name = "spam"',
			f'version = "2020.0.0"',
			f'license = {{text = "This is the MIT License"}}',
			])

	with in_directory(tmp_pathplus):
		config = PEP621Parser().parse(dom_toml.load(tmp_pathplus / "pyproject.toml")["project"])

	advanced_data_regression.check(config)


@pytest.mark.parametrize(
		"license_key, expected",
		[
				pytest.param(
						"license = {}",
						"The 'project.license' table should contain one of 'text' or 'file'.",
						id="empty"
						),
				pytest.param(
						'license = {text = "MIT", file = "LICENSE.txt"}',
						"The 'project.license.file' and 'project.license.text' keys are mutually exclusive.",
						id="double_license"
						),
				]
		)
def test_pep621_class_bad_config_license(
		license_key: str,
		expected: str,
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		):

	(tmp_pathplus / "pyproject.toml").write_lines([
			f'[project]',
			f'name = "spam"',
			f'version = "2020.0.0"',
			license_key,
			])

	with in_directory(tmp_pathplus), pytest.raises(BadConfigError, match=expected):
		config = PEP621Parser().parse(dom_toml.load(tmp_pathplus / "pyproject.toml")["project"])

		advanced_data_regression.check(config)


@pytest.mark.parametrize("config, expects, match", bad_pep621_config)
def test_pep621_class_bad_config(
		config: str,
		expects: Type[Exception],
		match: str,
		tmp_pathplus: PathPlus,
		):
	(tmp_pathplus / "pyproject.toml").write_clean(config)

	with in_directory(tmp_pathplus), pytest.raises(expects, match=match):
		PEP621Parser().parse(dom_toml.load(tmp_pathplus / "pyproject.toml")["project"])


@pytest.mark.parametrize("filename", ["README", "README.rtf"])
def test_parse_config_readme_errors(filename: str, tmp_pathplus: PathPlus):
	config = dedent(f"""
[project]
name = "spam"
version = "2020.0.0"
readme = "{filename}"
""")
	(tmp_pathplus / "pyproject.toml").write_clean(config)
	(tmp_pathplus / filename).write_text("This is the readme.")

	with in_directory(tmp_pathplus), pytest.raises(ValueError, match=f"Unrecognised filetype for '{filename}'"):
		PEP621Parser().parse(dom_toml.load(tmp_pathplus / "pyproject.toml")["project"])


@pytest.mark.parametrize("toml_config", valid_buildsystem_config)
def test_buildsystem_parser_valid_config(
		toml_config: str,
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		):
	(tmp_pathplus / "pyproject.toml").write_clean(toml_config)
	config = BuildSystemParser().parse(dom_toml.load(tmp_pathplus / "pyproject.toml")["build-system"])

	config["requires"] = list(map(str, config["requires"]))  # type: ignore

	advanced_data_regression.check(config)


@pytest.mark.parametrize("config, expects, match", bad_buildsystem_config)
def test_buildsystem_parser_errors(config: str, expects: Type[Exception], match: str, tmp_pathplus: PathPlus):
	(tmp_pathplus / "pyproject.toml").write_clean(config)

	with in_directory(tmp_pathplus), pytest.raises(expects, match=match):
		BuildSystemParser().parse(dom_toml.load(tmp_pathplus / "pyproject.toml")["build-system"])


@pytest.mark.parametrize("toml_config", [*valid_pep621_config, *valid_buildsystem_config])
def test_pyproject_class_valid_config(
		toml_config: str,
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		):

	(tmp_pathplus / "pyproject.toml").write_clean(toml_config)

	with in_directory(tmp_pathplus):
		config = PyProject.load(tmp_pathplus / "pyproject.toml")

	advanced_data_regression.check(config.to_dict())


@pytest.mark.parametrize(
		"config, expects, match",
		[
				*bad_pep621_config,
				*bad_buildsystem_config,
				pytest.param(
						'banana = "fruit"\n[project]\nname = "food"',
						BadConfigError,
						"Unexpected top level keys: 'banana'",
						id="unexpected_top_level"
						),
				]
		)
def test_pyproject_class_bad_config(
		config: str,
		expects: Type[Exception],
		match: str,
		tmp_pathplus: PathPlus,
		):

	(tmp_pathplus / "pyproject.toml").write_clean(config)

	with in_directory(tmp_pathplus), pytest.raises(expects, match=match):
		PyProject.load(tmp_pathplus / "pyproject.toml")
