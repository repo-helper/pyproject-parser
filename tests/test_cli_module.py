# stdlib
import collections
import email.headerregistry
import re
import sys

# 3rd party
import click
import pytest
from consolekit.testing import CliRunner, Result
from consolekit.tracebacks import handle_tracebacks
from dom_toml.parser import BadConfigError

# this package
from pyproject_parser.cli import ConfigTracebackHandler, resolve_class

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
		exception,
		file_regression,
		cli_runner: CliRunner,
		):

	@click.command()
	def demo():

		with handle_tracebacks(False, ConfigTracebackHandler):
			raise exception

	result: Result = cli_runner.invoke(demo, catch_exceptions=False)
	result.check_stdout(file_regression)
	assert result.exit_code == 1


@exceptions
def test_traceback_handler_show_traceback(
		exception,
		file_regression,
		cli_runner: CliRunner,
		):

	@click.command()
	def demo():

		with handle_tracebacks(True, ConfigTracebackHandler):
			raise exception

	with pytest.raises(type(exception), match=re.escape(str(exception))):
		cli_runner.invoke(demo, catch_exceptions=False)


@pytest.mark.parametrize("exception", [EOFError(), KeyboardInterrupt(), click.Abort()])
def test_handle_tracebacks_ignored_exceptions_click(
		exception,
		cli_runner: CliRunner,
		):

	@click.command()
	def demo():

		with handle_tracebacks(False, ConfigTracebackHandler):
			raise exception

	result: Result = cli_runner.invoke(demo, catch_exceptions=False)

	assert result.stdout.strip() == "Aborted!"
	assert result.exit_code == 1


@pytest.mark.parametrize("exception", [EOFError, KeyboardInterrupt, click.Abort, SystemExit])
def test_handle_tracebacks_ignored_exceptions(exception, ):

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
