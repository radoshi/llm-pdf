from pathlib import Path

from llmpdf.main import expand_globs


def test_expand_globs(tmp_path: Path):
    # Create a temporary directory for the first test case
    temp_dir1 = tmp_path / "Desktop"
    temp_dir1.mkdir()
    # Create some dummy PDF files
    for i in range(3):
        (temp_dir1 / f"file{i}.pdf").touch()

    files = expand_globs([str(temp_dir1 / "*.pdf")])
    assert all(Path(f).exists() for f in files)
    assert all(Path(f).is_file() for f in files)
    assert all(Path(f).name.endswith(".pdf") for f in files)

    # For the second test case, use a non-existent directory
    non_existent_dir = "/path/that/does/not/exist"
    files = expand_globs([f"{non_existent_dir}/*.pdf"])
    assert not files
