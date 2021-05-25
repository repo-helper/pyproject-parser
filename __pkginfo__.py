#  This file is managed by 'repo_helper'. Don't edit it directly.
#  Copyright © 2020 Dominic Davis-Foster <dominic@davis-foster.co.uk>
#
#  This file is distributed under the same license terms as the program it came with.
#  There will probably be a file called LICEN[S/C]E in the same directory as this file.
#
#  In any case, this program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# This script based on https://github.com/rocky/python-uncompyle6/blob/master/__pkginfo__.py
#

__all__ = [
		"__version__",
		"extras_require",
		]

__version__ = "0.2.3"
extras_require = {
		"readme": ["docutils==0.16", "readme-renderer[md]>=27.0"],
		"cli": ["click>=7.1.2", "consolekit>=1.1.2"],
		"all": ["click>=7.1.2", "consolekit>=1.1.2", "docutils==0.16", "readme-renderer[md]>=27.0"]
		}
