# 3rd party
import pytest
from coincidence.regressions import AdvancedFileRegressionFixture
from domdf_python_tools.paths import PathPlus
from pyproject_examples.example_configs import COMPLETE_A, COMPLETE_A_WITH_FILES, COMPLETE_B, COMPLETE_PROJECT_A

# this package
from pyproject_parser import PyProject

UNORDERED = """\
[project]
keywords = [ "pep517", "pep621", "build", "sdist", "wheel", "packaging", "distribution",]
version = "2021.0.0"
description = "A simple Python wheel builder for simple projects."
dynamic = [ "classifiers", "requires-python",]
dependencies = [
  "httpx",
  "gidgethub[httpx]>4.0.0",
  "django>2.1; os_name != 'nt'",
  "django>2.0; os_name == 'nt'"
]
name = "whey"

[build-system]
requires = [ "whey",]
build-backend = "whey"





[project.urls]
Homepage = "https://whey.readthedocs.io/en/latest"
Documentation = "https://whey.readthedocs.io/en/latest"
"Issue Tracker" = "https://github.com/repo-helper/whey/issues"
"Source Code" = "https://github.com/repo-helper/whey"
[tool.whey]
base-classifiers = [ "Development Status :: 4 - Beta",]
python-versions = [ "3.6", "3.7", "3.8", "3.9", "3.10",]
python-implementations = [ "CPython", "PyPy",]
platforms = [ "Windows", "macOS", "Linux",]
license-key = "MIT"

[[project.authors]]
email = "dominic@davis-foster.co.uk"
name = "Dominic Davis-Foster"


"""


@pytest.mark.parametrize(
		"toml_string",
		[
				pytest.param(COMPLETE_A, id="COMPLETE_A"),
				pytest.param(COMPLETE_B, id="COMPLETE_B"),
				pytest.param(COMPLETE_PROJECT_A, id="COMPLETE_PROJECT_A"),
				]
		)
def test_dumps(tmp_pathplus: PathPlus, toml_string: str, advanced_file_regression: AdvancedFileRegressionFixture):
	(tmp_pathplus / "pyproject.toml").write_clean(toml_string)

	config = PyProject.load(filename=tmp_pathplus / "pyproject.toml")

	config.dump(tmp_pathplus / "pyproject.toml")

	advanced_file_regression.check_file(tmp_pathplus / "pyproject.toml")
	advanced_file_regression.check(config.dumps(), extension=".toml")


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
def test_reformat(
		tmp_pathplus: PathPlus, toml_string: str, advanced_file_regression: AdvancedFileRegressionFixture
		):
	(tmp_pathplus / "pyproject.toml").write_clean(toml_string)
	(tmp_pathplus / "README.rst").write_clean("This is the README")
	(tmp_pathplus / "LICENSE").write_clean("This is the LICENSE")

	PyProject.reformat(tmp_pathplus / "pyproject.toml")
	advanced_file_regression.check_file(tmp_pathplus / "pyproject.toml")
