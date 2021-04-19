=======
CLI
=======

``pyproject-parser`` also has a command-line interface for validating and reformaing ``pyproject.toml`` files.

Commands
---------

validate
*********

.. click:: pyproject_parser.__main__:validate
	:prog: pyproject-parser validate
	:nested: none

reformat
*********

.. click:: pyproject_parser.__main__:reformat
	:prog: pyproject-parser reformat
	:nested: none



As a ``pre-commit`` hook
----------------------------

``pyproject-parser`` can also be used as a `pre-commit <https://pre-commit.com/>`_ hook.
To do so, add the following to your
`.pre-commit-config.yaml <https://pre-commit.com/#2-add-a-pre-commit-configuration>`_ file:

.. pre-commit::
	:rev: 0.2.0
	:hooks: validate-pyproject
