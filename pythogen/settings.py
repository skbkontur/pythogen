import os
from pathlib import Path


CLIENT_TEMPLATE_NAME = "main.j2"

CURRENT_DIR_PATH = Path(__file__).parent.absolute()
WORKING_DIR_PATH = Path(os.getcwd())
HTTP_CLIENT_TEMPLATES_DIR_PATH = CURRENT_DIR_PATH / Path("templates/http_toolkit_client")
HTTP_PACKAGE_TEMPLATES_DIR_PATH = CURRENT_DIR_PATH / Path("templates/http_client_package")

CLIENT_OUTPUT_PATH = os.environ.get("CLIENT_OUTPUT_PATH", None)
