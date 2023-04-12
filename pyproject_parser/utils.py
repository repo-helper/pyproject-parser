#!/usr/bin/env python3
#
#  utils.py
"""
Utility functions.
"""
#
#  Copyright © 2021-2023 Dominic Davis-Foster <dominic@davis-foster.co.uk>
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
import io
import os
import sys
from typing import TYPE_CHECKING, Any, Dict, Optional

# 3rd party
from dom_toml.parser import BadConfigError
from domdf_python_tools.paths import PathPlus
from domdf_python_tools.typing import PathLike

if sys.version_info < (3, 11):
	# 3rd party
	import tomli as tomllib
else:
	# 3rd party
	import tomllib

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


def render_rst(content: str, filename: PathLike = "<string>") -> None:
	"""
	Attempt to render the given content as :wikipedia:`ReStructuredText`.

	.. extras-require:: readme
		:pyproject:
		:scope: function

	:param content:
	:param filename: The original filename.

	.. versionchanged:: 0.8.0  Added the ``filename`` argument.
	"""

	try:
		# 3rd party
		import docutils.core
		import readme_renderer.rst  # type: ignore[import]
		from docutils.utils import SystemMessage
		from docutils.writers.html4css1 import Writer

	except ImportError:  # pragma: no cover
		return

	# Adapted from https://github.com/pypa/readme_renderer/blob/main/readme_renderer/rst.py#L106
	settings = readme_renderer.rst.SETTINGS.copy()
	settings["warning_stream"] = io.StringIO()

	writer = Writer()
	writer.translator_class = readme_renderer.rst.ReadMeHTMLTranslator

	try:
		parts = docutils.core.publish_parts(content, str(filename), writer=writer, settings_overrides=settings)
		if parts.get("docinfo", '') + parts.get("fragment", ''):
			# Success!
			return
	except SystemMessage:
		pass

	if not settings["warning_stream"].tell():
		raise BadConfigError("Error rendering README: No content rendered from RST source.")
	else:
		sys.stderr.write(settings["warning_stream"].getvalue())
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
			render_rst(content, readme_file)


class PyProjectDeprecationWarning(Warning):
	"""
	Warning for the use of deprecated features in `pyproject.toml`.

	This is a user-facing warning which will be shown by default.
	For developer-facing warnings intended for direct consumers of this library,
	use a standard :class:`DeprecationWarning`.

	.. versionadded:: 0.5.0
	"""


def _load_toml(filename: PathLike, ) -> Dict[str, Any]:
	r"""
	Parse TOML from the given file.

	:param filename: The filename to read from to.

	:returns: A mapping containing the ``TOML`` data.
	"""

	return tomllib.loads(PathPlus(filename).read_text())
