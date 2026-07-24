import os
from pathlib import Path

from typer.testing import CliRunner

from pythogen import main, settings


runner = CliRunner()

README_POST_METHOD_PATH = "tests/readme/README-POST.md"
README_DELETE_METHOD_PATH = "tests/readme/README-DELETE.md"
README_PUT_METHOD_PATH = "tests/readme/README-PUT.md"
README_PATCH_METHOD_PATH = "tests/readme/README-PATCH.md"
README_GET_METHOD_PATH = "tests/readme/README-GET.md"
README_HEAD_METHOD_PATH = "tests/readme/README-HEAD.md"

OPENAPI_PATH = "tests/docs/openapi.yaml"
OPENAPI_PATH_POST = "tests/docs/openapi-post-method.yaml"
OPENAPI_PATH_DELETE = "tests/docs/openapi-delete-method.yaml"
OPENAPI_PATH_PUT = "tests/docs/openapi-put-method.yaml"
OPENAPI_PATH_PATCH = "tests/docs/openapi-patch-method.yaml"
OPENAPI_PATH_GET = "tests/docs/openapi-get-method.yaml"
OPENAPI_PATH_HEAD = "tests/docs/openapi-head-method.yaml"

def test_create_readme_file(tmp_path):
    result = runner.invoke(main.app, [OPENAPI_PATH, "--output-path", str(tmp_path)])
    generated_files = os.listdir(settings.WORKING_DIR_PATH / tmp_path)
    expected_file = "README.md"
    assert result.exit_code == 0
    assert expected_file in generated_files

def test_post_method_readme(tmp_path):
    result = runner.invoke(main.app, [OPENAPI_PATH_POST, "--output-path", str(tmp_path), "--name", "Test"])
    readme_file = tmp_path / "README.md"
    expected_file = Path(README_POST_METHOD_PATH)
    assert result.exit_code == 0
    assert readme_file.read_text() == expected_file.read_text()

def test_delete_method_readme(tmp_path):
    result = runner.invoke(main.app, [OPENAPI_PATH_DELETE, "--output-path", str(tmp_path), "--name", "Test"])
    readme_file = tmp_path / "README.md"
    expected_file = Path(README_DELETE_METHOD_PATH)
    assert result.exit_code == 0
    assert readme_file.read_text() == expected_file.read_text()

def test_put_method_readme(tmp_path):
    result = runner.invoke(main.app, [OPENAPI_PATH_PUT, "--output-path", str(tmp_path), "--name", "Test"])
    readme_file = tmp_path / "README.md"
    expected_file = Path(README_PUT_METHOD_PATH)
    assert result.exit_code == 0
    assert readme_file.read_text() == expected_file.read_text()

def test_patch_method_readme(tmp_path):
    result = runner.invoke(main.app, [OPENAPI_PATH_PATCH, "--output-path", str(tmp_path), "--name", "Test"])
    readme_file = tmp_path / "README.md"
    expected_file = Path(README_PATCH_METHOD_PATH)
    assert result.exit_code == 0
    assert readme_file.read_text() == expected_file.read_text()

def test_get_method_readme(tmp_path):
    result = runner.invoke(main.app, [OPENAPI_PATH_GET, "--output-path", str(tmp_path), "--name", "Test"])
    readme_file = tmp_path / "README.md"
    expected_file = Path(README_GET_METHOD_PATH)
    assert result.exit_code == 0
    assert readme_file.read_text() == expected_file.read_text()

def test_head_method_readme(tmp_path):
    result = runner.invoke(main.app, [OPENAPI_PATH_HEAD, "--output-path", str(tmp_path), "--name", "Test"])
    readme_file = tmp_path / "README.md"
    expected_file = Path(README_HEAD_METHOD_PATH)
    assert result.exit_code == 0
    assert readme_file.read_text() == expected_file.read_text()
