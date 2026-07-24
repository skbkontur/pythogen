import os
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from pythogen import main, settings


runner = CliRunner()


OPENAPI_TOO_MUCH_ALLOF_PATH = "tests/docs/openapi-with-too-much-allof.yaml"
OPENAPI_PATH = "tests/docs/openapi.yaml"
OPENAPI_PATH_POST = "tests/docs/openapi-post-method.yaml"
OPENAPI_PATH_DELETE = "tests/docs/openapi-delete-method.yaml"
OPENAPI_PATH_HEAD = "tests/docs/openapi-head-method.yaml"
TMP_DIR_PATH = "tests/pythogen/tmp"
ASYNC_CLIENT_PATH = f"{TMP_DIR_PATH}/async_client.py"
ASYNC_CLIENT_PKG_PATH = f"{TMP_DIR_PATH}/async_client_pkg"


@pytest.fixture
def temp_files():
    Path(TMP_DIR_PATH).mkdir(parents=True, exist_ok=True)
    yield
    try:
        Path(ASYNC_CLIENT_PATH).unlink()
    except FileNotFoundError:
        pass

@pytest.mark.usefixtures("temp_files")
def test_entrypoint_gen_http_client() -> None:
    result = runner.invoke(main.app, [OPENAPI_PATH])
    assert result.exit_code == 0

@pytest.mark.usefixtures("temp_files")
def test_entrypoint_gen_http_client_post_method() -> None:
    result = runner.invoke(main.app, [OPENAPI_PATH_POST])
    assert result.exit_code == 0

@pytest.mark.usefixtures("temp_files")
def test_entrypoint_gen_http_client_delete_method() -> None:
    result = runner.invoke(main.app, [OPENAPI_PATH_DELETE])
    assert result.exit_code == 0

@pytest.mark.usefixtures("temp_files")
def test_entrypoint_gen_http_client_head_method() -> None:
    result = runner.invoke(main.app, [OPENAPI_PATH_HEAD])
    assert result.exit_code == 0

@pytest.mark.usefixtures("temp_files")
def test_entrypoint_generates_client_in_src_layout(tmp_path) -> None:
    result = runner.invoke(main.app, [OPENAPI_PATH, "--output-path", str(tmp_path)])
    assert result.exit_code == 0

    assert (tmp_path / "src" / "kontur" / "test" / "__init__.py").exists()
    assert (tmp_path / "src" / "kontur" / "test" / "clients" / "__init__.py").exists()
    assert (tmp_path / "src" / "kontur" / "test" / "models" / "__init__.py").exists()
    assert not (tmp_path / "kontur" / "test" / "__init__.py").exists()


@pytest.mark.usefixtures("temp_files")
def test_entrypoint_gen_http_client_in_shell() -> None:
    process = subprocess.Popen(
        ['python', 'pythogen/main.py', OPENAPI_PATH],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = process.communicate()
    assert b"" in stdout
    assert stdout == b''
    assert stderr == b''


@pytest.mark.usefixtures("temp_files")
def test_entrypoint_gen_http_client_in_shell_with_too_much_allof() -> None:
    process = subprocess.Popen(
        ['python', 'pythogen/main.py', OPENAPI_TOO_MUCH_ALLOF_PATH],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _, stderr = process.communicate()
    assert b"Failed to generate a client" in stderr
    assert b"\"allOf\" field in property can contains only one item" in stderr
