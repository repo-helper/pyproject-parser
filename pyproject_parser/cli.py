#!/usr/bin/env python3
#
#  cli.py
"""
Command line interface.

.. versionadded:: 0.2.0

.. extras-require:: cli
	:pyproject:
"""
#
#  Copyright © 2021 Dominic Davis-Foster <dominic@davis-foster.co.uk>
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#  DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#  OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
#  OR OTHER DEALINGS IN THE SOFTWARE.
#

# stdlib
import importlib
import re
from typing import Pattern, Type

# 3rd party
import click  # nodep
from consolekit.tracebacks import TracebackHandler  # nodep
from consolekit.utils import abort  # nodep
from dom_toml.parser import BadConfigError

__all__ = ["resolve_class", "ConfigTracebackHandler"]

class_string_re: Pattern[str] = re.compile("([A-Za-z_][A-Za-z_0-9.]+):([A-Za-z_][A-Za-z_0-9]+)")


def resolve_class(raw_class_string: str, name: str) -> Type:
	"""
	Resolve the class name for the :option:`-P / --parser-class <pyproject-parser check -P>`
	and :option:`-E / --encoder-class <pyproject-parser reformat -E>` options.

	:param raw_class_string:
	:param name: The name of the option, e.g. ``encoder-class``. Used for error messages.
	"""  # noqa: D400

	class_string_m = class_string_re.match(raw_class_string)

	if class_string_m:
		module_name, class_name = class_string_m.groups()
	else:
		raise click.BadOptionUsage(f"{name}", f"Invalid syntax for '--{name}'")

	module = importlib.import_module(module_name)
	resolved_class: Type = getattr(module, class_name)

	return resolved_class


class ConfigTracebackHandler(TracebackHandler):
	"""
	:class:`consolekit.tracebacks.TracebackHandler` which handles :exc:`dom_toml.parser.BadConfigError`.
	"""

	def handle_BadConfigError(self, e: "BadConfigError") -> bool:  # noqa: D102
		raise abort(f"{e.__class__.__name__}: {e}", colour=False)

	def handle_KeyError(self, e: KeyError) -> bool:  # noqa: D102
		raise abort(f"{e.__class__.__name__}: {e}", colour=False)

	def handle_TypeError(self, e: TypeError) -> bool:  # noqa: D102
		raise abort(f"{e.__class__.__name__}: {e}", colour=False)
