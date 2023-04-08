# stdlib
import collections
import email.headerregistry
import re
import sys
import warnings
from typing import Type

# 3rd party
import click
import pytest
from coincidence.regressions import AdvancedFileRegressionFixture
from consolekit.testing import CliRunner, Result
from consolekit.tracebacks import handle_tracebacks
from dom_toml.parser import BadConfigError
from domdf_python_tools.utils import redirect_output

# this package
from pyproject_parser.cli import ConfigTracebackHandler, prettify_deprecation_warning, resolve_class
from pyproject_parser.utils import PyProjectDeprecationWarning

exceptions = pytest.mark.parametrize(
		"exception",
		[
				pytest.param(FileNotFoundError("foo.txt"), id="FileNotFoundError"),
				pytest.param(FileExistsError("foo.txt"), id="FileExistsError"),
				pytest.param(Exception("Something's awry!"), id="Exception"),
				pytest.param(ValueError("'age' must be >= 0"), id="ValueError"),
				pytest.param(TypeError("Expected type int, got type str"), id="TypeError"),
				pytest.param(NameError("name 'hello' is not defined"), id="NameError"),
				pytest.param(SyntaxError("invalid syntax"), id="SyntaxError"),
				pytest.param(BadConfigError("Expected a string value for 'name'"), id="BadConfigError"),
				pytest.param(KeyError("name"), id="KeyError"),
				]
		)


@exceptions
def test_traceback_handler(
		exception: Exception,
		advanced_file_regression: AdvancedFileRegressionFixture,
		cli_runner: CliRunner,
		):

	@click.command()
	def demo():  # noqa: MAN002

		with handle_tracebacks(False, ConfigTracebackHandler):
			raise exception

	result: Result = cli_runner.invoke(demo, catch_exceptions=False)
	result.check_stdout(advanced_file_regression)
	assert result.exit_code == 1


@exceptions
def test_traceback_handler_show_traceback(exception: Exception, cli_runner: CliRunner):

	@click.command()
	def demo():  # noqa: MAN002

		with handle_tracebacks(True, ConfigTracebackHandler):
			raise exception

	with pytest.raises(type(exception), match=re.escape(str(exception))):
		cli_runner.invoke(demo, catch_exceptions=False)


@pytest.mark.parametrize("exception", [EOFError(), KeyboardInterrupt(), click.Abort()])
def test_handle_tracebacks_ignored_exceptions_click(
		exception: Exception,
		cli_runner: CliRunner,
		):

	@click.command()
	def demo():  # noqa: MAN002

		with handle_tracebacks(False, ConfigTracebackHandler):
			raise exception

	result: Result = cli_runner.invoke(demo, catch_exceptions=False)

	assert result.stdout.strip() == "Aborted!"
	assert result.exit_code == 1


@pytest.mark.parametrize("exception", [EOFError, KeyboardInterrupt, click.Abort, SystemExit])
def test_handle_tracebacks_ignored_exceptions(exception: Type[Exception]):

	with pytest.raises(exception):  # noqa: PT012
		with handle_tracebacks(False, ConfigTracebackHandler):
			raise exception


def test_resolve_class():
	# stdlib
	import importlib

	assert resolve_class("collections:defaultdict", "class") is collections.defaultdict
	assert resolve_class("importlib:import_module", "class") is importlib.import_module

	if sys.version_info >= (3, 8):
		# stdlib
		import importlib.metadata
		assert resolve_class("importlib.metadata:metadata", "class") is importlib.metadata.metadata

	assert resolve_class("email.headerregistry:Address", "class") is email.headerregistry.Address

	with pytest.raises(click.BadOptionUsage, match="Invalid syntax for '--class'") as e:
		resolve_class("collections.Counter", "class")

	assert e.value.option_name == "class"


@pytest.mark.filterwarnings("default")
def test_prettify_deprecation_warning():

	with redirect_output() as (stdout, stderr):
		prettify_deprecation_warning()
		warnings.warn("This is a warning", PyProjectDeprecationWarning)

	assert stderr.getvalue() == 'WARNING: This is a warning\n'
