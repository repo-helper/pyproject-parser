#!/usr/bin/env python3
#
#  __init__.py
"""
Type hints for :mod:`pyproject_parer`.
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
from typing import Dict, List, Optional

# 3rd party
from packaging.markers import Marker
from packaging.version import Version
from shippinglabel.requirements import ComparableRequirement
from typing_extensions import Literal, TypedDict

__all__ = ["BuildSystemDict", "Dynamic", "ProjectDict", "Author"]

BuildSystemDict = TypedDict(
		"BuildSystemDict",
		{
				"requires": List[ComparableRequirement],
				"build-backend": Optional[str],
				"backend-path": Optional[List[str]]
				}
		)

Dynamic = Literal[
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
	"optional-dependencies"
	]

ProjectDict = TypedDict(
		"ProjectDict",
		{
				"name": str,
				"version": Optional[Version],
				"description": Optional[str],
				"readme": Optional[Dict[str, str]],
				"requires-python": Optional[Marker],
				"license": Optional[str],
				"authors": List["Author"],
				"maintainers": List["Author"],
				"keywords": List[str],
				"classifiers": List[str],
				"urls": Dict[str, str],
				"scripts": Dict[str, str],
				"gui-scripts": Dict[str, str],
				"entry-points": Dict[str, Dict[str, str]],
				"dependencies": List[ComparableRequirement],
				"optional-dependencies": Dict[str, List[ComparableRequirement]],
				"dynamic": List[Dynamic],
				}
		)


class Author(TypedDict, total=False):
	name: Optional[str]
	email: Optional[str]
