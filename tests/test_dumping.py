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

DUMPS_README_TEMPLATE = """\
[build-system]
requires = [ "whey",]
build-backend = "whey"

[project]
name = "Whey"
version = "2021.0.0"
description = "A simple Python wheel builder for simple projects."
keywords = [ "pep517", "pep621", "build", "sdist", "wheel", "packaging", "distribution",]
dynamic = [ "classifiers", "requires-python",]
dependencies = [
  "httpx",
  "gidgethub[httpx]>4.0.0",
  "django>2.1; os_name != 'nt'",
  "django>2.0; os_name == 'nt'"
]
{readme_block}

[[project.authors]]
email = "dominic@davis-foster.co.uk"
name = "Dominic Davis-Foster"

[project.urls]
Homepage = "https://whey.readthedocs.io/en/latest"
Documentation = "https://whey.readthedocs.io/en/latest"
"Issue Tracker" = "https://github.com/repo-helper/whey/issues"
"Source Code" = "https://github.com/repo-helper/whey"
"""

COMPLETE_UNDERSCORE_NAME = """\
[build-system]
requires = [ "whey",]
build-backend = "whey"

[project]
name = "toctree_plus"
version = "2021.0.0"
description = "A simple Python wheel builder for simple projects."
keywords = [ "pep517", "pep621", "build", "sdist", "wheel", "packaging", "distribution",]
dynamic = [ "classifiers", "requires-python",]
dependencies = [
  "httpx",
  "gidgethub[httpx]>4.0.0",
  "django>2.1; os_name != 'nt'",
  "django>2.0; os_name == 'nt'"
]

[[project.authors]]
email = "dominic@davis-foster.co.uk"
name = "Dominic Davis-Foster"

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
package = "whey"
"""


@pytest.mark.parametrize(
		"toml_string",
		[
				pytest.param(COMPLETE_A, id="COMPLETE_A"),
				pytest.param(COMPLETE_B, id="COMPLETE_B"),
				pytest.param(COMPLETE_PROJECT_A, id="COMPLETE_PROJECT_A"),
				]
		)
def test_dumps(
		tmp_pathplus: PathPlus,
		toml_string: str,
		advanced_file_regression: AdvancedFileRegressionFixture,
		):
	(tmp_pathplus / "pyproject.toml").write_clean(toml_string)

	config = PyProject.load(filename=tmp_pathplus / "pyproject.toml")

	config.dump(tmp_pathplus / "pyproject.toml")

	advanced_file_regression.check_file(tmp_pathplus / "pyproject.toml")
	advanced_file_regression.check(config.dumps(), extension=".toml")


def _param(readme_block: str, **kwargs):  # noqa: MAN002
	return pytest.param(DUMPS_README_TEMPLATE.format(readme_block=readme_block), **kwargs)


@pytest.mark.parametrize(
		"toml_string",
		[
				_param(readme_block="readme = 'README.rst'", id="string"),
				_param(
						readme_block="[project.readme]\ntext = 'This is the README'\ncontent-type = 'text/x-rst'",
						id="dict_text"
						),
				_param(
						readme_block="[project.readme]\nfile = 'README.rst'\ncontent-type = 'text/x-rst'",
						id="dict_file"
						),
				]
		)
def test_dumps_readme(
		tmp_pathplus: PathPlus,
		toml_string: str,
		advanced_file_regression: AdvancedFileRegressionFixture,
		):
	(tmp_pathplus / "pyproject.toml").write_clean(toml_string)
	(tmp_pathplus / "README.rst").write_clean("This is the README")

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
				pytest.param(COMPLETE_UNDERSCORE_NAME, id="COMPLETE_UNDERSCORE_NAME"),
				]
		)
def test_reformat(
		tmp_pathplus: PathPlus,
		toml_string: str,
		advanced_file_regression: AdvancedFileRegressionFixture,
		):
	(tmp_pathplus / "pyproject.toml").write_clean(toml_string)
	(tmp_pathplus / "README.rst").write_clean("This is the README")
	(tmp_pathplus / "LICENSE").write_clean("This is the LICENSE")

	PyProject.reformat(tmp_pathplus / "pyproject.toml")
	advanced_file_regression.check_file(tmp_pathplus / "pyproject.toml")

	# Should be no changes
	PyProject.reformat(tmp_pathplus / "pyproject.toml")
	advanced_file_regression.check_file(tmp_pathplus / "pyproject.toml")
