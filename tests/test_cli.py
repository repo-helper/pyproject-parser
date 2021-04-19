# 3rd party
import pytest
from coincidence.regressions import AdvancedDataRegressionFixture, AdvancedFileRegressionFixture
from consolekit.testing import CliRunner, Result
from domdf_python_tools.paths import PathPlus, in_directory
from pyproject_examples import valid_buildsystem_config, valid_pep621_config
from pyproject_examples.example_configs import COMPLETE_A, COMPLETE_A_WITH_FILES, COMPLETE_B, COMPLETE_PROJECT_A

# this package
from pyproject_parser.__main__ import reformat, validate
from tests.test_dumping import UNORDERED


@pytest.mark.parametrize(
		"toml_string",
		[
				pytest.param(COMPLETE_A, id="COMPLETE_A"),
				pytest.param(COMPLETE_A_WITH_FILES, id="COMPLETE_A_WITH_FILES"),
				pytest.param(COMPLETE_B, id="COMPLETE_B"),
				pytest.param(COMPLETE_PROJECT_A, id="COMPLETE_PROJECT_A"),
				pytest.param(UNORDERED, id="UNORDERED"),
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

	assert result.exit_code == 0

	advanced_file_regression.check_file(tmp_pathplus / "pyproject.toml")
	result.check_stdout(advanced_file_regression, extension=".diff")


@pytest.mark.parametrize("toml_string", [*valid_pep621_config, *valid_buildsystem_config])
def test_validate(
		toml_string: str,
		tmp_pathplus: PathPlus,
		cli_runner: CliRunner,
		advanced_data_regression: AdvancedDataRegressionFixture,
		):
	(tmp_pathplus / "pyproject.toml").write_clean(toml_string)

	with in_directory(tmp_pathplus):
		result: Result = cli_runner.invoke(validate, catch_exceptions=False)

	assert result.exit_code == 0
