# Based on https://github.com/sphinx-doc/sphinx/blob/3.x/sphinx/writers/latex.py
#
# Copyright (c) 2007-2021 by the Sphinx team.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# * Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

# stdlib
from contextlib import suppress
from typing import List

# 3rd party
import sphinx.transforms
from docutils import nodes
from sphinx import addnodes
from sphinx.application import Sphinx
from sphinx.locale import __
from sphinx.util import logging
from sphinx.util.docutils import SphinxDirective
from sphinx.util.nodes import clean_astext
from sphinx.writers.latex import LaTeXTranslator

logger = logging.getLogger(__name__)


def visit_title(self: LaTeXTranslator, node: nodes.title) -> None:
	parent = node.parent
	if isinstance(parent, addnodes.seealso):
		# the environment already handles this
		raise nodes.SkipNode
	elif isinstance(parent, nodes.section):
		if self.this_is_the_title:
			if len(node.children) != 1 and not isinstance(node.children[0], nodes.Text):
				logger.warning(__("document title is not a single Text node"), location=node)
			if not self.elements["title"]:
				# text needs to be escaped since it is inserted into
				# the output literally
				self.elements["title"] = self.escape(node.astext())
			self.this_is_the_title = 0
			raise nodes.SkipNode
		elif not node.get("only-html", False):
			print(node)

			short = ''
			if node.traverse(nodes.image):
				short = ("[%s]" % self.escape(' '.join(clean_astext(node).split())))

			try:
				self.body.append(r'\%s%s{' % (self.sectionnames[self.sectionlevel], short))
			except IndexError:
				# just use "subparagraph", it's not numbered anyway
				self.body.append(r'\%s%s{' % (self.sectionnames[-1], short))
			# breakpoint()
			self.context.append('}\n' + self.hypertarget_to(node.parent))
		else:
			self.body.append("$$POP_TO_HERE$$")
			self.context.append('')
			self.in_title = 0
			return

	elif isinstance(parent, nodes.topic):
		self.body.append(r'\sphinxstyletopictitle{')
		self.context.append('}\n')
	elif isinstance(parent, nodes.sidebar):
		self.body.append(r'\sphinxstylesidebartitle{')
		self.context.append('}\n')
	elif isinstance(parent, nodes.Admonition):
		self.body.append('{')
		self.context.append('}\n')
	elif isinstance(parent, nodes.table):
		# Redirect body output until title is finished.
		self.pushbody([])
	else:
		logger.warning(
				__('encountered title node not in section, topic, table, '
					'admonition or sidebar'), location=node
				)
		self.body.append("\\sphinxstyleothertitle{")
		self.context.append('}\n')
	self.in_title = 1


def depart_title(self: LaTeXTranslator, node: nodes.title) -> None:
	while "$$POP_TO_HERE$$" in self.body:
		self.body.pop()

	self.in_title = 0
	if isinstance(node.parent, nodes.table):
		self.table.caption = self.popbody()
	else:
		self.body.append(self.context.pop())


class HTMLSectionDirective(SphinxDirective):

	def run(self) -> List[nodes.Node]:

		container = nodes.paragraph()
		container["only-html"] = True
		return [container]


class FilterHTMLOnlySections(sphinx.transforms.SphinxTransform):
	"""
	Filter system messages from a doctree.
	"""

	default_priority = 999

	def apply(self, **kwargs) -> None:
		for node in self.document.traverse(nodes.paragraph):
			if node.get("only-html", False):
				for child_node in node.parent.children:
					with suppress(TypeError):
						child_node["only-html"] = True

			node.parent["only-html"] = node.get("only-html", False)
			node["only-html"] = False


def setup(app: Sphinx):
	app.add_directive("html-section", HTMLSectionDirective)
	app.add_transform(FilterHTMLOnlySections)
	app.add_node(nodes.title, override=True, latex=(visit_title, depart_title))
