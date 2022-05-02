#!/usr/bin/env python3
#
#  __main__.py
"""
CLI entry point.

.. versionadded:: 0.2.0
"""
#
#  Copyright © 2021-2022 Dominic Davis-Foster <dominic@davis-foster.co.uk>
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
from typing import TYPE_CHECKING, Any, Iterable, List, Optional, Type, TypeVar

# 3rd party
import click  # nodep
from consolekit import click_group  # nodep
from consolekit.commands import MarkdownHelpCommand  # nodep
from consolekit.options import (  # nodep
		DescribedArgument,
		auto_default_argument,
		auto_default_option,
		colour_option,
		flag_option
		)
from consolekit.tracebacks import handle_tracebacks, traceback_option  # nodep

# this package
from pyproject_parser import License
from pyproject_parser.cli import prettify_deprecation_warning

if TYPE_CHECKING:
	# 3rd party
	from consolekit.terminal_colours import ColourTrilean
	from domdf_python_tools.typing import PathLike

__all__ = ["main", "reformat", "check"]


@click_group()
def main():  # pragma: no cover  # noqa: D103
	pass


_C = TypeVar("_C", bound=click.Command)


def options(c: _C) -> _C:
	pyproject_file_option = auto_default_argument(
			"pyproject_file",
			type=click.STRING,
			description="The ``pyproject.toml`` file.",
			cls=DescribedArgument,
			)
	parser_class_option = auto_default_option(
			"-P",
			"--parser-class",
			type=click.STRING,
			help="The class to parse the 'pyproject.toml' file with.",
			show_default=True,
			)

	pyproject_file_option(c)
	parser_class_option(c)
	traceback_option()(c)

	return c


@options
@main.command(cls=MarkdownHelpCommand)
def check(
		pyproject_file: "PathLike" = "pyproject.toml",
		parser_class: str = "pyproject_parser:PyProject",
		show_traceback: bool = False,
		):
	"""
	Validate the given ``pyproject.toml`` file.
	"""

	# 3rd party
	import dom_toml
	from dom_toml.parser import BadConfigError
	from domdf_python_tools.paths import PathPlus
	from domdf_python_tools.words import Plural, word_join

	# this package
	from pyproject_parser import PyProject
	from pyproject_parser.cli import ConfigTracebackHandler, resolve_class
	from pyproject_parser.parsers import BuildSystemParser, PEP621Parser

	if not show_traceback:
		prettify_deprecation_warning()

	pyproject_file = PathPlus(pyproject_file)

	click.echo(f"Validating {str(pyproject_file)!r}")

	with handle_tracebacks(show_traceback, ConfigTracebackHandler):
		parser: Type[PyProject] = resolve_class(parser_class, "parser-class")
		parser.load(filename=pyproject_file)

		raw_config = dom_toml.load(pyproject_file)

		_keys = Plural("key", "keys")

		def error_on_unknown(
				keys: Iterable[str],
				expected_keys: Iterable[str],
				table_name: str,
				) -> None:
			unknown_keys = set(keys) - set(expected_keys)

			if unknown_keys:
				raise BadConfigError(
						f"Unknown {_keys(len(unknown_keys))} in '[{table_name}]': "
						f"{word_join(sorted(unknown_keys), use_repr=True)}",
						)

		# Implements PEPs 517 and 518
		error_on_unknown(raw_config.get("build-system", {}).keys(), BuildSystemParser.keys, "build-system")

		# Implements PEP 621
		error_on_unknown(raw_config.get("project", {}).keys(), {*PEP621Parser.keys, "dynamic"}, "project")


_resolve_help = "Resolve file key in project.readme and project.license (if present) to retrieve the content of the file."


@traceback_option()
@auto_default_option(
		"-P",
		"--parser-class",
		type=click.STRING,
		help="The class to parse the 'pyproject.toml' file with.",
		show_default=True,
		)
@auto_default_option(
		"-f",
		"--file",
		"pyproject_file",
		type=click.STRING,
		help="The ``pyproject.toml`` file.",
		)
@auto_default_option(
		"-i",
		"--indent",
		help="Add indentation to the JSON output.",
		type=click.INT,
		)
@flag_option(
		"-r",
		"--resolve",
		help=_resolve_help,
		show_default=True,
		)
@auto_default_argument(
		"field",
		type=click.STRING,
		description="The field to retrieve from the ``pyproject.toml`` file.",
		cls=DescribedArgument,
		)
@main.command(cls=MarkdownHelpCommand)
def info(
		field: Optional[str] = None,
		pyproject_file: "PathLike" = "pyproject.toml",
		parser_class: str = "pyproject_parser:PyProject",
		resolve: bool = False,
		show_traceback: bool = False,
		indent: Optional[int] = None,
		):
	"""
	Extract information from the given ``pyproject.toml`` file and print the JSON representation.
	"""

	# stdlib
	import os
	import re

	# 3rd party
	import dom_toml
	import sdjson  # nodep
	from domdf_python_tools.paths import PathPlus, in_directory

	# this package
	from pyproject_parser import PyProject
	from pyproject_parser.cli import _json_encoders  # noqa: F401
	from pyproject_parser.cli import ConfigTracebackHandler, resolve_class
	from pyproject_parser.type_hints import Readme

	if not show_traceback:
		prettify_deprecation_warning()

	pyproject_file = PathPlus(pyproject_file)

	with handle_tracebacks(show_traceback, ConfigTracebackHandler):
		parser: Type[PyProject] = resolve_class(parser_class, "parser-class")

		check_readme = os.getenv("CHECK_README")

		try:

			if field is not None and not field.startswith("project.readme"):
				os.environ["CHECK_README"] = '0'

			config = parser.load(filename=pyproject_file)

			if resolve:
				with in_directory(pyproject_file.parent):
					config.resolve_files()

			raw_config = dom_toml.load(pyproject_file)

			output: Any

			if not field:
				print(sdjson.dumps(config, indent=indent))
				sys.exit(0)

			field_parts = field.split('.')
			if field_parts[0] == "build-system":
				output = config.build_system
			elif field_parts[0] == "project":
				output = config.project
			else:
				output = raw_config[field_parts[0]]

			for part in field_parts[1:]:
				# TODO: slice?
				m = re.match(r"^\[(\d)]$", part)
				if m:
					# array index
					output = output[int(m.group(1))]
				elif isinstance(output, (Readme, License)):
					output = getattr(output, part)
				else:
					# field name
					output = output[part]

			print(sdjson.dumps(output, indent=indent))

		finally:
			if check_readme is None:
				if "CHECK_README" in os.environ:
					del os.environ["CHECK_README"]
			else:
				os.environ["CHECK_README"] = check_readme


@options
@colour_option()
@flag_option("-d", "--show-diff", help="Show a (coloured) diff of changes.")
@auto_default_option(
		"-E",
		"--encoder-class",
		type=click.STRING,
		help="The class to encode the config to TOML with.",
		show_default=True,
		)
@main.command(cls=MarkdownHelpCommand)
def reformat(
		pyproject_file: "PathLike" = "pyproject.toml",
		encoder_class: str = "pyproject_parser:PyProjectTomlEncoder",
		parser_class: str = "pyproject_parser:PyProject",
		show_traceback: bool = False,
		show_diff: bool = False,
		colour: "ColourTrilean" = None,
		):
	"""
	Reformat the given ``pyproject.toml`` file.
	"""

	# 3rd party
	from consolekit.terminal_colours import resolve_color_default  # nodep
	from consolekit.utils import coloured_diff  # nodep
	from domdf_python_tools.paths import PathPlus
	from toml import TomlEncoder

	# this package
	from pyproject_parser import PyProject, _NormalisedName
	from pyproject_parser.cli import ConfigTracebackHandler, resolve_class

	if not show_traceback:
		prettify_deprecation_warning()

	pyproject_file = PathPlus(pyproject_file)

	click.echo(f"Reformatting {str(pyproject_file)!r}")

	with handle_tracebacks(show_traceback, ConfigTracebackHandler):
		parser: Type[PyProject] = resolve_class(parser_class, "parser-class")
		encoder: Type[TomlEncoder] = resolve_class(encoder_class, "encoder-class")

		original_content: List[str] = pyproject_file.read_lines()

		config = parser.load(filename=pyproject_file, set_defaults=False)

		if config.project is not None and isinstance(config.project["name"], _NormalisedName):
			config.project["name"] = config.project["name"].unnormalized

		reformatted_content: List[str] = config.dump(filename=pyproject_file, encoder=encoder).split('\n')

		changed = reformatted_content != original_content

		if show_diff and changed:
			diff = coloured_diff(
					original_content,
					reformatted_content,
					str(pyproject_file),
					str(pyproject_file),
					"(original)",
					"(reformatted)",
					lineterm='',
					)

			click.echo(diff, color=resolve_color_default(colour))

		sys.exit(int(changed))


if __name__ == "__main__":
	sys.exit(main())
