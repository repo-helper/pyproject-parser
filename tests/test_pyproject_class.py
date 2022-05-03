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


@pytest.mark.parametrize("toml_config", [*valid_pep621_config, *valid_buildsystem_config])
def test_from_dict(toml_config: str, tmp_pathplus: PathPlus):

	(tmp_pathplus / "pyproject.toml").write_clean(toml_config)

	with in_directory(tmp_pathplus):
		config = PyProject.load(tmp_pathplus / "pyproject.toml")

	assert PyProject.from_dict(config.to_dict()) == config

	hyphen_map = config.to_dict()
	hyphen_map["build-system"] = hyphen_map.pop("build_system")
	assert PyProject.from_dict(hyphen_map) == config


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
						"Unexpected top-level key 'banana'. Only 'build-system', 'project' and 'tool' are allowed.",
						id="unexpected_top_level"
						),
				pytest.param(
						"[coverage]\nomit = 'demo.py'\n[flake8]\nselect = ['F401']",
						BadConfigError,
						"Unexpected top-level key 'coverage'. Only 'build-system', 'project' and 'tool' are allowed.",
						id="top-level",
						),
				pytest.param(
						"[build_system]\nbackend = 'whey'",
						BadConfigError,
						"Unexpected top-level key 'build_system'. Did you mean 'build-system'",
						id="top_level_typo_underscore",
						),
				pytest.param(
						"[Build-System]\nbackend = 'whey'",
						BadConfigError,
						"Unexpected top-level key 'Build-System'. Did you mean 'build-system'",
						id="top_level_typo_caps",
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
						'[project]\nname = "foo"\nversion = "1.2.3"\n[project.optional-dependencies]\nfoo = [123]',
						TypeError,
						r"Invalid type for 'project.optional-dependencies.foo\[0\]': expected <class 'str'>, got <class 'int'>",
						id="invalid_optional_dependencies_type_dict_list_int",
						),
				pytest.param(
						'[project]\nname = "foo"\nversion = "1.2.3"\n[project.optional-dependencies]\nfoo = "123"',
						TypeError,
						"Invalid type for 'project.optional-dependencies.foo': expected <class 'collections.abc.Sequence'>, got <class 'str'>",
						id="invalid_optional_dependencies_type_dict_str",
						),
				pytest.param(
						'[project]\nname = "foo"\nversion = "1.2.3"\n[project.entry-points.console_scripts]',
						BadConfigError,
						"'project.entry-points' may not contain a 'console_scripts' sub-table. Use 'project.scripts' instead.",
						id="console_scripts_entry_point",
						),
				pytest.param(
						'[project]\nname = "foo"\nversion = "1.2.3"\n[project.entry-points.gui_scripts]',
						BadConfigError,
						"'project.entry-points' may not contain a 'gui_scripts' sub-table. Use 'project.gui-scripts' instead.",
						id="gui_scripts_entry_point",
						),
				pytest.param(
						'[project]\nname = "foo"\nversion = "1.2.3"\n[project.entry-points.console-scripts]',
						BadConfigError,
						"'project.entry-points' may not contain a 'console-scripts' sub-table. Use 'project.scripts' instead.",
						id="console_scripts_hyphen_entry_point",
						),
				pytest.param(
						'[project]\nname = "foo"\nversion = "1.2.3"\n[project.entry-points.gui-scripts]',
						BadConfigError,
						"'project.entry-points' may not contain a 'gui-scripts' sub-table. Use 'project.gui-scripts' instead.",
						id="gui_scripts_hyphen_entry_point",
						),
				# pytest.param(
				# 		'[project]\nname = "foo"\nversion = "1.2.3"\n[project.optional-dependencies]\nwith-hyphen = []',
				# 		TypeError,
				# 		"Invalid extra name 'with-hyphen'",
				# 		id="extra_invalid_a",
				# 		),
				pytest.param(
						'[project]\nname = "foo"\nversion = "1.2.3"\n[project.optional-dependencies]\n"quoted?" = []',
						TypeError,
						r"Invalid extra name 'quoted\?'",
						id="extra_invalid_b",
						),
				pytest.param(
						'[project]\nname = "foo"\nversion = "1.2.3"\n[project.optional-dependencies]\n"number#1" = []',
						TypeError,
						"Invalid extra name 'number#1'",
						id="extra_invalid_c",
						),
				# For Part 2
				# pytest.param(
				# 		'[project]\nname = "foo"\nversion = "1.2.3"\n[project.optional-dependencies]\n"dev_test" = []\n"dev-test" = []',
				# 		BadConfigError,
				# 		"'project.optional-dependencies.dev-test': Multiple extras were defined with the same normalized name of 'dev-test'",
				# 		id="duplicate_extra_1",
				# 		),
				# pytest.param(
				# 		'[project]\nname = "foo"\nversion = "1.2.3"\n[project.optional-dependencies]\n"dev-test" = []\n"dev_test" = []',
				# 		BadConfigError,
				# 		"'project.optional-dependencies.dev_test': Multiple extras were defined with the same normalized name of 'dev-test'",
				# 		id="duplicate_extra_2",
				# 		),
				# pytest.param(
				# 		'[project]\nname = "foo"\nversion = "1.2.3"\n[project.optional-dependencies]\n"dev.test" = []\n"dev_test" = []',
				# 		BadConfigError,
				# 		"'project.optional-dependencies.dev_test': Multiple extras were defined with the same normalized name of 'dev-test'",
				# 		id="duplicate_extra_3",
				# 		),
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
