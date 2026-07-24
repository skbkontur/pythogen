import os
import sys
from pathlib import Path

import pytest

from jinja2 import Environment, FileSystemLoader
from pythogen import models
from pythogen.packager import mock_response_repr, query_params_repr, path_params_repr, headers_repr, body_repr, \
    j2_assertions, url_repr, match_headers_repr, match_content_repr
from pythogen.renderer import classname, j2_typerepr, j2_responserepr, iterresponsemap, propertyfield, \
    j2_repr_any_of, varname, parameterfield, docstring_lines, wrap_lines

dir_name = os.path.dirname(os.path.abspath(__file__))
# sys.path.insert(0, dir_name + '/../')
sys.path.insert(0, dir_name)


LIBFIXTURES = ()

pytest.register_assert_rewrite(*LIBFIXTURES)
pytest_plugins = (
    # Our own plugins
    *LIBFIXTURES,
    # Third party plugins
)

@pytest.fixture(scope="module", autouse=True)
def responses_model_generation_template():
    template_dir_path = Path(__file__).parent.parent.absolute() / Path(
    "pythogen/templates/http_toolkit_client")

    method_template_name = "models/responses.py.j2"

    globals = {
        "classname": classname,
        "typerepr": j2_typerepr,
        "responserepr": j2_responserepr,
        "iterresponsemap": iterresponsemap,
        "mock_response_repr": mock_response_repr,
        "query_params_repr": query_params_repr,
        "path_params_repr": path_params_repr,
        "headers_repr": headers_repr,
        "body_repr": body_repr,
        "assertions": j2_assertions,
        "url_repr": url_repr,
        "match_headers_repr": match_headers_repr,
        "match_content_repr": match_content_repr,
        "docstring_lines": docstring_lines,
        "wrap_lines": wrap_lines,
        "line_length": 119,
        "propertyfield": propertyfield,
        "repranyof": j2_repr_any_of,
        "Type": models.Type
    }

    assert (template_dir_path / method_template_name).exists()
    env = Environment(loader=FileSystemLoader(template_dir_path), extensions=["jinja2.ext.loopcontrols"])
    template = env.get_template(
        method_template_name,
        globals=globals,
    )
    return template

@pytest.fixture(scope="module", autouse=True)
def requests_model_generation_template():
    template_dir_path = Path(__file__).parent.parent.absolute() / Path(
    "pythogen/templates/http_toolkit_client")

    method_template_name = "models/requests.py.j2"

    globals = {
        "classname": classname,
        "typerepr": j2_typerepr,
        "responserepr": j2_responserepr,
        "iterresponsemap": iterresponsemap,
        "mock_response_repr": mock_response_repr,
        "query_params_repr": query_params_repr,
        "path_params_repr": path_params_repr,
        "headers_repr": headers_repr,
        "body_repr": body_repr,
        "assertions": j2_assertions,
        "url_repr": url_repr,
        "match_headers_repr": match_headers_repr,
        "match_content_repr": match_content_repr,
        "docstring_lines": docstring_lines,
        "wrap_lines": wrap_lines,
        "line_length": 119,
        "propertyfield": propertyfield,
        "repranyof": j2_repr_any_of,
        "Type": models.Type,
        "varname": varname,
        "parameterfield": parameterfield,
    }

    assert (template_dir_path / method_template_name).exists()
    env = Environment(loader=FileSystemLoader(template_dir_path), extensions=["jinja2.ext.loopcontrols"])
    template = env.get_template(
        method_template_name,
        globals=globals,
    )
    return template
