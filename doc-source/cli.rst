=======
CLI
=======

In addition to the parsing library, ``pyproject-parser`` has a command-line interface for validating
and reformatting ``pyproject.toml`` files.

.. versionadded:: 0.2.0

.. extras-require:: cli
	:pyproject:
	:scope: CLI


.. latex:vspace:: -9px

Commands
---------

.. latex:vspace:: -10px

check
*********

.. latex:vspace:: -5px

.. latex:samepage::

	.. click:: pyproject_parser.__main__:check
		:prog: pyproject-parser check
		:nested: none


.. latex:vspace:: 15px

The :option:`-P / --parser-class <-P>` and :option:`-E / --encoder-class <-E>` options
must be in the form ``<module_name>:<object_name>``.
or example, ``pyproject_parser:PyProject``, which corresponds to :class:`pyproject_parser.PyProject`.
The ``module_name`` may be any valid Python module, including those containing ``.`` .

.. latex:clearpage::

reformat
*********

.. click:: pyproject_parser.__main__:reformat
	:prog: pyproject-parser reformat
	:nested: none


info
*********

.. versionadded:: 0.5.0

.. click:: pyproject_parser.__main__:info
	:prog: pyproject-parser info
	:nested: none

.. latex:vspace:: 20px

:bold-title:`Example Usage:`

.. code-block:: bash

	# Print the readme text
	echo -e $(python3 -m pyproject_parser info project.readme.text -r | tr -d '"')

	# Print the license filename
	python3 -m pyproject_parser info project.license.file

	# Get one of the project's URLs
	python3 -m pyproject_parser info project.urls."Source Code"

	# Install the build-system requirements with pip
	pip install $(python3 -m pyproject_parser info build-system.requires | jq -r 'join(" ")')

	# Dump one of the tool sub-tables
	python3 -m pyproject_parser info tool.dependency-dash


As a ``pre-commit`` hook
----------------------------

``pyproject-parser`` can also be used as a `pre-commit <https://pre-commit.com/>`_ hook.
To do so, add the following to your
`.pre-commit-config.yaml <https://pre-commit.com/#2-add-a-pre-commit-configuration>`_ file:

.. pre-commit::
	:rev: 0.14.0b1
	:hooks: check-pyproject,reformat-pyproject
