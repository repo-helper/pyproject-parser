=================
pyproject-parser
=================

.. start short_desc

.. documentation-summary::
	:meta:

.. end short_desc

.. start shields

.. only:: html

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

	.. |docs| rtfd-shield::
		:project: pyproject-parser
		:alt: Documentation Build Status

	.. |docs_check| actions-shield::
		:workflow: Docs Check
		:alt: Docs Check Status

	.. |actions_linux| actions-shield::
		:workflow: Linux
		:alt: Linux Test Status

	.. |actions_windows| actions-shield::
		:workflow: Windows
		:alt: Windows Test Status

	.. |actions_macos| actions-shield::
		:workflow: macOS
		:alt: macOS Test Status

	.. |actions_flake8| actions-shield::
		:workflow: Flake8
		:alt: Flake8 Status

	.. |actions_mypy| actions-shield::
		:workflow: mypy
		:alt: mypy status

	.. |requires| image:: https://dependency-dash.herokuapp.com/github/repo-helper/pyproject-parser/badge.svg
		:target: https://dependency-dash.herokuapp.com/github/repo-helper/pyproject-parser/
		:alt: Requirements Status

	.. |coveralls| coveralls-shield::
		:alt: Coverage

	.. |codefactor| codefactor-shield::
		:alt: CodeFactor Grade

	.. |pypi-version| pypi-shield::
		:project: pyproject-parser
		:version:
		:alt: PyPI - Package Version

	.. |supported-versions| pypi-shield::
		:project: pyproject-parser
		:py-versions:
		:alt: PyPI - Supported Python Versions

	.. |supported-implementations| pypi-shield::
		:project: pyproject-parser
		:implementations:
		:alt: PyPI - Supported Implementations

	.. |wheel| pypi-shield::
		:project: pyproject-parser
		:wheel:
		:alt: PyPI - Wheel

	.. |conda-version| image:: https://img.shields.io/conda/v/conda-forge/pyproject-parser?logo=anaconda
		:target: https://anaconda.org/conda-forge/pyproject-parser
		:alt: Conda - Package Version

	.. |conda-platform| image:: https://img.shields.io/conda/pn/conda-forge/pyproject-parser?label=conda%7Cplatform
		:target: https://anaconda.org/conda-forge/pyproject-parser
		:alt: Conda - Platform

	.. |license| github-shield::
		:license:
		:alt: License

	.. |language| github-shield::
		:top-language:
		:alt: GitHub top language

	.. |commits-since| github-shield::
		:commits-since: v0.7.0
		:alt: GitHub commits since tagged version

	.. |commits-latest| github-shield::
		:last-commit:
		:alt: GitHub last commit

	.. |maintained| maintained-shield:: 2022
		:alt: Maintenance

	.. |pypi-downloads| pypi-shield::
		:project: pyproject-parser
		:downloads: month
		:alt: PyPI - Downloads

.. end shields

Installation
---------------

.. start installation

.. installation:: pyproject-parser
	:pypi:
	:github:
	:anaconda:
	:conda-channels: conda-forge

.. end installation

.. latex:vspace:: 20px

``pyproject-parser`` also has an optional README validation feature, which checks the README will render correctly on PyPI.
This requires that the ``readme`` extra is installed:

.. prompt:: bash

	python -m pip install pyproject-parser[readme]


Once the dependencies are installed the validation can be disabled by setting the
``CHECK_README`` environment variable to ``0``.


Contents
-----------

.. html-section::

.. toctree::
	:hidden:

	Home<self>

.. toctree::
	:maxdepth: 3
	:glob:

	cli
	api/pyproject-parser
	api/*

.. sidebar-links::
	:caption: Links
	:github:
	:pypi: pyproject-parser

	Contributing Guide<https://contributing.repo-helper.uk>
	Source
	license

.. start links

.. only:: html

	View the :ref:`Function Index <genindex>` or browse the `Source Code <_modules/index.html>`__.

	:github:repo:`Browse the GitHub Repository <repo-helper/pyproject-parser>`

.. end links
