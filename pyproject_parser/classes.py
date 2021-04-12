#!/usr/bin/env python3
#
#  classes.py
"""
Classes to represent readme and license files.
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
import pathlib
from contextlib import suppress
from typing import TYPE_CHECKING, Dict, Mapping, Optional, Type, TypeVar, overload

# 3rd party
import attr
from attr_utils.docstrings import add_attrs_doc
from domdf_python_tools.paths import PathPlus
from domdf_python_tools.typing import PathLike

# this package
from pyproject_parser.utils import content_type_from_filename

if TYPE_CHECKING:
	# this package
	from pyproject_parser.type_hints import ContentTypes, ReadmeDict

__all__ = ["License", "Readme", "_R", "_L"]

_R = TypeVar("_R", bound="Readme")
_L = TypeVar("_L", bound="License")
#
#
# @overload
# def _convert_filename(filename: None) -> None: ...
#
#
# @overload
# def _convert_filename(filename: PathLike) -> pathlib.Path: ...


def _convert_filename(filename: Optional[PathLike]) -> Optional[pathlib.Path]:
	if filename is None:
		return filename
	return pathlib.Path(filename)


# TODO: overloads for __init__


@add_attrs_doc
@attr.s
class Readme:
	"""
	Represents a readme in :pep:`621` configuration.
	"""

	#: The content type of the readme.
	content_type: Optional["ContentTypes"] = attr.ib(default=None)

	#: The charset / encoding of the readme.
	charset: str = attr.ib(default="UTF-8")

	#: The path to the readme file.
	file: Optional[pathlib.Path] = attr.ib(default=None, converter=_convert_filename)

	#: The content of the readme.
	text: Optional[str] = attr.ib(default=None)

	def __attrs_post_init__(self):
		# Sanity checks the supplied arguments

		if self.content_type and not (self.text or self.file):
			raise ValueError(
					"'content_type' cannot be provided on its own; "
					"please provide either 'text' or 'file' or use the 'from_file' method."
					)

		if self.text is None and self.file is None:
			raise TypeError(f"At least one of 'text' and 'file' must be supplied to {self.__class__!r}")

		if self.file is not None and self.content_type is None:
			with suppress(ValueError):
				self.content_type = content_type_from_filename(self.file)

	@content_type.validator
	def _check_content_type(self, attribute, value):
		if value not in {"text/markdown", "text/x-rst", "text/plain", None}:
			raise ValueError(f"Unsupported readme content-type {value!r}")

	@classmethod
	def from_file(cls: Type[_R], file: PathLike, charset: str = "UTF-8") -> _R:
		"""
		Create a :class:`~.Readme` from a filename.

		:param file: The path to the readme file.
		:param charset: he charset / encoding of the readme file.
		"""

		filename = PathPlus(file)

		if filename.suffix.lower() == ".md":
			return cls(file=filename, charset=str(charset), content_type="text/markdown")
		elif filename.suffix.lower() == ".rst":
			return cls(file=filename, charset=str(charset), content_type="text/x-rst")
		elif filename.suffix.lower() == ".txt":
			return cls(file=filename, charset=str(charset), content_type="text/plain")
		else:
			raise ValueError(f"Unrecognised filetype for '{filename!s}'")

	def resolve(self: _R, inplace: bool = False) -> _R:
		"""
		Retrieve the contents of the readme file if the :attr:`~.Readme.file` is set.

		Returns a new :class:`~.Readme` object with :attr:`~.Readme.text` set to the content of the file.

		:param inplace: Modifies and returns the current object rather than creating a new one.
		"""

		text = self.text
		if text is None and self.file:
			text = self.file.read_text(encoding=self.charset)

		if inplace:
			self.text = text
			return self

		else:
			return self.__class__(
					content_type=self.content_type,
					charset=self.charset,
					file=self.file,
					text=text,
					)

	def to_dict(self) -> "ReadmeDict":
		"""
		Construct a dictionary containing the keys of the :class:`~.Readme` object.

		.. seealso::

			* :meth:`~.Readme.to_pep621_dict`
			* :meth:`~.Readme.from_dict`
		"""

		as_dict: "ReadmeDict" = {}

		if self.content_type is not None:
			as_dict["content_type"] = self.content_type

		if self.charset != "UTF-8":
			as_dict["charset"] = self.charset

		if self.file is not None:
			as_dict["file"] = self.file.as_posix()

		if self.text is not None:
			as_dict["text"] = self.text

		return as_dict

	@classmethod
	def from_dict(cls: Type[_R], data: "ReadmeDict") -> _R:
		"""
		Construct a :class:`~.Readme` from a dictionary containing the same keys as the class constructor.

		In addition, ``content_type`` may instead be given as ``content-type``.

		:param data:

		.. seealso::

			* :meth:`~.Readme.to_dict`
			* :meth:`~.Readme.to_pep621_dict`
		"""

		data_dict = dict(data)
		if "content-type" in data_dict:
			data_dict["content_type"] = data_dict.pop("content-type")

		return cls(**data_dict)  # type: ignore[arg-type]

	def to_pep621_dict(self) -> Dict[str, str]:
		"""
		Construct a dictionary containing the keys of the :class:`~.Readme` object,
		suitable for use in :pep:`621` `pyproject.toml`` configuration.

		Unlike :meth:`~.Readme.to_dict` this ignores the ``text`` key if  :attr`~.Readme.file` is set,
		and ignores :attr`~.Readme.content_type` if it matches the content-type inferred
		from the file extension.

		.. seealso:: :meth:`~.Readme.from_dict`
		"""  # noqa: D400

		as_dict = {}

		if self.content_type is not None:
			as_dict["content-type"] = str(self.content_type)

		if self.charset != "UTF-8":
			as_dict["charset"] = self.charset

		if self.file is not None:
			as_dict["file"] = self.file.as_posix()

			if content_type_from_filename(self.file) == self.content_type:
				as_dict.pop("content-type")

		elif self.text is not None:
			as_dict["text"] = self.text

		return as_dict


@add_attrs_doc
@attr.s
class License:
	"""
	Represents a license in :pep:`621` configuration.
	"""

	#: The path to the license file.
	file: Optional[pathlib.Path] = attr.ib(default=None, converter=_convert_filename)

	#: The content of the license.
	text: Optional[str] = attr.ib(default=None)

	def __attrs_post_init__(self):
		# Sanity checks the supplied arguments
		if self.text is None and self.file is None:
			raise TypeError(f"At least one of 'text' and 'file' must be supplied to {self.__class__!r}")

		# if self.text is not None and self.file is not None:
		# 	raise TypeError("'text' and 'filename' are mutually exclusive.")

	def resolve(self: _L, inplace: bool = False) -> _L:
		"""
		Retrieve the contents of the license file if the :attr:`~.License.file` is set.

		Returns a new :class:`~.License` object with :attr:`~.License.text` set to the content of the file.

		:param inplace: Modifies and returns the current object rather than creating a new one.
		"""

		text = self.text
		if text is None and self.file:
			text = self.file.read_text(encoding="UTF-8")

		if inplace:
			self.text = text
			return self

		else:
			return self.__class__(
					file=self.file,
					text=text,
					)

	def to_dict(self) -> Dict[str, str]:
		"""
		Construct a dictionary containing the keys of the :class:`~.License` object.

		.. seealso::

			* :meth:`~.License.to_pep621_dict`
			* :meth:`~.License.from_dict`
		"""

		as_dict = {}

		if self.file is not None:
			as_dict["file"] = self.file.as_posix()
		if self.text is not None:
			as_dict["text"] = self.text

		return as_dict

	@classmethod
	def from_dict(cls: Type[_L], data: Mapping[str, str]) -> _L:
		"""
		Construct a :class:`~.License` from a dictionary containing the same keys as the class constructor.

		Functionally identical to ``License(**data)``
		but provided to give an identical API to :class:`~.Readme`.

		:param data:

		.. seealso::

			* :meth:`~.License.to_dict`
			* :meth:`~.License.to_pep621_dict`
		"""

		return cls(**data)

	def to_pep621_dict(self) -> Dict[str, str]:
		"""
		Construct a dictionary containing the keys of the :class:`~.Readme` object,
		suitable for use in :pep:`621` `pyproject.toml`` configuration.

		Unlike :meth:`~.Readme.to_dict` this ignores the ``text`` key if :attr`~.Readme.file` is set.

		.. seealso:: :meth:`~.Readme.from_dict`
		"""  # noqa: D400

		as_dict = self.to_dict()
		if "file" in as_dict and "text" in as_dict:
			as_dict.pop("text")

		return as_dict
