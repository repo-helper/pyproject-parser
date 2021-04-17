#################
pyproject-parser
#################

.. start short_desc

**Parser for 'pyproject.toml'**

.. end short_desc


.. start shields

.. list-table::
	:stub-columns: 1
	:widths: 10 90

	* - Docs
	  - |docs| |docs_check|
	* - Tests
	  - |actions_linux| |actions_windows| |actions_macos| |coveralls|
	* - PyPI
	  - |pypi-version| |supported-versions| |supported-implementations| |wheel|
	* - Anaconda
	  - |conda-version| |conda-platform|
	* - Activity
	  - |commits-latest| |commits-since| |maintained| |pypi-downloads|
	* - QA
	  - |codefactor| |actions_flake8| |actions_mypy|
	* - Other
	  - |license| |language| |requires|

.. |docs| image:: https://img.shields.io/readthedocs/pyproject-parser/latest?logo=read-the-docs
	:target: https://pyproject-parser.readthedocs.io/en/latest
	:alt: Documentation Build Status

.. |docs_check| image:: https://github.com/repo-helper/pyproject-parser/workflows/Docs%20Check/badge.svg
	:target: https://github.com/repo-helper/pyproject-parser/actions?query=workflow%3A%22Docs+Check%22
	:alt: Docs Check Status

.. |actions_linux| image:: https://github.com/repo-helper/pyproject-parser/workflows/Linux/badge.svg
	:target: https://github.com/repo-helper/pyproject-parser/actions?query=workflow%3A%22Linux%22
	:alt: Linux Test Status

.. |actions_windows| image:: https://github.com/repo-helper/pyproject-parser/workflows/Windows/badge.svg
	:target: https://github.com/repo-helper/pyproject-parser/actions?query=workflow%3A%22Windows%22
	:alt: Windows Test Status

.. |actions_macos| image:: https://github.com/repo-helper/pyproject-parser/workflows/macOS/badge.svg
	:target: https://github.com/repo-helper/pyproject-parser/actions?query=workflow%3A%22macOS%22
	:alt: macOS Test Status

.. |actions_flake8| image:: https://github.com/repo-helper/pyproject-parser/workflows/Flake8/badge.svg
	:target: https://github.com/repo-helper/pyproject-parser/actions?query=workflow%3A%22Flake8%22
	:alt: Flake8 Status

.. |actions_mypy| image:: https://github.com/repo-helper/pyproject-parser/workflows/mypy/badge.svg
	:target: https://github.com/repo-helper/pyproject-parser/actions?query=workflow%3A%22mypy%22
	:alt: mypy status

.. |requires| image:: https://requires.io/github/repo-helper/pyproject-parser/requirements.svg?branch=master
	:target: https://requires.io/github/repo-helper/pyproject-parser/requirements/?branch=master
	:alt: Requirements Status

.. |coveralls| image:: https://img.shields.io/coveralls/github/repo-helper/pyproject-parser/master?logo=coveralls
	:target: https://coveralls.io/github/repo-helper/pyproject-parser?branch=master
	:alt: Coverage

.. |codefactor| image:: https://img.shields.io/codefactor/grade/github/repo-helper/pyproject-parser?logo=codefactor
	:target: https://www.codefactor.io/repository/github/repo-helper/pyproject-parser
	:alt: CodeFactor Grade

.. |pypi-version| image:: https://img.shields.io/pypi/v/pyproject-parser
	:target: https://pypi.org/project/pyproject-parser/
	:alt: PyPI - Package Version

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/pyproject-parser?logo=python&logoColor=white
	:target: https://pypi.org/project/pyproject-parser/
	:alt: PyPI - Supported Python Versions

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/pyproject-parser
	:target: https://pypi.org/project/pyproject-parser/
	:alt: PyPI - Supported Implementations

.. |wheel| image:: https://img.shields.io/pypi/wheel/pyproject-parser
	:target: https://pypi.org/project/pyproject-parser/
	:alt: PyPI - Wheel

.. |conda-version| image:: https://img.shields.io/conda/v/domdfcoding/pyproject-parser?logo=anaconda
	:target: https://anaconda.org/domdfcoding/pyproject-parser
	:alt: Conda - Package Version

.. |conda-platform| image:: https://img.shields.io/conda/pn/domdfcoding/pyproject-parser?label=conda%7Cplatform
	:target: https://anaconda.org/domdfcoding/pyproject-parser
	:alt: Conda - Platform

.. |license| image:: https://img.shields.io/github/license/repo-helper/pyproject-parser
	:target: https://github.com/repo-helper/pyproject-parser/blob/master/LICENSE
	:alt: License

.. |language| image:: https://img.shields.io/github/languages/top/repo-helper/pyproject-parser
	:alt: GitHub top language

.. |commits-since| image:: https://img.shields.io/github/commits-since/repo-helper/pyproject-parser/v0.1.2
	:target: https://github.com/repo-helper/pyproject-parser/pulse
	:alt: GitHub commits since tagged version

.. |commits-latest| image:: https://img.shields.io/github/last-commit/repo-helper/pyproject-parser
	:target: https://github.com/repo-helper/pyproject-parser/commit/master
	:alt: GitHub last commit

.. |maintained| image:: https://img.shields.io/maintenance/yes/2021
	:alt: Maintenance

.. |pypi-downloads| image:: https://img.shields.io/pypi/dm/pyproject-parser
	:target: https://pypi.org/project/pyproject-parser/
	:alt: PyPI - Downloads

.. end shields

Installation
--------------

.. start installation

``pyproject-parser`` can be installed from PyPI or Anaconda.

To install with ``pip``:

.. code-block:: bash

	$ python -m pip install pyproject-parser

To install with ``conda``:

	* First add the required channels

	.. code-block:: bash

		$ conda config --add channels https://conda.anaconda.org/conda-forge
		$ conda config --add channels https://conda.anaconda.org/domdfcoding

	* Then install

	.. code-block:: bash

		$ conda install pyproject-parser

.. end installation

``pyproject-parser`` also has an optional README validation feature, which checks the README will render correctly on PyPI.
This requires that the ``readme`` extra is installed:

.. code-block:: bash

	$ python -m pip install pyproject-parser[readme]
