# stdlib
import pathlib
from typing import Union

# 3rd party
import pytest
from coincidence.regressions import AdvancedDataRegressionFixture
from dom_toml.parser import BadConfigError

# this package
from pyproject_parser.utils import content_type_from_filename, render_rst


@pytest.mark.parametrize(
		"filename, expected",
		[
				("foo.md", "text/markdown"),
				("foo/bar.md", "text/markdown"),
				("foo.rst", "text/x-rst"),
				("foo/bar.rst", "text/x-rst"),
				("foo.txt", "text/plain"),
				("foo/bar.txt", "text/plain"),
				(pathlib.Path("foo.md"), "text/markdown"),
				(pathlib.Path("foo/bar.md"), "text/markdown"),
				(pathlib.Path("foo.rst"), "text/x-rst"),
				(pathlib.Path("foo/bar.rst"), "text/x-rst"),
				(pathlib.Path("foo.txt"), "text/plain"),
				(pathlib.Path("foo/bar.txt"), "text/plain"),
				]
		)
def test_content_type_from_filename(filename: Union[str, pathlib.Path], expected: str):
	assert content_type_from_filename(filename) == expected


def test_render_rst_error(capsys, advanced_data_regression: AdvancedDataRegressionFixture):
	pytest.importorskip("readme_renderer")

	with pytest.raises(BadConfigError, match="Error rendering README."):
		render_rst(".. seealso::", "README.rst")  # A sphinx directive

	outerr = capsys.readouterr()
	assert outerr.err == 'README.rst:1: (ERROR/3) Unknown directive type "seealso".\n\n.. seealso::\n'
	assert outerr.out == ''


def test_render_rst_error_filename(capsys, advanced_data_regression: AdvancedDataRegressionFixture):
	pytest.importorskip("readme_renderer")

	with pytest.raises(BadConfigError, match="Error rendering README."):
		render_rst(".. seealso::", "Different_filename.rst")  # A sphinx directive

	outerr = capsys.readouterr()
	assert outerr.err == 'Different_filename.rst:1: (ERROR/3) Unknown directive type "seealso".\n\n.. seealso::\n'
	assert outerr.out == ''
