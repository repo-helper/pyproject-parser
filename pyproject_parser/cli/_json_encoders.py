#!/usr/bin/env python3
#
#  _json_encoders.py
"""
Encoder functions for :mod:`sdjson`.
"""
#
#  Copyright © 2022 Dominic Davis-Foster <dominic@davis-foster.co.uk>
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
from pathlib import PurePath
from typing import Dict, Union

# 3rd party
import sdjson  # nodep
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import Version
from shippinglabel.requirements import ComparableRequirement

# this package
from pyproject_parser import PyProject
from pyproject_parser.classes import License, Readme
from pyproject_parser.type_hints import ReadmeDict


@sdjson.register_encoder(ComparableRequirement)
@sdjson.register_encoder(Requirement)
@sdjson.register_encoder(Version)
@sdjson.register_encoder(SpecifierSet)
def _encode_from_packaging(obj: Union[ComparableRequirement, Requirement, Version, SpecifierSet]) -> str:
	return str(obj)


@sdjson.register_encoder(PurePath)
def _encode_pathlib(obj: PurePath) -> str:
	return obj.as_posix()


@sdjson.register_encoder(PyProject)
def _encode_pyproject(obj: PyProject) -> Dict:
	return {
			"build-system": obj.build_system,
			"project": obj.project,
			"tool": obj.tool,
			}


@sdjson.register_encoder(Readme)
@sdjson.register_encoder(License)
def _encode_readme_license(obj: Union[Readme, License]) -> Union[ReadmeDict, Dict[str, str]]:
	return obj.to_dict()
