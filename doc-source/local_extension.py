# 3rd party
from docutils import nodes
from sphinx.util.docutils import SphinxDirective


def configure(app, doctree):
	if app.builder.name.lower() == "html":
		app.config.toctree_plus_types.add("method")
		app.config.toctree_plus_types.add("attribute")


class Space(SphinxDirective):

	def run(self):
		# TODO: other builders
		return [
				nodes.raw('', "\n\\vspace{10px}\n", format="latex"),
				nodes.raw('', "\n</br>\n", format="html"),  # nodes.line_block('', nodes.line())
				]


def setup(app):
	app.connect("doctree-read", configure)
	app.add_directive("space", Space)
