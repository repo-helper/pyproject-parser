#!/usr/bin/env python3
#
#  utils.py
"""
Utility functions.
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
import os
import sys
from typing import TYPE_CHECKING, Optional

# 3rd party
from dom_toml.parser import BadConfigError
from domdf_python_tools.paths import PathPlus
from domdf_python_tools.typing import PathLike

if TYPE_CHECKING:
	# this package
	from pyproject_parser.type_hints import ContentTypes

__all__ = ["render_markdown", "render_rst", "content_type_from_filename", "PyProjectDeprecationWarning"]


def render_markdown(content: str) -> None:
	"""
	Attempt to render the given content as :wikipedia:`Markdown`.

	.. extras-require:: readme
		:pyproject:
		:scope: function

	:param content:
	"""

	try:
		# 3rd party
		import cmarkgfm  # type: ignore[import]  # noqa: F401
		import readme_renderer.markdown  # type: ignore[import]
	except ImportError:  # pragma: no cover
		return

	rendering_result = readme_renderer.markdown.render(content, stream=sys.stderr)

	if rendering_result is None:  # pragma: no cover
		raise BadConfigError("Error rendering README.")


def render_rst(content: str) -> None:
	"""
	Attempt to render the given content as :wikipedia:`ReStructuredText`.

	.. extras-require:: readme
		:pyproject:
		:scope: function

	:param content:
	"""

	try:
		# 3rd party
		import readme_renderer.rst  # type: ignore[import]
	except ImportError:  # pragma: no cover
		return

	rendering_result = readme_renderer.rst.render(content, stream=sys.stderr)

	if rendering_result is None:
		raise BadConfigError("Error rendering README.")


@functools.lru_cache()
def content_type_from_filename(filename: PathLike) -> "ContentTypes":
	"""
	Return the inferred content type for the given (readme) filename.

	:param filename:
	"""

	filename = PathPlus(filename)

	if filename.suffix.lower() == ".md":
		return "text/markdown"
	elif filename.suffix.lower() == ".rst":
		return "text/x-rst"
	elif filename.suffix.lower() == ".txt":
		return "text/plain"

	raise ValueError(f"Unsupported extension for {filename.as_posix()!r}")


def render_readme(
		readme_file: PathLike,
		content_type: Optional["ContentTypes"] = None,
		encoding: str = "UTF-8",
		) -> None:
	"""
	Attempts to render the given readme file.

	:param readme_file:
	:param content_type: The content-type of the readme.
		If :py:obj:`None` the type will be inferred from the file extension.
	:param encoding: The encoding to read the file with.
	"""

	readme_file = PathPlus(readme_file)

	if content_type is None:
		content_type = content_type_from_filename(filename=readme_file)

	content = readme_file.read_text(encoding=encoding)

	if int(os.environ.get("CHECK_README", 1)):
		if content_type == "text/markdown":
			render_markdown(content)
		elif content_type == "text/x-rst":
			render_rst(content)


class PyProjectDeprecationWarning(Warning):
	"""
	Warning for the use of deprecated features in `pyproject.toml`.

	This is a user-facing warning which will be shown by default.
	For developer-facing warnings intended for direct consumers of this library,
	use a standard :class:`DeprecationWarning`.

	.. versionadded:: 0.5.0
	"""
