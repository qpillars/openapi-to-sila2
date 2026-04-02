"""Command-line interface for openapi-to-sila2."""

import subprocess
from pathlib import Path

import typer

from openapi_to_sila2 import __version__
from openapi_to_sila2.class_generator import Sila2ClassGenerator
from openapi_to_sila2.fdl_generator import FDLGenerator

app = typer.Typer(
    name="openapi-to-sila2",
    help="Generate SiLA2 Feature Definitions and proxy servers from OpenAPI specifications",
)


def _run_fdl_generation(input_file: Path, output_dir: Path) -> None:
    """Generate SiLA2 FDL XML files from OpenAPI specification."""

    typer.echo(f"📖 Reading OpenAPI specification from: {input_file}")

    generator = FDLGenerator()
    generator.generate_fdl_from_openapi(str(input_file), str(output_dir))

    typer.echo(f"✅ Successfully generated SiLA2 FDL files in: {output_dir}")


def _run_codegen(output_dir: Path) -> None:
    """Run sila2-codegen on generated FDL files."""

    typer.echo("🔧 Running sila2-codegen on generated FDL files...")

    try:
        for feature_file in output_dir.glob("*.xml"):
            typer.echo(f"  Processing: {feature_file.name}")

            result = subprocess.run(
                [
                    "sila2-codegen",
                    "generate-feature-files",
                    "--overwrite",
                    str(feature_file),
                    "-o",
                    str(output_dir),
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                typer.echo(
                    f"❌ Code generation failed for {feature_file.name}:",
                    err=True,
                )

                if result.stdout:
                    typer.echo(f"   stdout: {result.stdout}", err=True)

                if result.stderr:
                    typer.echo(f"   stderr: {result.stderr}", err=True)

                raise typer.Exit(code=2)

        typer.echo("✅ Code generation completed successfully")

    except FileNotFoundError:
        typer.echo(
            "❌ Error: sila2-codegen command not found. Please ensure sila2 is installed.",
            err=True,
        )
        raise typer.Exit(code=1)

    except Exception as e:
        typer.echo("❌ Unexpected error during code generation:", err=True)
        typer.echo(f"   {e}", err=True)
        raise typer.Exit(code=2)


def _run_type_generation(output_dir: Path) -> None:
    """Generate Python type classes from proto files."""

    typer.echo("🐍 Generating Python type classes...")

    try:
        class_generator = Sila2ClassGenerator()

        for feature_folder in output_dir.iterdir():
            if not feature_folder.is_dir():
                continue

            proto_files = list(feature_folder.glob("*.proto"))

            if not proto_files:
                continue

            for proto_file in proto_files:
                typer.echo(f"  Processing: {proto_file.name}")
                class_code = class_generator.generate_classes_from_proto(str(proto_file))
                types_file = feature_folder / "types.py"
                types_file.write_text(class_code, encoding="utf-8")

        typer.echo("✅ Python type generation completed successfully")

    except Exception as e:
        typer.echo("❌ Error during Python type generation:", err=True)
        typer.echo(f"   {e}", err=True)
        raise typer.Exit(code=2)


@app.command()
def generate(
    input_file: Path = typer.Option(
        ...,
        "--input",
        "-i",
        help="Path to the OpenAPI specification file (JSON or YAML)",
        exists=True,
    ),
    output_dir: Path = typer.Option(
        Path("."),
        "--output",
        "-o",
        help="Output directory for generated SiLA2 FDL XML files",
    ),
    codegen: bool = typer.Option(
        False,
        "--codegen",
        help="Also run sila2-codegen on generated FDL files",
    ),
    types: bool = typer.Option(
        False,
        "--types",
        help="Also generate Python type classes (requires --codegen)",
    ),
    feature_prefix: str = typer.Option(
        "",
        "--feature-prefix",
        help="Optional prefix for feature identifiers",
    ),
) -> None:
    """
    Generate SiLA2 Feature Definition Language (FDL) files from an OpenAPI specification.

    This command converts an OpenAPI specification to SiLA2-compliant XML files
    for each tag/feature defined in the API. Optionally runs code generation
    and generates Python type classes.
    """

    try:
        output_dir.mkdir(parents=True, exist_ok=True)

        _run_fdl_generation(input_file, output_dir)

        if codegen:
            _run_codegen(output_dir)

        if types:
            if not codegen:
                typer.echo("⚠️  --types requires --codegen flag", err=True)
                raise typer.Exit(code=1)

            _run_type_generation(output_dir)

        if feature_prefix:
            typer.echo(f"ℹ️  Feature prefix '{feature_prefix}' applied (currently placeholder)")

        typer.echo("📄 Generated files are ready for use with SiLA2 systems")

    except FileNotFoundError as e:
        typer.echo(f"❌ Error: File not found - {e}", err=True)
        raise typer.Exit(code=1)
    except ValueError as e:
        typer.echo(f"❌ Error: Invalid specification - {e}", err=True)
        raise typer.Exit(code=1)
    except PermissionError:
        typer.echo(f"❌ Error: Permission denied writing to {output_dir}", err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"❌ Generation error: {e}", err=True)
        raise typer.Exit(code=2)


@app.command()
def version() -> None:
    """Print the version of openapi-to-sila2."""

    typer.echo(f"openapi-to-sila2 version: {__version__}")


def main() -> None:
    """Entry point for the CLI application."""

    app()


if __name__ == "__main__":
    main()
