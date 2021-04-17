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
from pyproject_parser.classes import License, Readme
from pyproject_parser.parsers import BuildSystemParser, PEP621Parser
from pyproject_parser.type_hints import Author, BuildSystemDict, ContentTypes, ProjectDict

__author__: str = "Dominic Davis-Foster"
__copyright__: str = "2021 Dominic Davis-Foster"
__license__: str = "MIT License"
__version__: str = "0.1.2"
__email__: str = "dominic@davis-foster.co.uk"

__all__ = ["PyProject", "PyProjectTomlEncoder", "_PP"]

_PP = TypeVar("_PP", bound="PyProject")


class PyProjectTomlEncoder(dom_toml.TomlEncoder):
	"""
	Custom TOML encoder supporting types from :mod:`pyproject_parser.classes` and packaging_.

	.. _packaging: https://packaging.pypa.io/en/latest/
	"""

	def __init__(self, _dict=dict, preserve=False):
		super().__init__(_dict=_dict, preserve=preserve)
		self.dump_funcs[str] = _dump_str
		self.dump_funcs[Version] = self.dump_packaging_types
		self.dump_funcs[Requirement] = self.dump_packaging_types
		self.dump_funcs[Marker] = self.dump_packaging_types
		self.dump_funcs[SpecifierSet] = self.dump_packaging_types
		self.dump_funcs[Readme] = self.dump_readme
		self.dump_funcs[License] = self.dump_license

	@staticmethod
	def dump_packaging_types(obj: Union[Version, Requirement, Marker, SpecifierSet]) -> str:
		"""
		Convert types from packaging_ to TOML.

		.. _packaging: https://packaging.pypa.io/en/latest/

		:param obj:
		"""

		return _dump_str(str(obj))

	def dump_readme(self, obj: Readme) -> str:
		"""
		Convert a :class:`~.Readme` to TOML.

		:param obj:
		"""

		readme_dict = obj.to_pep621_dict()
		if set(readme_dict.keys()) == {"file"}:
			return _dump_str(readme_dict["file"])

		return self.dump_inline_table(readme_dict)

	def dump_license(self, obj: License) -> str:
		"""
		Convert a :class:`~.License` to TOML.

		:param obj:
		"""

		return self.dump_inline_table(obj.to_pep621_dict())


@serde
@attr.s
class PyProject:
	"""
	Represents a ``pyproject.toml`` file.
	"""

	#: Represents the ``[build-system]`` table defined in :pep:`517` and :pep:`518`.
	build_system: Optional[BuildSystemDict] = attr.ib(default=None)

	#: Represents the ``[project]`` table defined in :pep:`621`.
	project: Optional[ProjectDict] = attr.ib(default=None)

	#: Represents the ``[tool]`` table defined in :pep:`518`.
	tool: Dict[str, Dict[str, Any]] = attr.ib(factory=dict)

	#: The :class:`dom_toml.parser.AbstractConfigParser` to parse the ``[build-system]`` table with.
	build_system_table_parser: ClassVar[BuildSystemParser] = BuildSystemParser()

	#: The :class:`dom_toml.parser.AbstractConfigParser` to parse the ``[project]`` table with.
	project_table_parser: ClassVar[PEP621Parser] = PEP621Parser()

	tool_parsers: ClassVar[Mapping[str, AbstractConfigParser]] = {}
	"""
	A mapping of subtable name to :class:`dom_toml.parser.AbstractConfigParser` to parse the ``[tool]`` table with.

	For example, to parse ``[tool.whey]``:

	.. code-block:: python

		class WheyParser(AbstractConfigParser):
			pass

		class CustomPyProject(PyProject):
			tool_parsers = {"whey": WheyParser()}
	"""

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
			the :meth:`parse() <dom_toml.parser.AbstractConfigParser.parse>` method on
			:attr:`~.build_system_table_parser` and :attr:`~.project_table_parser`.
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

		toml_dict = {"build-system": self.build_system, "project": self.project, "tool": self.tool}
		return dom_toml.dumps(toml_dict, encoder)

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

	@classmethod
	def reformat(cls: Type[_PP], filename: PathLike) -> str:
		"""
		Reformat the given ``pyproject.toml`` file.

		:param filename: The file to reformat.

		:returns: A string containing the reformatted TOML.
		"""

		original_project_table_parser = cls.project_table_parser
		cls.project_table_parser = PEP621Parser()

		try:
			config = cls.load(filename, set_defaults=False)
			return config.dump(filename)
		finally:
			cls.project_table_parser = original_project_table_parser

	def resolve_files(self):
		"""
		Resolve the "file" key in readme_ and license_ (if present) to retrieve the content of the file.

		Calling this method may mean it is no longer possible to recreate
		the original ``TOML`` file from this object.

		.. _readme: https://www.python.org/dev/peps/pep-0621/#readme
		.. _license: https://www.python.org/dev/peps/pep-0621/#license
		"""

		if self.project is not None:
			readme = self.project.get("readme", None)

			if readme is not None and isinstance(readme, Readme):
				readme.resolve(inplace=True)

			lic = self.project.get("license", None)

			if lic is not None and isinstance(lic, License):
				lic.resolve(inplace=True)
