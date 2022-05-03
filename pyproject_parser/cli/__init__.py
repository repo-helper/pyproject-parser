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
import functools
import importlib
import re
import sys
import warnings
from typing import Pattern, Type

# 3rd party
import click  # nodep
from consolekit.tracebacks import TracebackHandler  # nodep
from consolekit.utils import abort  # nodep
from dom_toml.parser import BadConfigError

# this package
from pyproject_parser.utils import PyProjectDeprecationWarning

__all__ = ["resolve_class", "ConfigTracebackHandler", "prettify_deprecation_warning"]

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

	has_traceback_option: bool = True
	"""
	Whether to show the message ``Use '--traceback' to view the full traceback.`` on error.
	Enabled by default.

	.. versionadded:: 0.5.0  In previous versions this was effectively :py:obj:`False`.
	"""

	@property
	def _tb_option_msg(self) -> str:
		if self.has_traceback_option:
			return "\nUse '--traceback' to view the full traceback."
		else:
			return ''

	def handle_BadConfigError(self, e: "BadConfigError") -> bool:  # noqa: D102
		raise abort(f"{e.__class__.__name__}: {e}{self._tb_option_msg}", colour=False)

	def handle_KeyError(self, e: KeyError) -> bool:  # noqa: D102
		raise abort(f"{e.__class__.__name__}: {e}{self._tb_option_msg}", colour=False)

	def handle_TypeError(self, e: TypeError) -> bool:  # noqa: D102
		raise abort(f"{e.__class__.__name__}: {e}{self._tb_option_msg}", colour=False)

	def handle_AttributeError(self, e: AttributeError) -> bool:  # noqa: D102
		raise abort(f"{e.__class__.__name__}: {e}{self._tb_option_msg}", colour=False)

	def handle_ImportError(self, e: ImportError) -> bool:  # noqa: D102
		raise abort(f"{e.__class__.__name__}: {e}{self._tb_option_msg}", colour=False)


def prettify_deprecation_warning() -> None:
	"""
	Catch :class:`PyProjectDeprecationWarnings <~.PyProjectDeprecationWarning>`
	and format them prettily for the command line.

	.. versionadded:: 0.5.0
	"""  # noqa: D400

	orig_showwarning = warnings.showwarning

	if orig_showwarning is prettify_deprecation_warning:
		return

	@functools.wraps(warnings.showwarning)
	def showwarning(message, category, filename, lineno, file=None, line=None):
		if isinstance(message, PyProjectDeprecationWarning):
			if file is None:
				file = sys.stderr

			s = f"WARNING: {message.args[0]}\n"
			file.write(s)

		else:
			orig_showwarning(message, category, filename, lineno, file, line)

	warnings.showwarning = showwarning
