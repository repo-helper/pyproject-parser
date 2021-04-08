#!/usr/bin/env python3
#
#  __init__.py
"""
Parser for ``pyproject.toml``.
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
from typing import Any, ClassVar, Dict, Mapping, Optional, Type, TypeVar, Union

# 3rd party
import attr
import dom_toml
import toml
from attr_utils.serialise import serde
from dom_toml.encoder import _dump_str
from dom_toml.parser import AbstractConfigParser, BadConfigError
from domdf_python_tools.paths import PathPlus, in_directory
from domdf_python_tools.typing import PathLike
from domdf_python_tools.words import word_join
from packaging.markers import Marker
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import Version

# this package
from pyproject_parser.parsers import BuildSystemParser, PEP621Parser
from pyproject_parser.type_hints import Author, BuildSystemDict, ProjectDict

__all__ = ["PyProject"]

__author__: str = "Dominic Davis-Foster"
__copyright__: str = "2021 Dominic Davis-Foster"
__license__: str = "MIT License"
__version__: str = "0.0.0"
__email__: str = "dominic@davis-foster.co.uk"

_PP = TypeVar("_PP", bound="PyProject")


def _represent_packaging_types(obj: Union[Version, Requirement, Marker, SpecifierSet]):
	return _dump_str(str(obj))


class PyProjectTomlEncoder(dom_toml.TomlEncoder):

	def __init__(self, _dict=dict, preserve=False):
		super().__init__(_dict=_dict, preserve=preserve)
		self.dump_funcs[str] = _dump_str
		self.dump_funcs[Version] = _represent_packaging_types
		self.dump_funcs[Requirement] = _represent_packaging_types
		self.dump_funcs[Marker] = _represent_packaging_types
		self.dump_funcs[SpecifierSet] = _represent_packaging_types


@serde
@attr.s
class PyProject:
	build_system: Optional[BuildSystemDict] = attr.ib(default=None)
	project: Optional[ProjectDict] = attr.ib(default=None)
	tool: Dict[str, Dict[str, Any]] = attr.ib(factory=dict)

	build_system_table_parser: ClassVar[BuildSystemParser] = BuildSystemParser()
	project_table_parser: ClassVar[PEP621Parser] = PEP621Parser()
	tool_parsers: ClassVar[Mapping[str, AbstractConfigParser]] = {}

	@classmethod
	def load(
			cls: Type[_PP],
			filename: PathLike,
			set_defaults: bool = False,
			) -> _PP:
		"""
		Load the ``pyproject.toml`` configuration mapping from the given file.

		:param filename:
		:param set_defaults: If :py:obj:`True`, passes ``set_defaults=True``
			the :meth:`dom_toml.parser.AbstractConfigParser.parse` method on
			:attr:`~.build_system_table_parser` and :attr:`~.project_table_parser` the and
			:attr:`dom_toml.parser.AbstractConfigParser.factories`
			will be set as defaults for the returned mapping.
		"""

		filename = PathPlus(filename)

		project_dir = filename.parent
		config = dom_toml.load(filename)

		keys = set(config.keys())

		build_system_table: Optional[BuildSystemDict] = None
		project_table: Optional[ProjectDict] = None
		tool_table: Dict[str, Dict[str, Any]] = {}

		with in_directory(project_dir):
			if "build-system" in config:
				build_system_table = cls.build_system_table_parser.parse(
						config["build-system"], set_defaults=set_defaults
						)
				keys.remove("build-system")

			if "project" in config:
				project_table = cls.project_table_parser.parse(config["project"], set_defaults=set_defaults)
				keys.remove("project")

			if "tool" in config:
				tool_table = config["tool"]
				keys.remove("tool")

				for tool_name, tool_subtable in tool_table.items():
					if tool_name in cls.tool_parsers:
						tool_table[tool_name] = cls.tool_parsers[tool_name].parse(tool_subtable)

		if keys:
			raise BadConfigError(f"Unexpected top level keys: {word_join(sorted(keys), use_repr=True)}")

		return cls(
				build_system=build_system_table,
				project=project_table,
				tool=tool_table,
				)

	def dumps(
			self,
			encoder: Union[Type[toml.TomlEncoder], toml.TomlEncoder, None] = PyProjectTomlEncoder,
			) -> str:
		"""
		Serialise to TOML.

		:param encoder: The :class:`toml.TomlEncoder` to use for constructing the output string.
		"""

		# TODO: filter out default values (lists and dicts)

		return dom_toml.dumps(self.to_dict(), encoder)

	def dump(
			self,
			filename: PathLike,
			encoder: Union[Type[toml.TomlEncoder], toml.TomlEncoder, None] = PyProjectTomlEncoder,
			):
		"""
		Write as TOML to the given file.

		:param filename: The filename to write to.
		:param encoder: The :class:`toml.TomlEncoder` to use for constructing the output string.

		:returns: A string containing the TOML representation.
		"""

		filename = PathPlus(filename)
		as_toml = self.dumps(encoder=encoder)
		filename.write_clean(as_toml)
		return as_toml
