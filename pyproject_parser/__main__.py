#!/usr/bin/env python3
#
#  __main__.py
"""
CLI entry point.
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
import sys
from typing import Type, TypeVar

# 3rd party
import click  # nodep
from consolekit import click_group  # nodep
from consolekit.options import auto_default_argument, auto_default_option, colour_option, flag_option  # nodep
from consolekit.terminal_colours import ColourTrilean, resolve_color_default  # nodep
from consolekit.tracebacks import handle_tracebacks, traceback_option  # nodep
from consolekit.utils import abort, coloured_diff  # nodep
from domdf_python_tools.paths import PathPlus
from domdf_python_tools.typing import PathLike
from toml import TomlEncoder

# this package
from pyproject_parser import PyProject
from pyproject_parser.cli import ConfigTracebackHandler, resolve_class

__all__ = ["main", "reformat", "validate"]


class CustomTracebackHandler(ConfigTracebackHandler):

	def handle_AttributeError(self, e: AttributeError) -> bool:  # noqa: D102
		raise abort(f"{e.__class__.__name__}: {e}\nUse '--traceback' to view the full traceback.", colour=False)

	def handle_ImportError(self, e: ImportError) -> bool:  # noqa: D102
		raise abort(f"{e.__class__.__name__}: {e}\nUse '--traceback' to view the full traceback.", colour=False)


@click_group()
def main():  # pragma: no cover
	pass


_C = TypeVar("_C", bound=click.Command)


def options(c: _C) -> _C:
	auto_default_argument("pyproject_file", type=click.STRING)(c)
	auto_default_option("-P", "--parser-class", default=click.STRING)(c)
	traceback_option()(c)
	return c


@options
@main.command()
def validate(
		pyproject_file: PathLike = "pyproject.toml",
		parser_class: str = "pyproject_parser:PyProject",
		show_traceback: bool = False,
		):
	"""
	Validate the given ``pyproject.toml`` file
	"""

	pyproject_file = PathPlus(pyproject_file)

	click.echo(f"Validating {str(pyproject_file)!r}")

	with handle_tracebacks(show_traceback, CustomTracebackHandler):
		parser: Type[PyProject] = resolve_class(parser_class, "parser-class")
		parser.load(filename=pyproject_file)


@colour_option()
@flag_option("-D", "--show-diff", help="Show a (coloured) diff of changes.")
@options
@auto_default_option("-E", "--encoder-class", default=click.STRING)
@main.command()
def reformat(
		pyproject_file: PathLike = "pyproject.toml",
		encoder_class: str = "pyproject_parser:PyProjectTomlEncoder",
		parser_class: str = "pyproject_parser:PyProject",
		show_traceback: bool = False,
		show_diff: bool = False,
		colour: ColourTrilean = None,
		):
	"""
	Reformat the given ``pyproject.toml`` file
	"""

	pyproject_file = PathPlus(pyproject_file)

	click.echo(f"Reformatting {str(pyproject_file)!r}")

	with handle_tracebacks(show_traceback, CustomTracebackHandler):
		parser: Type[PyProject] = resolve_class(parser_class, "parser-class")
		encoder: Type[TomlEncoder] = resolve_class(encoder_class, "encoder-class")

		original_content = pyproject_file.read_lines()

		config = parser.load(filename=pyproject_file, set_defaults=False)
		reformatted_content = config.dump(filename=pyproject_file, encoder=encoder)

		if show_diff:
			diff = coloured_diff(
					original_content,
					reformatted_content.split('\n'),
					str(pyproject_file),
					str(pyproject_file),
					"(original)",
					"(reformatted)",
					lineterm='',
					)

			click.echo(diff, color=resolve_color_default(colour))


if __name__ == "__main__":
	sys.exit(main())
