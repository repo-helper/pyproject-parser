# stdlib
import re
from textwrap import dedent
from typing import Type

# 3rd party
import dom_toml
import pytest
from coincidence.regressions import AdvancedDataRegressionFixture
from dom_toml.parser import BadConfigError
from domdf_python_tools.paths import PathPlus, in_directory

# this package
from pyproject_parser import BuildSystemParser, PEP621Parser
from tests.example_configs import (
		bad_buildsystem_config,
		bad_pep621_config,
		valid_buildsystem_config,
		valid_pep621_config
		)


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


class ReducedPEP621Parser(PEP621Parser, inherit_defaults=True):
	keys = ["name", "version", "dependencies"]


@pytest.mark.parametrize("toml_config", valid_pep621_config)
def test_pep621_subclass(
		toml_config: str,
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		):

	(tmp_pathplus / "pyproject.toml").write_clean(toml_config)

	with in_directory(tmp_pathplus):
		config = ReducedPEP621Parser().parse(dom_toml.load(tmp_pathplus / "pyproject.toml")["project"])

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
		"readme, expected, exception",
		[
				pytest.param(
						"readme = {}",
						"The 'project.readme' table cannot be empty.",
						BadConfigError,
						id="empty",
						),
				pytest.param(
						"readme = {fil = 'README.md'}",
						"Unknown format for 'project.readme': {'fil': 'README.md'}",
						BadConfigError,
						id="unknown_key",
						),
				pytest.param(
						'readme = {text = "This is the inline README."}',
						"The 'project.readme.content-type' key must be provided when 'project.readme.text' is given.",
						BadConfigError,
						id="text_only"
						),
				pytest.param(
						'readme = {content-type = "text/x-rst"}',
						"The 'project.readme.content-type' key cannot be provided on its own; "
						"Please provide the 'project.readme.text' key too.",
						BadConfigError,
						id="content_type_only"
						),
				pytest.param(
						'readme = {charset = "cp1252"}',
						"The 'project.readme.charset' key cannot be provided on its own; "
						"Please provide the 'project.readme.text' key too.",
						BadConfigError,
						id="charset_only"
						),
				pytest.param(
						'readme = {charset = "cp1252", content-type = "text/x-rst"}',
						"The 'project.readme.content-type' key cannot be provided on its own; "
						"Please provide the 'project.readme.text' key too.",
						BadConfigError,
						id="content_type_charset"
						),
				pytest.param(
						'readme = {text = "This is the inline README", content-type = "application/x-abiword"}',
						"Unrecognised value for 'project.readme.content-type': 'application/x-abiword'",
						BadConfigError,
						id="bad_content_type"
						),
				pytest.param(
						'readme = {file = "README"}',
						"Unsupported extension for 'README'",
						ValueError,
						id="no_extension",
						),
				pytest.param(
						'readme = {file = "README.doc"}',
						"Unsupported extension for 'README.doc'",
						ValueError,
						id="bad_extension"
						),
				pytest.param(
						'readme = {file = "README.doc", text = "This is the README"}',
						"The 'project.readme.file' and 'project.readme.text' keys are mutually exclusive.",
						BadConfigError,
						id="file_and_readme"
						),
				]
		)
def test_pep621_class_bad_config_readme(
		readme: str,
		expected: str,
		exception: Type[Exception],
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		):

	(tmp_pathplus / "pyproject.toml").write_lines([
			"[project]",
			'name = "spam"',
			'version = "2020.0.0"',
			readme,
			])

	with in_directory(tmp_pathplus), pytest.raises(exception, match=expected):
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

	with in_directory(tmp_pathplus), pytest.raises(ValueError, match=f"Unsupported extension for '{filename}'"):
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