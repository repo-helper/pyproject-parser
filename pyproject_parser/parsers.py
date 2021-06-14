#!/usr/bin/env python3
#
#  parsers.py
"""
TOML configuration parsers.
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
import collections.abc
import os
import re
from abc import ABCMeta
from collections import defaultdict
from typing import Any, Callable, ClassVar, Dict, Iterable, List, Mapping, Union, cast

# 3rd party
from apeye import URL
from apeye.email_validator import EmailSyntaxError, validate_email
from dom_toml.parser import TOML_TYPES, AbstractConfigParser, BadConfigError, construct_path
from natsort import natsorted, ns
from packaging.specifiers import InvalidSpecifier, Specifier, SpecifierSet
from packaging.version import InvalidVersion, Version
from shippinglabel import normalize
from shippinglabel.classifiers import validate_classifiers
from shippinglabel.requirements import ComparableRequirement, combine_requirements

# this package
from pyproject_parser.classes import License, Readme, _NormalisedName
from pyproject_parser.type_hints import Author, BuildSystemDict, ProjectDict
from pyproject_parser.utils import content_type_from_filename, render_readme

__all__ = [
		"RequiredKeysConfigParser",
		"BuildSystemParser",
		"PEP621Parser",
		]

name_re = re.compile("^([A-Z0-9]|[A-Z0-9][A-Z0-9._-]*[A-Z0-9])$", flags=re.IGNORECASE)


class RequiredKeysConfigParser(AbstractConfigParser, metaclass=ABCMeta):
	"""
	Abstract base class for TOML configuration parsers which have required keys.

	.. autosummary-widths:: 17/32
		:html: 1/2
	"""

	required_keys: ClassVar[List[str]]
	table_name: ClassVar[str]

	def parse(
			self,
			config: Dict[str, TOML_TYPES],
			set_defaults: bool = False,
			) -> Dict[str, TOML_TYPES]:
		"""
		Parse the TOML configuration.

		:param config:
		:param set_defaults: If :py:obj:`True`, the values in
			:attr:`self.defaults <dom_toml.parser.AbstractConfigParser.defaults>` and
			:attr:`self.factories <dom_toml.parser.AbstractConfigParser.factories>`
			will be set as defaults for the returned mapping.
		"""

		for key in self.required_keys:
			if key in config:
				continue
			elif set_defaults and (key in self.defaults or key in self.factories):
				continue  # pragma: no cover https://github.com/nedbat/coveragepy/issues/198
			else:
				raise BadConfigError(f"The {construct_path([self.table_name, key])!r} field must be provided.")

		return super().parse(config, set_defaults)

	def assert_sequence_not_str(
			self,
			obj: Any,
			path: Iterable[str],
			what: str = "type",
			) -> None:
		"""
		Assert that ``obj`` is a :class:`~typing.Sequence` and not a :class:`str`,
		otherwise raise an error with a helpful message.

		:param obj: The object to check the type of.
		:param path: The elements of the path to ``obj`` in the TOML mapping.
		:param what: What ``obj`` is, e.g. ``'type'``, ``'value type'``.

		.. latex:clearpage::
		"""  # noqa: D400

		if isinstance(obj, str):
			name = construct_path(path)
			raise TypeError(
					f"Invalid {what} for {name!r}: "
					f"expected <class 'collections.abc.Sequence'>, got {type(obj)!r}",
					)

		self.assert_type(obj, collections.abc.Sequence, path, what=what)


class BuildSystemParser(RequiredKeysConfigParser):
	"""
	Parser for the :pep:`build-system table <518#build-system-table>` table from ``pyproject.toml``.

	.. autosummary-widths:: 17/32
		:html: 4/10
	"""  # noqa: RST399

	table_name: ClassVar[str] = "build-system"
	required_keys: ClassVar[List[str]] = ["requires"]
	keys: ClassVar[List[str]] = ["requires", "build-backend", "backend-path"]
	factories: ClassVar[Dict[str, Callable[..., Any]]] = {"requires": list}
	defaults: ClassVar[Dict[str, Any]] = {"build-backend": None, "backend-path": None}

	def parse_requires(self, config: Dict[str, TOML_TYPES]) -> List[ComparableRequirement]:
		"""
		Parse the :pep:`requires <518#build-system-table>` key.

		:param config: The unparsed TOML config for the :pep:`build-system table <518#build-system-table>`.
		"""  # noqa: RST399

		parsed_dependencies = set()
		key_path = [self.table_name, "requires"]

		self.assert_sequence_not_str(config["requires"], key_path)

		for idx, keyword in enumerate(config["requires"]):
			self.assert_indexed_type(keyword, str, key_path, idx=idx)
			parsed_dependencies.add(ComparableRequirement(keyword))

		return sorted(combine_requirements(parsed_dependencies))

	def parse_build_backend(self, config: Dict[str, TOML_TYPES]) -> str:
		"""
		Parse the ``build_backend`` key defined by :pep:`517`.

		:param config: The unparsed TOML config for the :pep:`build-system table <518#build-system-table>`.
		"""  # noqa: RST399

		build_backend = config["build-backend"]
		self.assert_type(build_backend, str, [self.table_name, "build-backend"])
		return build_backend

	def parse_backend_path(self, config: Dict[str, TOML_TYPES]) -> List[str]:
		"""
		Parse the ``backend-path`` key defined by :pep:`517`.

		:param config: The unparsed TOML config for the :pep:`build-system table <518#build-system-table>`.
		"""  # noqa: RST399

		parsed_backend_paths = []
		key_path = [self.table_name, "backend-path"]

		self.assert_sequence_not_str(config["backend-path"], key_path)

		for idx, path in enumerate(config["backend-path"]):
			self.assert_indexed_type(path, str, key_path, idx=idx)
			parsed_backend_paths.append(path)

		return parsed_backend_paths

	def parse(  # type: ignore[override]
		self,
		config: Dict[str, TOML_TYPES],
		set_defaults: bool = False,
		) -> BuildSystemDict:
		"""
		Parse the TOML configuration.

		:param config:
		:param set_defaults: If :py:obj:`True`, the values in
			:attr:`self.defaults <dom_toml.parser.AbstractConfigParser.defaults>` and
			:attr:`self.factories <dom_toml.parser.AbstractConfigParser.factories>`
			will be set as defaults for the returned mapping.

		:rtype:

		.. latex:clearpage::
		"""

		parsed_config = super().parse(config, set_defaults)

		if (
				parsed_config.get("backend-path", None) is not None
				and parsed_config.get("build-backend", None) is None
				):
			raise BadConfigError(
					f"{construct_path([self.table_name, 'backend-path'])!r} "
					f"cannot be specified without also specifying "
					f"{construct_path([self.table_name, 'build-backend'])!r}"
					)

		return cast(BuildSystemDict, parsed_config)


class PEP621Parser(RequiredKeysConfigParser):
	"""
	Parser for :pep:`621` metadata from ``pyproject.toml``.

	.. autosummary-widths:: 1/2
		:html: 1/2
	"""

	table_name: ClassVar[str] = "project"
	keys: List[str] = [
			"name",
			"version",
			"description",
			"readme",
			"requires-python",
			"license",
			"authors",
			"maintainers",
			"keywords",
			"classifiers",
			"urls",
			"scripts",
			"gui-scripts",
			"entry-points",
			"dependencies",
			"optional-dependencies",
			]
	required_keys: ClassVar[List[str]] = ["name"]
	defaults: ClassVar[Dict[str, Any]] = {
			"version": None,
			"description": None,
			"readme": None,
			"requires-python": None,
			"license": None,
			}
	factories: ClassVar[Dict[str, Callable[..., Any]]] = {
			"authors": list,
			"maintainers": list,
			"keywords": list,
			"classifiers": list,
			"urls": dict,
			"scripts": dict,
			"gui-scripts": dict,
			"entry-points": dict,
			"dependencies": list,
			"optional-dependencies": dict,
			}

	@staticmethod
	def parse_name(config: Dict[str, TOML_TYPES]) -> str:
		"""
		Parse the :pep621:`name` key, giving the name of the project.

		* **Format**: :toml:`String`
		* **Core Metadata**: :core-meta:`Name`

		This key is required, and must be defined statically.

		Tools SHOULD normalize this name, as specified by :pep:`503`,
		as soon as it is read for internal consistency.

		:bold-title:`Example:`

		.. code-block:: TOML

			[project]
			name = "spam"

		:param config: The unparsed TOML config for the :pep621:`project table <table-name>`.
		"""

		normalized_name = _NormalisedName(normalize(config["name"]))
		normalized_name.unnormalized = config["name"]

		# https://packaging.python.org/specifications/core-metadata/#name
		if not name_re.match(normalized_name):
			raise BadConfigError("The value for 'project.name' is invalid.")

		return normalized_name

	@staticmethod
	def parse_version(config: Dict[str, TOML_TYPES]) -> Version:
		"""
		Parse the :pep621:`version` key, giving the version of the project as supported by :pep:`440`.

		* **Format**: :toml:`String`
		* **Core Metadata**: :core-meta:`Version`

		Users SHOULD prefer to specify normalized versions.

		:bold-title:`Example:`

		.. code-block:: TOML

			[project]
			version = "2020.0.0"

		:param config: The unparsed TOML config for the :pep621:`project table <table-name>`.
		"""

		version = str(config["version"])

		try:
			return Version(str(version))
		except InvalidVersion as e:
			raise BadConfigError(str(e))

	def parse_description(self, config: Dict[str, TOML_TYPES]) -> str:
		"""
		Parse the :pep621:`description` key, giving a summary description of the project.

		* **Format**: :toml:`String`
		* **Core Metadata**: :core-meta:`Summary`

		:bold-title:`Example:`

		.. code-block:: TOML

			[project]
			description = "Lovely Spam! Wonderful Spam!"

		:param config: The unparsed TOML config for the :pep621:`project table <table-name>`.
		"""

		description = config["description"]

		self.assert_type(description, str, ["project", "description"])

		return description.strip()

	@staticmethod
	def parse_readme(config: Dict[str, TOML_TYPES]) -> Readme:
		"""
		Parse the :pep621:`readme` key, giving the full description of the project (i.e. the README).

		* **Format**: :toml:`String` or :toml:`table`
		* **Core Metadata**: :core-meta:`Description`

		This field accepts either a string or a table.
		If it is a string then it is the relative path to a text file containing the full description.
		The file's encoding MUST be UTF-8, and have one of the following content types:

		* ``text/markdown``, with a case-insensitive ``.md`` suffix.
		* ``text/x-rst``, with a case-insensitive ``.rst`` suffix.
		* ``text/plain``, with a case-insensitive ``.txt`` suffix.

		If a tool recognizes more extensions than this PEP, they MAY infer the content-type for the user
		without specifying this field as dynamic.
		For all unrecognized suffixes when a content-type is not provided, tools MUST raise an error.

		.. space::
		.. latex:clearpage::

		The readme field may instead be a table with the following keys:

		* ``file`` -- a string value representing a relative path to a file containing the full description.
		* ``text`` -- a string value which is the full description.
		* ``content-type`` -- (required) a string specifying the content-type of the full description.
		* ``charset`` -- (optional, default UTF-8) the encoding of the ``file``.
		  Tools MAY support other encodings if they choose to.

		The ``file`` and ``text`` keys are mutually exclusive, but one must be provided in the table.

		:bold-title:`Examples:`

		.. code-block:: TOML

			[project]
			readme = "README.rst"

			[project.readme]
			file = "README.rst"
			content-type = "text/x-rst"
			encoding = "UTF-8"

			[project.readme]
			text = "Spam is a brand of canned cooked pork made by Hormel Foods Corporation."
			content-type = "text/x-rst"

		:param config: The unparsed TOML config for the :pep621:`project table <table-name>`.
		"""

		readme: Union[Dict, str] = config["readme"]

		if isinstance(readme, str):
			# path to readme_file
			readme_content_type = content_type_from_filename(readme)
			render_readme(readme, readme_content_type)
			return Readme(file=readme, content_type=readme_content_type)

		elif isinstance(readme, dict):
			if not readme:
				raise BadConfigError("The 'project.readme' table cannot be empty.")

			if "file" in readme and "text" in readme:
				raise BadConfigError(
						"The 'project.readme.file' and 'project.readme.text' keys "
						"are mutually exclusive."
						)

			elif set(readme.keys()) in ({"file"}, {"file", "charset"}):
				readme_encoding = readme.get("charset", "UTF-8")
				render_readme(readme["file"], encoding=readme_encoding)
				readme_content_type = content_type_from_filename(readme["file"])
				return Readme(file=readme["file"], content_type=readme_content_type, charset=readme_encoding)

			elif set(readme.keys()) in ({"file", "content-type"}, {"file", "charset", "content-type"}):
				readme_encoding = readme.get("charset", "UTF-8")
				render_readme(readme["file"], encoding=readme_encoding)
				return Readme(file=readme["file"], content_type=readme["content-type"], charset=readme_encoding)

			elif "content-type" in readme and "text" not in readme:
				raise BadConfigError(
						"The 'project.readme.content-type' key cannot be provided on its own; "
						"Please provide the 'project.readme.text' key too."
						)

			elif "charset" in readme and "text" not in readme:
				raise BadConfigError(
						"The 'project.readme.charset' key cannot be provided on its own; "
						"Please provide the 'project.readme.text' key too."
						)

			elif "text" in readme:
				if "content-type" not in readme:
					raise BadConfigError(
							"The 'project.readme.content-type' key must be provided "
							"when 'project.readme.text' is given."
							)
				elif readme["content-type"] not in {"text/markdown", "text/x-rst", "text/plain"}:
					raise BadConfigError(
							f"Unrecognised value for 'project.readme.content-type': {readme['content-type']!r}"
							)

				if "charset" in readme:
					raise BadConfigError(
							"The 'project.readme.charset' key cannot be provided "
							"when 'project.readme.text' is given."
							)

				return Readme(text=readme["text"], content_type=readme["content-type"])

			else:
				raise BadConfigError(f"Unknown format for 'project.readme': {readme!r}")

		raise TypeError(f"Unsupported type for 'project.readme': {type(readme)!r}")

	@staticmethod
	def parse_requires_python(config: Dict[str, TOML_TYPES]) -> Specifier:
		"""
		Parse the :pep621:`requires-python` key, giving the Python version requirements of the project.

		The requirement should be in the form of a :pep:`508` marker.

		* **Format**: :toml:`String`
		* **Core Metadata**: :core-meta:`Requires-Python`

		:bold-title:`Example:`

		.. code-block:: TOML

			[project]
			requires-python = ">=3.6"

		:param config: The unparsed TOML config for the :pep621:`project table <table-name>`.

		:rtype:

		.. latex:clearpage::
		"""

		version = str(config["requires-python"])

		try:
			return SpecifierSet(str(version))
		except InvalidSpecifier as e:
			raise BadConfigError(str(e))

	@staticmethod
	def parse_license(config: Dict[str, TOML_TYPES]) -> License:
		"""
		Parse the :pep621:`license` key.

		* **Format**: :toml:`Table`
		* **Core Metadata**: :core-meta:`License`

		The table may have one of two keys:

		* ``file`` -- a string value that is a relative file path to the file which contains
		  the license for the project. The file's encoding MUST be UTF-8.
		* ``text`` -- string value which is the license of the project.

		These keys are mutually exclusive,  so a tool MUST raise an error if the metadata specifies both keys.

		:bold-title:`Example:`

		.. code-block:: TOML

			[project.license]
			file = "LICENSE.rst"

			[project.license]
			file = "COPYING"

			[project.license]
			text = \"\"\"
			This software may only be obtained by sending the author a postcard,
			and then the user promises not to redistribute it.
			\"\"\"

		:param config: The unparsed TOML config for the :pep621:`project table <table-name>`.
		"""  # noqa: D300,D301

		license = config["license"]  # noqa: A001  # pylint: disable=redefined-builtin

		if "text" in license and "file" in license:
			raise BadConfigError(
					"The 'project.license.file' and 'project.license.text' keys "
					"are mutually exclusive."
					)
		elif "text" in license:
			return License(text=str(license["text"]))
		elif "file" in license:
			os.stat(license["file"])
			return License(license["file"])
		else:
			raise BadConfigError("The 'project.license' table should contain one of 'text' or 'file'.")

	@staticmethod
	def _parse_authors(config: Dict[str, TOML_TYPES], key_name: str = "authors") -> List[Author]:
		all_authors: List[Author] = []

		for idx, author in enumerate(config[key_name]):
			name = author.get("name", None)
			email = author.get("email", None)

			if name is not None and ',' in name:
				raise BadConfigError(f"The 'project.{key_name}[{idx}].name' key cannot contain commas.")

			if email is not None:
				try:
					email = validate_email(email).email
				except EmailSyntaxError as e:
					raise BadConfigError(f"Invalid email {email!r}: {e} ")

			all_authors.append({"name": name, "email": email})

		return all_authors

	def parse_authors(self, config: Dict[str, TOML_TYPES]) -> List[Author]:
		"""
		Parse the :pep621:`authors` key.

		* **Format**: :toml:`Array` of :toml:`inline tables <inline table>` with string keys and values
		* **Core Metadata**: :core-meta:`Author/Author-email`

		The tables list the people or organizations considered to be the "authors" of the project.

		Each table has 2 keys: ``name`` and ``email``.
		Both values must be strings.

		* The ``name`` value MUST be a valid email name (i.e. whatever can be put as a name,
		  before an email, in :rfc:`822`) and not contain commas.
		* The ``email`` value MUST be a valid email address.

		Both keys are optional.

		Using the data to fill in core metadata is as follows:

		1. If only ``name`` is provided, the value goes in :core-meta:`Author`.
		2. If only ``email`` is provided, the value goes in :core-meta:`Author-email`.
		3. If both ``email`` and ``name`` are provided, the value goes in :core-meta:`Author-email`.
		   The value should be formatted as ``{name} <{email}>``
		   (with appropriate quoting, e.g. using :class:`email.headerregistry.Address`).
		4. Multiple values should be separated by commas.

		:bold-title:`Example:`

		.. code-block:: TOML

			[project]
			authors = [
				{email = "hi@pradyunsg.me"},
				{name = "Tzu-Ping Chung"}
			]

			[[project.authors]]
			name = "Tzu-Ping Chung"

		:param config: The unparsed TOML config for the :pep621:`project table <table-name>`.
		"""

		return self._parse_authors(config, "authors")

	def parse_maintainers(self, config: Dict[str, TOML_TYPES]) -> List[Author]:
		"""
		Parse the :pep621:`maintainers` key.

		* **Format**: :toml:`Array` of :toml:`inline tables <inline table>` with string keys and values
		* **Core Metadata**: :core-meta:`Maintainer/Maintainer-email`

		The tables list the people or organizations considered to be the "maintainers" of the project.

		Each table has 2 keys: ``name`` and ``email``.
		Both values must be strings.

		* The ``name`` value MUST be a valid email name (i.e. whatever can be put as a name,
		  before an email, in :rfc:`822`) and not contain commas.
		* The ``email`` value MUST be a valid email address.

		Both keys are optional.

		1. If only ``name`` is provided, the value goes in :core-meta:`Maintainer`.
		2. If only ``email`` is provided, the value goes in :core-meta:`Maintainer-email`.
		3. If both ``email`` and ``name`` are provided, the value goes in :core-meta:`Maintainer-email`,
		   with the format ``{name} <{email}>``
		   (with appropriate quoting, e.g. using :class:`email.headerregistry.Address`).
		4. Multiple values should be separated by commas.

		:param config: The unparsed TOML config for the :pep621:`project table <table-name>`.
		"""

		return self._parse_authors(config, "maintainers")

	def parse_keywords(self, config: Dict[str, TOML_TYPES]) -> List[str]:
		"""
		Parse the :pep621:`keywords` key, giving the keywords for the project.

		* **Format**: :toml:`Array` of :toml:`strings <string>`
		* **Core Metadata**: :core-meta:`Keywords`

		:bold-title:`Example:`

		.. code-block:: TOML

			[project]
			keywords = ["egg", "bacon", "sausage", "tomatoes", "Lobster Thermidor"]

		:param config: The unparsed TOML config for the :pep621:`project table <table-name>`.
		"""

		parsed_keywords = set()
		key_path = [self.table_name, "keywords"]

		self.assert_sequence_not_str(config["keywords"], key_path)

		for idx, keyword in enumerate(config["keywords"]):
			self.assert_indexed_type(keyword, str, key_path, idx=idx)
			parsed_keywords.add(keyword)

		return natsorted(parsed_keywords, alg=ns.GROUPLETTERS)

	def parse_classifiers(self, config: Dict[str, TOML_TYPES]) -> List[str]:
		"""
		Parse the :pep621:`classifiers` key, giving the `trove classifiers`_ which apply to the project.

		.. _trove classifiers: https://pypi.org/classifiers/

		* **Format**: :toml:`Array` of :toml:`strings <string>`
		* **Core Metadata**: :core-meta:`Classifiers`

		:bold-title:`Example:`

		.. code-block:: TOML

			[project]
			classifiers = [
				"Development Status :: 4 - Beta",
				"Programming Language :: Python"
			]

		:param config: The unparsed TOML config for the :pep621:`project table <table-name>`.
		"""

		parsed_classifiers = set()
		key_path = [self.table_name, "classifiers"]

		self.assert_sequence_not_str(config["classifiers"], key_path)

		for idx, keyword in enumerate(config["classifiers"]):
			self.assert_indexed_type(keyword, str, key_path, idx=idx)
			parsed_classifiers.add(keyword)

		validate_classifiers(parsed_classifiers)

		return natsorted(parsed_classifiers)

	def parse_urls(self, config: Dict[str, TOML_TYPES]) -> Dict[str, str]:
		"""
		Parse the :pep621:`urls` table.

		* **Format**: :toml:`Table`, with keys and values of :toml:`strings <string>`
		* **Core Metadata**: :core-meta:`Project-URL`

		A table of URLs where the key is the URL label and the value is the URL itself.

		:bold-title:`Example:`

		.. code-block:: TOML

			[project.urls]
			homepage = "https://example.com"
			documentation = "https://readthedocs.org"
			repository = "https://github.com"
			changelog = "https://github.com/me/spam/blob/master/CHANGELOG.md"

		:param config: The unparsed TOML config for the :pep621:`project table <table-name>`.
		"""

		parsed_urls = {}

		project_urls = config["urls"]

		self.assert_type(project_urls, dict, ["project", "urls"])

		for category, url in project_urls.items():
			self.assert_value_type(url, str, ["project", "urls", category])

			parsed_urls[category] = str(URL(url))

		return parsed_urls

	def parse_scripts(self, config: Dict[str, TOML_TYPES]) -> Dict[str, str]:
		"""
		Parse the :pep621:`scripts` table.

		**Format**: :toml:`Table`, with keys and values of :toml:`strings <string>`

		The console scripts provided by the project.

		The keys are the names of the scripts and the values are the object references
		in the form ``module.submodule:object``.

		:bold-title:`Example:`

		.. code-block:: TOML

			[project.scripts]
			spam-cli = "spam:main_cli"

		:param config: The unparsed TOML config for the :pep621:`project table <table-name>`.
		"""

		scripts = config["scripts"]

		self.assert_type(scripts, dict, ["project", "scripts"])

		for name, func in scripts.items():
			self.assert_value_type(func, str, ["project", "scripts", name])

		return scripts

	def parse_gui_scripts(self, config: Dict[str, TOML_TYPES]) -> Dict[str, str]:
		"""
		Parse the :pep621:`gui-scripts` table.

		**Format**: table, with keys and values of strings

		The graphical application scripts provided by the project.

		The keys are the names of the scripts and the values are the object references
		in the form ``module.submodule:object``.

		:bold-title:`Example:`

		.. code-block:: TOML

			[project.gui-scripts]
			spam-gui = "spam.gui:main_gui"

		:param config: The unparsed TOML config for the :pep621:`project table <table-name>`.
		"""

		gui_scripts = config["gui-scripts"]

		self.assert_type(gui_scripts, dict, ["project", "gui-scripts"])

		for name, func in gui_scripts.items():
			self.assert_value_type(func, str, ["project", "gui-scripts", name])

		return gui_scripts

	def parse_entry_points(self, config: Dict[str, TOML_TYPES]) -> Dict[str, Dict[str, str]]:
		"""
		Parse the :pep621:`entry-points` table.

		**Format**: :toml:`Table` of :toml:`tables <table>`, with keys and values of :toml:`strings <string>`

		Each sub-table's name is an entry point group.

		* Users MUST NOT create nested sub-tables but instead keep the entry point groups to only one level deep.
		* Users MUST NOT created sub-tables for ``console_scripts`` or ``gui_scripts``.
		  Use ``[project.scripts]`` and ``[project.gui-scripts]`` instead.

		See the `entry point specification`_ for more details.

		.. _entry point specification: https://packaging.python.org/specifications/entry-points/

		:bold-title:`Example:`

		.. code-block:: TOML

			[project.entry-points."spam.magical"]
			tomatoes = "spam:main_tomatoes"

			# pytest plugins refer to a module, so there is no ':obj'
			[project.entry-points.pytest11]
			nbval = "nbval.plugin"

		:param config: The unparsed TOML config for the :pep621:`project table <table-name>`.

		:rtype:

		.. latex:clearpage::
		"""

		entry_points = config["entry-points"]

		self.assert_type(entry_points, dict, ["project", "entry-points"])

		for group, sub_table in entry_points.items():

			self.assert_value_type(sub_table, dict, ["project", "entry-points", group])

			if normalize(group) in "console-scripts":
				name = construct_path(["project", "entry-points"])
				suggested_name = construct_path(["project", "scripts"])
				raise BadConfigError(
						f"{name!r} may not contain a {group!r} sub-table. Use {suggested_name!r} instead."
						)
			elif normalize(group) in "gui-scripts":
				name = construct_path(["project", "entry-points"])
				suggested_name = construct_path(["project", "gui-scripts"])
				raise BadConfigError(
						f"{name!r} may not contain a {group!r} sub-table. Use {suggested_name!r} instead."
						)

			for name, func in sub_table.items():
				self.assert_value_type(func, str, ["project", "entry-points", group, name])

		return entry_points

	def parse_dependencies(self, config: Dict[str, TOML_TYPES]) -> List[ComparableRequirement]:
		"""
		Parse the :pep621:`dependencies` key, giving the dependencies of the project.

		* **Format**: :toml:`Array` of :pep:`508` strings
		* **Core Metadata**: :core-meta:`Requires-Dist`

		Each string MUST be formatted as a valid :pep:`508` string.

		:bold-title:`Example:`

		.. code-block:: TOML

			[project]
			dependencies = [
				"httpx",
				"gidgethub[httpx]>4.0.0",
				"django>2.1; os_name != 'nt'",
				"django>2.0; os_name == 'nt'"
			]

		:param config: The unparsed TOML config for the :pep621:`project table <table-name>`.
		"""

		parsed_dependencies = set()

		key_path = [self.table_name, "dependencies"]

		self.assert_sequence_not_str(config["dependencies"], key_path)

		for idx, keyword in enumerate(config["dependencies"]):
			self.assert_indexed_type(keyword, str, key_path, idx=idx)
			parsed_dependencies.add(ComparableRequirement(keyword))

		return sorted(combine_requirements(parsed_dependencies))

	def parse_optional_dependencies(
			self,
			config: Dict[str, TOML_TYPES],
			) -> Dict[str, List[ComparableRequirement]]:
		"""
		Parse the :pep621:`optional-dependencies` table, giving the optional dependencies of the project.

		* **Format**: :toml:`Table` with values of :toml:`arrays <Array>` of :pep:`508` strings
		* **Core Metadata**: :core-meta:`Requires-Dist` and :core-meta:`Provides-Extra`

		.. raw:: html

			</br>

		* The keys specify an extra, and must be valid Python identifiers.
		* The values are arrays of strings, which must be valid :pep:`508` strings.

		:bold-title:`Example:`

		.. code-block:: TOML

			[project.optional-dependencies]
			test = [
			  "pytest < 5.0.0",
			  "pytest-cov[all]"
			]

		:param config: The unparsed TOML config for the :pep621:`project table <table-name>`.
		"""

		parsed_optional_dependencies = defaultdict(set)

		err_template = (
				f"Invalid type for 'project.optional-dependencies{{idx_string}}': "
				f"expected {dict!r}, got {{actual_type!r}}"
				)

		optional_dependencies: Mapping[str, Any] = config["optional-dependencies"]

		if not isinstance(optional_dependencies, dict):
			raise TypeError(err_template.format(idx_string='', actual_type=type(optional_dependencies)))

		for extra, dependencies in optional_dependencies.items():
			if not extra.isidentifier():
				raise TypeError(f"Invalid extra name {extra!r}: must be a valid Python identifier")

			self.assert_sequence_not_str(dependencies, path=["project", "optional-dependencies", extra])

			for idx, dep in enumerate(dependencies):
				if isinstance(dep, str):
					parsed_optional_dependencies[extra].add(ComparableRequirement(dep))
				else:
					raise TypeError(err_template.format(idx_string=f'.{extra}[{idx}]', actual_type=type(dep)))

		return {e: sorted(combine_requirements(d)) for e, d in parsed_optional_dependencies.items()}

	def parse(  # type: ignore[override]
		self,
		config: Dict[str, TOML_TYPES],
		set_defaults: bool = False,
		) -> ProjectDict:
		"""
		Parse the TOML configuration.

		:param config:
		:param set_defaults: If :py:obj:`True`, the values in
			:attr:`self.defaults <dom_toml.parser.AbstractConfigParser.defaults>` and
			:attr:`self.factories <dom_toml.parser.AbstractConfigParser.factories>`
			will be set as defaults for the returned mapping.
		"""

		dynamic_fields = config.get("dynamic", [])

		if "name" in dynamic_fields:
			raise BadConfigError("The 'project.name' field may not be dynamic.")

		super_parsed_config = super().parse(config, set_defaults=set_defaults)

		return {
				**super_parsed_config,  # type: ignore[misc]
				"dynamic": dynamic_fields,
				}
