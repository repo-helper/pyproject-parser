# stdlib
from typing import Type

# 3rd party
import pytest
from coincidence.regressions import AdvancedDataRegressionFixture
from dom_toml.parser import AbstractConfigParser, BadConfigError
from domdf_python_tools.paths import PathPlus, in_directory
from pyproject_examples import (
		bad_buildsystem_config,
		bad_pep621_config,
		valid_buildsystem_config,
		valid_pep621_config
		)
from pyproject_examples.example_configs import COMPLETE_A, COMPLETE_A_WITH_FILES, COMPLETE_B, COMPLETE_PROJECT_A

# this package
from pyproject_parser import PyProject


@pytest.mark.parametrize("toml_config", [*valid_pep621_config, *valid_buildsystem_config])
def test_valid_config(
		toml_config: str,
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		):

	(tmp_pathplus / "pyproject.toml").write_clean(toml_config)

	with in_directory(tmp_pathplus):
		config = PyProject.load(tmp_pathplus / "pyproject.toml")

	advanced_data_regression.check(config.to_dict())


@pytest.mark.parametrize(
		"toml_config",
		[
				*valid_pep621_config,
				*valid_buildsystem_config,
				pytest.param(COMPLETE_A_WITH_FILES, id="COMPLETE_A_WITH_FILES")
				]
		)
def test_valid_config_resolve_files(
		toml_config: str,
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		):

	(tmp_pathplus / "pyproject.toml").write_clean(toml_config)
	(tmp_pathplus / "README.rst").write_clean("This is the README")
	(tmp_pathplus / "LICENSE").write_clean("This is the LICENSE")

	with in_directory(tmp_pathplus):
		config = PyProject.load(tmp_pathplus / "pyproject.toml")
		config.resolve_files()

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
				pytest.param(
						'[project]\nname = "foo"\nversion = "1.2.3"\n[[project.authors]]\nemail = "foo.bar"',
						BadConfigError,
						"Invalid email 'foo.bar': The email address is not valid. It must have exactly one @-sign.",
						id="bad_email",
						),
				pytest.param(
						'[project]\nname = "foo"\nversion = "1.2.3"\noptional-dependencies = 123',
						TypeError,
						"Invalid type for 'project.optional-dependencies': expected <class 'dict'>, got <class 'int'>",
						id="invalid_optional_dependencies_type_int",
						),
				pytest.param(
						'[project]\nname = "foo"\nversion = "1.2.3"\noptional-dependencies = "123"',
						TypeError,
						"Invalid type for 'project.optional-dependencies': expected <class 'dict'>, got <class 'str'>",
						id="invalid_optional_dependencies_type_str",
						),
				pytest.param(
						'[project]\nname = "foo"\nversion = "1.2.3"\noptional-dependencies = ["123"]',
						TypeError,
						"Invalid type for 'project.optional-dependencies': expected <class 'dict'>, got <class 'list'>",
						id="invalid_optional_dependencies_type_list",
						),
				pytest.param(
						'[project]\nname = "foo"\nversion = "1.2.3"\n[project.optional-dependencies]\nfoo = 123',
						TypeError,
						"Invalid type for 'project.optional-dependencies.foo': expected <class 'collections.abc.Sequence'>, got <class 'int'>",
						id="invalid_optional_dependencies_type_dict_int",
						),
				pytest.param(
						'[project]\nname = "foo"\nversion = "1.2.3"\n[project.optional-dependencies]\nfoo = "123"',
						TypeError,
						"Invalid type for 'project.optional-dependencies.foo': expected <class 'collections.abc.Sequence'>, got <class 'str'>",
						id="invalid_optional_dependencies_type_dict_str",
						),
				]
		)
def test_bad_config(
		config: str,
		expects: Type[Exception],
		match: str,
		tmp_pathplus: PathPlus,
		):

	(tmp_pathplus / "pyproject.toml").write_clean(config)

	with in_directory(tmp_pathplus), pytest.raises(expects, match=match):
		PyProject.load(tmp_pathplus / "pyproject.toml").resolve_files()


class WheyParser(AbstractConfigParser):
	keys = ["platforms", "package"]


class WheyPyProject(PyProject):
	tool_parsers = {"whey": WheyParser()}


@pytest.mark.parametrize(
		"toml_config",
		[
				pytest.param(COMPLETE_PROJECT_A, id="COMPLETE_PROJECT_A"),
				pytest.param(COMPLETE_A, id="COMPLETE_A"),
				pytest.param(COMPLETE_B, id="COMPLETE_B"),
				]
		)
def test_custom_pyproject_class(
		toml_config: str,
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		):

	(tmp_pathplus / "pyproject.toml").write_clean(toml_config)

	with in_directory(tmp_pathplus):
		config = WheyPyProject.load(tmp_pathplus / "pyproject.toml")

	advanced_data_regression.check(config.to_dict())
