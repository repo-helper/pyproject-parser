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

.. latex:vspace:: -4px

check
*********

.. latex:samepage::

	.. click:: pyproject_parser.__main__:check
		:prog: pyproject-parser check
		:nested: none

reformat
*********

.. click:: pyproject_parser.__main__:reformat
	:prog: pyproject-parser reformat
	:nested: none

.. latex:vspace:: 20px

The :option:`-P / --parser-class <-P>` and :option:`-E / --encoder-class <-E>` options
must be in the form ``<module_name>:<object_name>``.
or example, ``pyproject_parser:PyProject``, which corresponds to :class:`pyproject_parser.PyProject`.
The ``module_name`` may be any valid Python module, including those containing ``.`` .


As a ``pre-commit`` hook
----------------------------

``pyproject-parser`` can also be used as a `pre-commit <https://pre-commit.com/>`_ hook.
To do so, add the following to your
`.pre-commit-config.yaml <https://pre-commit.com/#2-add-a-pre-commit-configuration>`_ file:

.. pre-commit::
	:rev: 0.4.1
	:hooks: check-pyproject,reformat-pyproject
