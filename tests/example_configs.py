# stdlib
import re

# 3rd party
import pytest
from coincidence.selectors import not_windows, only_windows
from dom_toml.parser import BadConfigError

MINIMAL_CONFIG = '[project]\nname = "spam"\nversion = "2020.0.0"'

KEYWORDS = f"""\
{MINIMAL_CONFIG}
keywords = ["egg", "bacon", "sausage", "tomatoes", "Lobster Thermidor"]
"""

AUTHORS = f"""\
{MINIMAL_CONFIG}
authors = [
  {{email = "hi@pradyunsg.me"}},
  {{name = "Tzu-Ping Chung"}}
]
"""

UNICODE = f"""\
{MINIMAL_CONFIG}
description = "Factory ⸻ A code generator 🏭"
authors = [{{name = "Łukasz Langa"}}]
"""

MAINTAINERS = f"""\
{MINIMAL_CONFIG}
maintainers = [
  {{name = "Brett Cannon", email = "brett@python.org"}}
]
"""

CLASSIFIERS = f"""\
{MINIMAL_CONFIG}
classifiers = [
  "Development Status :: 4 - Beta",
  "Programming Language :: Python"
]
"""

DEPENDENCIES = f"""\
{MINIMAL_CONFIG}
dependencies = [
  "httpx",
  "gidgethub[httpx]>4.0.0",
  "django>2.1; os_name != 'nt'",
  "django>2.0; os_name == 'nt'"
]
"""

OPTIONAL_DEPENDENCIES = f"""\
{MINIMAL_CONFIG}

[project.optional-dependencies]
test = [
  "pytest < 5.0.0",
  "pytest-cov[all]",
  'matplotlib>=3.0.0; platform_machine != "aarch64" or python_version > "3.6"',
]
"""

URLS = f"""\
{MINIMAL_CONFIG}

[project.urls]
homepage = "example.com"
documentation = "readthedocs.org"
repository = "github.com"
changelog = "github.com/me/spam/blob/master/CHANGELOG.md"
"""

ENTRY_POINTS = f"""\
{MINIMAL_CONFIG}

[project.scripts]
spam-cli = "spam:main_cli"

[project.gui-scripts]
spam-gui = "spam:main_gui"

[project.entry-points."spam.magical"]
tomatoes = "spam:main_tomatoes"

[project.entry-points."flake8.extension"]
SXL = "flake8_sphinx_links:Plugin"
"""

COMPLETE_PROJECT_A = """\
[project]
name = "spam"
version = "2020.0.0"
description = "Lovely Spam! Wonderful Spam!"
requires-python = ">=3.8"
keywords = ["egg", "bacon", "sausage", "tomatoes", "Lobster Thermidor"]
authors = [
  {email = "hi@pradyunsg.me"},
  {name = "Tzu-Ping Chung"}
]
maintainers = [
  {name = "Brett Cannon", email = "brett@python.org"}
]
classifiers = [
  "Development Status :: 4 - Beta",
  "Programming Language :: Python"
]

dependencies = [
  "httpx",
  "gidgethub[httpx]>4.0.0",
  "django>2.1; os_name != 'nt'",
  "django>2.0; os_name == 'nt'"
]

[project.optional-dependencies]
test = [
  "pytest < 5.0.0",
  "pytest-cov[all]"
]

[project.urls]
homepage = "example.com"
documentation = "readthedocs.org"
repository = "github.com"
changelog = "github.com/me/spam/blob/master/CHANGELOG.md"

[project.scripts]
spam-cli = "spam:main_cli"

[project.gui-scripts]
spam-gui = "spam:main_gui"

[project.entry-points."spam.magical"]
tomatoes = "spam:main_tomatoes"
"""

COMPLETE_A = """\
[build-system]
requires = [ "whey",]
build-backend = "whey"

[project]
name = "whey"
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
"""

COMPLETE_B = """\
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
additional-files = [
  "include whey/style.css",
]
"""

DYNAMIC_REQUIREMENTS = """\
[build-system]
requires = [ "whey",]
build-backend = "whey"

[project]
name = "Whey"
version = "2021.0.0"
description = "A simple Python wheel builder for simple projects."
readme = "README.rst"
keywords = [ "pep517", "pep621", "build", "sdist", "wheel", "packaging", "distribution",]
dynamic = [ "classifiers", "dependencies", "requires-python",]

[project.license]
file = "LICENSE"

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

LONG_REQUIREMENTS = """\
[build-system]
requires = [ "whey",]
build-backend = "whey"

[project]
name = "Whey"
version = "2021.0.0"
description = "A simple Python wheel builder for simple projects."
readme = "README.rst"
dynamic = [ "classifiers", "requires-python",]
dependencies = [
  "httpx",
  "gidgethub[httpx]>4.0.0",
  "django>2.1; os_name != 'nt'",
  "django>2.0; os_name == 'nt'",
  "typed-ast>=1.4.2; python_version < '3.8' and platform_python_implementation == 'CPython'"
]

[project.license]
file = "LICENSE"

[[project.authors]]
email = "dominic@davis-foster.co.uk"
name = "Dominic Davis-Foster"

[tool.whey]
base-classifiers = [ "Development Status :: 4 - Beta",]
license-key = "MIT"
package = "whey"
"""

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
				r"No such file or directory: ((Windows|Posix)Path(Plus)?\('README.rst'\)|'README.rst')",
				id="missing_readme_file",
				marks=not_windows("Message differs on Windows.")
				),
		pytest.param(
				f'{MINIMAL_CONFIG}\nlicense = {{file = "LICENSE.txt"}}',
				FileNotFoundError,
				r"No such file or directory: ((Windows|Posix)Path(Plus)?\('LICENSE.txt'\)|'LICENSE.txt')",
				id="missing_license_file",
				marks=not_windows("Message differs on Windows.")
				),
		pytest.param(
				f'{MINIMAL_CONFIG}\nreadme = "README.rst"',
				FileNotFoundError,
				"[WinError 2] The system cannot find the file specified: 'README.rst'",
				id="missing_readme_file_win32",
				marks=only_windows("Message differs on Windows.")
				),
		pytest.param(
				f'{MINIMAL_CONFIG}\nlicense = {{file = "LICENSE.txt"}}',
				FileNotFoundError,
				"[WinError 2] The system cannot find the file specified: 'LICENSE.txt'",
				id="missing_license_file_win32",
				marks=only_windows("Message differs on Windows.")
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

COMPLETE_A_WITH_FILES = """\
[build-system]
requires = [ "whey",]
build-backend = "whey"

[project]
name = "whey"
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
license = { file = "LICENSE" }
readme = "README.rst"

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
"""
