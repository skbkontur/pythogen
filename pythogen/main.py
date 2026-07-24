from pathlib import Path

import typer
from openapi_spec_validator import validate
from openapi_spec_validator.readers import read_from_filename

from pythogen import exceptions, settings
from pythogen import packager
from pythogen import renderer
from pythogen.parsers.document import parse_openapi_file


app = typer.Typer(pretty_exceptions_enable=False)

EXIT_CODE_GENERATION_ERROR = 2

@app.command()
def main(
    input: str = typer.Argument(..., help="input OpenAPI file path"),
    name: str = typer.Option("Client", help="client class name"),
    package_name: str = typer.Option("kontur.test", help="package path"),
    doc_link: str = typer.Option(help="doc link"),
    base_url: str = typer.Option(help="base url"),
    repo_url: str = typer.Option(help="repo url"),
    author_name: str = typer.Option(help="author name"),
    author_email: str = typer.Option(help="author email"),
    line_length: int = typer.Option(default=119, help="Set the line-length"),
    ignore_unknown_format: bool = typer.Option(default=False, help="Ignore unknown type format"),
    output_path: str = typer.Option(default=None, help="output path"),
):
    """
    Generate HTTP clients for python from OpenAPI
    """
    if not output_path:
        output_path = settings.CLIENT_OUTPUT_PATH or settings.WORKING_DIR_PATH / package_name.replace(".", "_")
    else:
        output_path = settings.WORKING_DIR_PATH / Path(output_path)
    spec_dict, _ = read_from_filename(input)
    validate(spec_dict)

    try:
        document = parse_openapi_file(input, ignore_unknown_format)

    except exceptions.Exit:
        raise typer.Exit(code=EXIT_CODE_GENERATION_ERROR)

    packager.init_package(
        package_name=package_name,
        output_path=output_path,
        client_name=name,
        doc_link=doc_link,
        base_url=base_url,
        repo_url=repo_url,
        author_name=author_name,
        author_email=author_email,
        document=document,
        line_length=line_length,
    )

    renderer.render_client(
        document=document,
        name=name,
        package_name=package_name,
        output_path=output_path,
        line_length=line_length,
    )


# Used in pytroject.toml -> [tool.poetry.scripts]
def run() -> None:
    typer.run(main)  # pragma: no cover


if __name__ == "__main__":
    app()
