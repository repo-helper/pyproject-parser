# 3rd party
import pytest
from domdf_python_tools.paths import PathPlus

# this package
from pyproject_parser import License, Readme


class TestReadme:

	def test_no_test_or_file(self):
		with pytest.raises(TypeError, match="At least one of 'text' and 'file' must be supplied to .*"):
			Readme()

		with pytest.raises(TypeError, match="At least one of 'text' and 'file' must be supplied to .*"):
			Readme(charset="UTF-8")

	def test_content_type_sole_arg(self):

		match = "'content_type' cannot be provided on its own; please provide either 'text' or 'file' or use the 'from_file' method."

		with pytest.raises(ValueError, match=match):
			Readme(content_type="text/x-rst")

	def test_invalid_content_types(self):
		with pytest.raises(ValueError, match="Unsupported readme content-type 'application/json'"):
			Readme(text="This is the readme", content_type="application/json")  # type: ignore[arg-type]

		with pytest.raises(ValueError, match="Unsupported readme content-type 'image/jpeg'"):
			Readme(file="photo.jpg", content_type="image/jpeg")  # type: ignore[arg-type]

	def test_from_file(self, tmp_pathplus: PathPlus):
		(tmp_pathplus / "README.rst").write_clean("This is the README")

		readme = Readme.from_file(tmp_pathplus / "README.rst")
		assert readme.file == tmp_pathplus / "README.rst"
		assert readme.content_type == "text/x-rst"
		assert readme.text is None

		readme.resolve(inplace=True)
		assert readme.file == tmp_pathplus / "README.rst"
		assert readme.content_type == "text/x-rst"
		assert readme.text == "This is the README\n"

		(tmp_pathplus / "README.txt").write_clean("This is the README")

		readme = Readme.from_file(tmp_pathplus / "README.txt")
		assert readme.file == tmp_pathplus / "README.txt"
		assert readme.content_type == "text/plain"
		assert readme.text is None

		readme.resolve(inplace=True)
		assert readme.file == tmp_pathplus / "README.txt"
		assert readme.content_type == "text/plain"
		assert readme.text == "This is the README\n"

	def test_from_file_bad_filetype(self, tmp_pathplus: PathPlus):
		with pytest.raises(ValueError, match="Unrecognised filetype for '.*README'"):
			Readme.from_file(tmp_pathplus / "README")
		with pytest.raises(ValueError, match="Unrecognised filetype for '.*README.rtf'"):
			Readme.from_file(tmp_pathplus / "README.rtf")
		with pytest.raises(ValueError, match="Unrecognised filetype for '.*README.doc'"):
			Readme.from_file(tmp_pathplus / "README.doc")

	def test_from_file_charset(self, tmp_pathplus: PathPlus):
		(tmp_pathplus / "README.md").write_clean("This is the README", encoding="cp1252")

		readme = Readme.from_file(tmp_pathplus / "README.md", charset="cp1252")
		assert readme.file == tmp_pathplus / "README.md"
		assert readme.content_type == "text/markdown"
		assert readme.text is None

		readme.resolve(inplace=True)
		assert readme.file == tmp_pathplus / "README.md"
		assert readme.content_type == "text/markdown"
		assert readme.text == "This is the README\n"

	def test_resolve(self, tmp_pathplus: PathPlus):
		(tmp_pathplus / "README.txt").write_clean("This is the README")

		readme = Readme(file=tmp_pathplus / "README.txt", content_type="text/plain")
		assert readme.file == tmp_pathplus / "README.txt"
		assert readme.content_type == "text/plain"
		assert readme.text is None

		resolved_readme = readme.resolve()
		assert readme is not resolved_readme

		assert resolved_readme.file == tmp_pathplus / "README.txt"
		assert resolved_readme.content_type == "text/plain"
		assert resolved_readme.text == "This is the README\n"

	def test_resolve_inplace(self, tmp_pathplus: PathPlus):
		(tmp_pathplus / "README.txt").write_clean("This is the README")

		readme = Readme(file=tmp_pathplus / "README.txt", content_type="text/plain")
		assert readme.file == tmp_pathplus / "README.txt"
		assert readme.content_type == "text/plain"
		assert readme.text is None

		resolved_readme = readme.resolve(inplace=True)
		assert readme is resolved_readme

		assert readme.file == tmp_pathplus / "README.txt"
		assert readme.content_type == "text/plain"
		assert readme.text == "This is the README\n"

		assert resolved_readme.file == tmp_pathplus / "README.txt"
		assert resolved_readme.content_type == "text/plain"
		assert resolved_readme.text == "This is the README\n"

	def test_to_dict(self, tmp_pathplus: PathPlus):
		(tmp_pathplus / "README.rst").write_clean("This is the README")

		readme = Readme(file=tmp_pathplus / "README.rst", content_type="text/x-rst")

		assert readme.to_dict() == {
				"file": f"{tmp_pathplus.as_posix()}/README.rst",
				"content_type": "text/x-rst",
				}
		assert Readme.from_dict(readme.to_dict()) == readme
		assert Readme(**readme.to_dict()) == readme

		(tmp_pathplus / "README.rst").write_clean("This is the README", encoding="cp1252")

		readme = Readme(file=tmp_pathplus / "README.rst", content_type="text/x-rst", charset="cp1252")

		assert readme.to_dict() == {
				"file": f"{tmp_pathplus.as_posix()}/README.rst",
				"content_type": "text/x-rst",
				"charset": "cp1252",
				}
		assert Readme.from_dict(readme.to_dict()) == readme
		assert Readme(**readme.to_dict()) == readme

		readme = Readme(text="This is the README", content_type="text/x-rst")

		assert readme.to_dict() == {
				"text": "This is the README",
				"content_type": "text/x-rst",
				}
		assert Readme.from_dict(readme.to_dict()) == readme
		assert Readme(**readme.to_dict()) == readme

	def test_to_pep621_dict(self, tmp_pathplus: PathPlus):
		(tmp_pathplus / "README.rst").write_clean("This is the README")

		readme = Readme(file=tmp_pathplus / "README.rst", content_type="text/x-rst")

		assert readme.to_pep621_dict() == {
				"file": f"{tmp_pathplus.as_posix()}/README.rst",
				}

		# TODO: the type ignore needs the TypedDict function fix in typing-extensions
		assert Readme.from_dict(readme.to_pep621_dict()) == readme  # type: ignore[arg-type]

		(tmp_pathplus / "README.md").write_clean("This is the README")

		readme = Readme(file=tmp_pathplus / "README.md", content_type="text/x-rst")

		assert readme.to_pep621_dict() == {
				"file": f"{tmp_pathplus.as_posix()}/README.md",
				"content-type": "text/x-rst",
				}

		# TODO: the type ignore needs the TypedDict function fix in typing-extensions
		assert Readme.from_dict(readme.to_pep621_dict()) == readme  # type: ignore[arg-type]

		(tmp_pathplus / "README.rst").write_clean("This is the README", encoding="cp1252")

		readme = Readme(file=tmp_pathplus / "README.rst", content_type="text/x-rst", charset="cp1252")

		assert readme.to_pep621_dict() == {
				"file": f"{tmp_pathplus.as_posix()}/README.rst",
				"charset": "cp1252",
				}

		# TODO: the type ignore needs the TypedDict function fix in typing-extensions
		assert Readme.from_dict(readme.to_pep621_dict()) == readme  # type: ignore[arg-type]

		readme = Readme(text="This is the README", content_type="text/x-rst")

		assert readme.to_pep621_dict() == {
				"text": "This is the README",
				"content-type": "text/x-rst",
				}

		# TODO: the type ignore needs the TypedDict function fix in typing-extensions
		assert Readme.from_dict(readme.to_pep621_dict()) == readme  # type: ignore[arg-type]


class TestLicense:

	def test_no_test_or_file(self):
		with pytest.raises(TypeError, match="At least one of 'text' and 'file' must be supplied to .*"):
			License()

	def test_resolve(self, tmp_pathplus: PathPlus):
		(tmp_pathplus / "LICENSE.txt").write_clean("This is the LICENSE")

		lic = License(file=tmp_pathplus / "LICENSE.txt")
		assert lic.file == tmp_pathplus / "LICENSE.txt"
		assert lic.text is None

		resolved_lic = lic.resolve()
		assert lic is not resolved_lic

		assert resolved_lic.file == tmp_pathplus / "LICENSE.txt"
		assert resolved_lic.text == "This is the LICENSE\n"

	def test_resolve_inplace(self, tmp_pathplus: PathPlus):
		(tmp_pathplus / "LICENSE.txt").write_clean("This is the LICENSE")

		lic = License(file=tmp_pathplus / "LICENSE.txt")
		assert lic.file == tmp_pathplus / "LICENSE.txt"
		assert lic.text is None

		resolved_lic = lic.resolve(inplace=True)
		assert lic is resolved_lic

		assert lic.file == tmp_pathplus / "LICENSE.txt"
		assert lic.text == "This is the LICENSE\n"

		assert resolved_lic.file == tmp_pathplus / "LICENSE.txt"
		assert resolved_lic.text == "This is the LICENSE\n"

	def test_to_dict(self, tmp_pathplus: PathPlus):
		(tmp_pathplus / "LICENSE.rst").write_clean("This is the LICENSE")

		lic = License(file=tmp_pathplus / "LICENSE.rst")

		assert lic.to_dict() == {"file": f"{tmp_pathplus.as_posix()}/LICENSE.rst"}
		assert License.from_dict(lic.to_dict()) == lic
		assert License(**lic.to_dict()) == lic

		(tmp_pathplus / "LICENSE.rst").write_clean("This is the LICENSE", encoding="cp1252")

		lic = License(file=tmp_pathplus / "LICENSE.rst")

		assert lic.to_dict() == {"file": f"{tmp_pathplus.as_posix()}/LICENSE.rst"}
		assert License.from_dict(lic.to_dict()) == lic
		assert License(**lic.to_dict()) == lic

		lic = License(text="This is the LICENSE")

		assert lic.to_dict() == {"text": "This is the LICENSE"}
		assert License.from_dict(lic.to_dict()) == lic
		assert License(**lic.to_dict()) == lic

	def test_to_pep621_dict(self, tmp_pathplus: PathPlus):
		(tmp_pathplus / "LICENSE.rst").write_clean("This is the LICENSE")

		lic = License(file=tmp_pathplus / "LICENSE.rst")

		assert lic.to_pep621_dict() == {"file": f"{tmp_pathplus.as_posix()}/LICENSE.rst"}
		assert License.from_dict(lic.to_pep621_dict()) == lic

		(tmp_pathplus / "LICENSE.md").write_clean("This is the LICENSE")

		lic = License(file=tmp_pathplus / "LICENSE.md")

		assert lic.to_pep621_dict() == {"file": f"{tmp_pathplus.as_posix()}/LICENSE.md"}
		assert License.from_dict(lic.to_pep621_dict()) == lic

		(tmp_pathplus / "LICENSE.rst").write_clean("This is the LICENSE", encoding="cp1252")

		lic = License(file=tmp_pathplus / "LICENSE.rst")

		assert lic.to_pep621_dict() == {"file": f"{tmp_pathplus.as_posix()}/LICENSE.rst"}
		assert License.from_dict(lic.to_pep621_dict()) == lic

		lic = License(text="This is the LICENSE")

		assert lic.to_pep621_dict() == {"text": "This is the LICENSE"}
		assert License.from_dict(lic.to_pep621_dict()) == lic

		(tmp_pathplus / "LICENSE").write_clean("This is the LICENSE")
		lic = License(text="This is the LICENSE\n", file=tmp_pathplus / "LICENSE")

		assert lic.to_pep621_dict() == {"file": (tmp_pathplus / "LICENSE").as_posix()}
		assert License.from_dict(lic.to_pep621_dict()).resolve() == lic
