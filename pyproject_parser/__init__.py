#!/usr/bin/env python3
#
#  __init__.py
"""
Parser for ``pyproject.toml``.
"""
#
#  Copyright © 2021 Dominic Davis-Foster <dominic@davis-foster.co.uk>
#
#  PyProjectTomlEncoder.dumps based on https://github.com/hukkin/tomli-w
#  MIT Licensed
#  Copyright (c) 2021 Taneli Hukkinen
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
from typing import (
		Any,
		ClassVar,
		Dict,
		Iterator,
		List,
		Mapping,
		MutableMapping,
		Optional,
		Tuple,
		Type,
		TypeVar,
		Union
		)

# 3rd party
import attr
import dom_toml
from dom_toml.decoder import InlineTableDict
from dom_toml.encoder import TomlEncoder
from dom_toml.parser import AbstractConfigParser, BadConfigError
from domdf_python_tools.paths import PathPlus, in_directory
from domdf_python_tools.typing import PathLike
from domdf_python_tools.words import word_join
from packaging.markers import Marker
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import Version
from shippinglabel import normalize

# this package
from pyproject_parser.classes import License, Readme, _NormalisedName
from pyproject_parser.parsers import BuildSystemParser, DependencyGroupsParser, PEP621Parser
from pyproject_parser.type_hints import (  # noqa: F401
		Author,
		BuildSystemDict,
		ContentTypes,
		DependencyGroupsDict,
		ProjectDict,
		_PyProjectAsTomlDict
		)
from pyproject_parser.utils import _load_toml

__author__: str = "Dominic Davis-Foster"
__copyright__: str = "2021 Dominic Davis-Foster"
__license__: str = "MIT License"
__version__: str = "0.13.0"
__email__: str = "dominic@davis-foster.co.uk"

__all__ = ["PyProject", "PyProjectTomlEncoder", "_PP"]

_PP = TypeVar("_PP", bound="PyProject")

_translation_table = {
		8: "\\b",
		9: "\\t",
		10: "\\n",
		12: "\\f",
		13: "\\r",
		92: "\\\\",
		}


def _dump_str(v: str) -> str:
	v = str(v).translate(_translation_table)

	if "'" in v and '"' not in v:
		quote_char = '"'
	elif '"' in v and "'" not in v:
		quote_char = "'"
	else:
		quote_char = '"'
		v = v.replace('"', '\\"')

	return f"{quote_char}{v}{quote_char}"


class PyProjectTomlEncoder(dom_toml.TomlEncoder):
	"""
	Custom TOML encoder supporting types in :mod:`pyproject_parser.classes` and packaging_.

	.. _packaging: https://packaging.pypa.io/en/latest/

	.. autosummary-widths:: 23/64
	"""

	def __init__(self, preserve: bool = False) -> None:
		super().__init__(preserve=preserve)

	def dumps(
			self,
			table: Mapping[str, Any],
			*,
			name: str,
			inside_aot: bool = False,
			) -> Iterator[str]:
		"""
		Serialise the given table.

		:param name: The table name.
		:param inside_aot:

		:rtype:

		.. versionadded:: 0.11.0
		"""

		yielded = False
		literals = []
		tables: List[Tuple[str, Any, bool]] = []
		for k, v in table.items():
			if v is None:
				continue
			if self.preserve and isinstance(v, InlineTableDict):
				literals.append((k, v))
			elif isinstance(v, dict):
				tables.append((k, v, False))
			elif self._is_aot(v):
				tables.extend((k, t, True) for t in v)
			else:
				literals.append((k, v))

		if inside_aot or name and (literals or not tables):
			yielded = True
			yield f"[[{name}]]\n" if inside_aot else f"[{name}]\n"

		if literals:
			yielded = True
			for k, v in literals:
				yield f"{self.format_key_part(k)} = {self.format_literal(v)}\n"

		for k, v, in_aot in tables:
			if yielded:
				yield '\n'
			else:
				yielded = True
			key_part = self.format_key_part(k)
			display_name = f"{name}.{key_part}" if name else key_part

			yield from self.dumps(v, name=display_name, inside_aot=in_aot)

	def format_literal(self, obj: object, *, nest_level: int = 0) -> str:
		"""
		Format a literal value.

		:param obj:
		:param nest_level:

		:rtype:

		.. versionadded:: 0.11.0
		"""

		if isinstance(obj, (str, _NormalisedName)):
			return _dump_str(obj)
		elif isinstance(obj, (Version, Requirement, Marker, SpecifierSet)):
			return self.dump_packaging_types(obj)
		else:
			return super().format_literal(obj, nest_level=nest_level)

	def format_inline_array(self, obj: Union[Tuple, List], nest_level: int) -> str:
		"""
		Format an inline array.

		:param obj:
		:param nest_level:

		:rtype:

		.. versionadded:: 0.11.0
		"""

		if not len(obj):
			return "[]"

		item_indent = "    " * (1 + nest_level)
		closing_bracket_indent = "    " * nest_level
		single_line = "[ " + ", ".join(
				self.format_literal(item, nest_level=nest_level + 1) for item in obj
				) + f",]"

		if len(single_line) <= self.max_width:
			return single_line
		else:
			start = "[\n"
			body = ",\n".join(item_indent + self.format_literal(item, nest_level=nest_level + 1) for item in obj)
			end = f",\n{closing_bracket_indent}]"
			return start + body + end

	@staticmethod
	def dump_packaging_types(obj: Union[Version, Requirement, Marker, SpecifierSet]) -> str:
		"""
		Convert types in packaging_ to TOML.

		.. _packaging: https://packaging.pypa.io/en/latest/

		:param obj:
		"""

		return _dump_str(str(obj))


@attr.s
class PyProject:
	"""
	Represents a ``pyproject.toml`` file.

	:param build_system:

	.. versionchanged:: 0.13.0  Added ``dependency_groups`` and ``dependency_groups_table_parser`` properties.

	.. autosummary-widths:: 4/10

	.. autoclasssumm:: PyProject
		:autosummary-sections: Methods
		:autosummary-exclude-members: __ge__,__gt__,__le__,__lt__,__ne__,__init__,__repr__,__eq__

	.. latex:clearpage::

	.. autosummary-widths:: 1/2

	.. autoclasssumm:: PyProject
		:autosummary-sections: Attributes

	"""

	#: Represents the :pep:`build-system table <518#build-system-table>` defined in :pep:`517` and :pep:`518`.
	build_system: Optional[BuildSystemDict] = attr.ib(default=None)

	#: Represents the :pep:`dependency groups table <735#specification>` defined in :pep:`735`.
	dependency_groups: Optional[DependencyGroupsDict] = attr.ib(default=None)

	#: Represents the :pep621:`project table <table-name>` defined in :pep:`621`.
	project: Optional[ProjectDict] = attr.ib(default=None)

	#: Represents the :pep:`tool table <518#tool-table>` defined in :pep:`518`.
	tool: Dict[str, Dict[str, Any]] = attr.ib(factory=dict)

	build_system_table_parser: ClassVar[BuildSystemParser] = BuildSystemParser()
	"""
	The :class:`~dom_toml.parser.AbstractConfigParser`
	to parse the :pep:`build-system table <518#build-system-table>` with.
	"""

	dependency_groups_table_parser: ClassVar[DependencyGroupsParser] = DependencyGroupsParser()
	"""
	The :class:`~dom_toml.parser.AbstractConfigParser`
	to parse the :pep:`dependency groups table <735#specification>` with.

	.. versionadded:: 0.13.0
	"""

	project_table_parser: ClassVar[PEP621Parser] = PEP621Parser()
	"""
	The :class:`~dom_toml.parser.AbstractConfigParser`
	to parse the :pep621:`project table <table-name>` with.
	"""

	tool_parsers: ClassVar[Mapping[str, AbstractConfigParser]] = {}
	"""
	A mapping of subtable names to :class:`~dom_toml.parser.AbstractConfigParser` objects
	to parse the :pep:`tool table <518#tool-table>` with.

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
		config = _load_toml(filename)

		keys = set(config.keys())

		build_system_table: Optional[BuildSystemDict] = None
		dependency_groups_table: Optional[DependencyGroupsDict] = None
		project_table: Optional[ProjectDict] = None
		tool_table: Dict[str, Dict[str, Any]] = {}

		with in_directory(project_dir):
			if "build-system" in config:
				build_system_table = cls.build_system_table_parser.parse(
						config["build-system"], set_defaults=set_defaults
						)
				keys.remove("build-system")

			if "dependency-groups" in config:
				dependency_groups_table = cls.dependency_groups_table_parser.parse(
						config["dependency-groups"], set_defaults=set_defaults
						)
				keys.remove("dependency-groups")

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
			allowed_top_level = ("build-system", "dependency-groups", "project", "tool")

			for top_level_key in sorted(keys):
				if top_level_key in allowed_top_level:
					continue

				if normalize(top_level_key) in allowed_top_level:
					raise BadConfigError(
							f"Unexpected top-level key {top_level_key!r}. "
							f"Did you mean {normalize(top_level_key)!r}?",
							)

				raise BadConfigError(
						f"Unexpected top-level key {top_level_key!r}. "
						f"Only {word_join(allowed_top_level, use_repr=True)} are allowed.",
						)

		return cls(
				build_system=build_system_table,
				dependency_groups=dependency_groups_table,
				project=project_table,
				tool=tool_table,
				)

	def dumps(
			self,
			encoder: Union[Type[TomlEncoder], TomlEncoder] = PyProjectTomlEncoder,
			) -> str:
		"""
		Serialise to TOML.

		:param encoder: The :class:`~dom_toml.encoder.TomlEncoder` to use for constructing the output string.
		"""

		# TODO: filter out default values (lists and dicts)

		toml_dict: _PyProjectAsTomlDict = {
				"build-system": self.build_system,
				"project": self.project,
				"tool": self.tool,
				"dependency-groups": self.dependency_groups,
				}

		if toml_dict["project"] is not None:
			if "license" in toml_dict["project"] and toml_dict["project"]["license"] is not None:
				toml_dict["project"] = {  # type: ignore[typeddict-item]
					**toml_dict["project"],  # type: ignore[misc,arg-type]
					"license": toml_dict["project"]["license"].to_pep621_dict()
					}

			if "readme" in toml_dict["project"] and toml_dict["project"]["readme"] is not None:
				readme_dict = toml_dict["project"]["readme"].to_pep621_dict()

				_project: Dict[str, Any]

				if set(readme_dict.keys()) == {"file"}:
					_project = {**toml_dict["project"], "readme": readme_dict["file"]}
				else:
					_project = {**toml_dict["project"], "readme": readme_dict}

				toml_dict["project"] = _project  # type: ignore[typeddict-item]

		return dom_toml.dumps(toml_dict, encoder)

	def dump(
			self,
			filename: PathLike,
			encoder: Union[Type[TomlEncoder], TomlEncoder] = PyProjectTomlEncoder,
			) -> str:
		"""
		Write as TOML to the given file.

		:param filename: The filename to write to.
		:param encoder: The :class:`~dom_toml.encoder.TomlEncoder` to use for constructing the output string.

		:returns: A string containing the TOML representation.
		"""

		filename = PathPlus(filename)
		as_toml = self.dumps(encoder=encoder)
		filename.write_clean(as_toml)
		return as_toml

	@classmethod
	def reformat(
			cls: Type[_PP],
			filename: PathLike,
			encoder: Union[Type[TomlEncoder], TomlEncoder] = PyProjectTomlEncoder,
			) -> str:
		"""
		Reformat the given ``pyproject.toml`` file.

		:param filename: The file to reformat.
		:param encoder: The :class:`~dom_toml.encoder.TomlEncoder` to use for constructing the output string.

		:returns: A string containing the reformatted TOML.

		.. versionchanged:: 0.2.0

			* Added the ``encoder`` argument.
			* The parser configured as :attr:`~.project_table_parser` is now used to parse
			  the :pep621:`project table <table-name>`, rather than always using :class:`~.PEP621Parser`.

		"""

		config = cls.load(filename, set_defaults=False)
		if config.project is not None and isinstance(config.project["name"], _NormalisedName):
			config.project["name"] = config.project["name"].unnormalized

		return config.dump(filename, encoder=encoder)

	def resolve_files(self) -> None:
		"""
		Resolve the ``file`` key in :pep621:`readme` and :pep621:`license`
		(if present) to retrieve the content of the file.

		Calling this method may mean it is no longer possible to recreate
		the original ``TOML`` file from this object.
		"""  # noqa: D400

		if self.project is not None:
			readme = self.project.get("readme", None)

			if readme is not None and isinstance(readme, Readme):
				readme.resolve(inplace=True)

			lic = self.project.get("license", None)

			if lic is not None and isinstance(lic, License):
				lic.resolve(inplace=True)

	@classmethod
	def from_dict(cls: Type[_PP], d: Mapping[str, Any]) -> _PP:
		"""
		Construct an instance of :class:`~.PyProject` from a dictionary.

		:param d: The dictionary.
		"""

		kwargs = {}

		for key, value in d.items():
			if key == "build-system":
				key = "build_system"
			elif key == "dependency-groups":
				key = "dependency_groups"

			kwargs[key] = value

		return cls(**kwargs)

	def to_dict(self) -> MutableMapping[str, Any]:
		"""
		Returns a dictionary containing the contents of the class.

		.. seealso:: :func:`attr.asdict`
		"""

		return {
				"build_system": self.build_system,
				"project": self.project,
				"tool": self.tool,
				"dependency_groups": self.dependency_groups,
				}
