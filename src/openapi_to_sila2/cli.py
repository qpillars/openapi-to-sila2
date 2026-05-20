"""Command-line interface for openapi-to-sila2."""

import shutil
import subprocess
import sys
from pathlib import Path

import typer

from openapi_to_sila2 import __version__
from openapi_to_sila2.class_generator import Sila2ClassGenerator
from openapi_to_sila2.fdl_generator import FDLGenerator
from openapi_to_sila2.validation import ValidationLevel, validate_fdl, validate_fdl_dir

app = typer.Typer(
    name="openapi-to-sila2",
    help="Generate SiLA2 Feature Definitions and proxy servers from OpenAPI specifications",
)


def _run_fdl_generation(input_file: Path, output_dir: Path, collect_warnings: bool = False) -> None:
    """Generate SiLA2 FDL XML files from OpenAPI specification."""

    typer.echo(f"📖 Reading OpenAPI specification from: {input_file}")

    generator = FDLGenerator()
    warnings = generator.generate_fdl_from_openapi(str(input_file), str(output_dir), collect_warnings=collect_warnings)

    typer.echo(f"✅ Successfully generated SiLA2 FDL files in: {output_dir}")

    if collect_warnings:
        from openapi_to_sila2.lossy_scan import format_warnings_table

        typer.echo("")
        typer.echo("--- Lossy-construct report ---")
        typer.echo(format_warnings_table(warnings or []))


def _resolve_sila2_codegen() -> str:
    """
    Find the `sila2-codegen` console script, preferring the venv that's
    running us. `shutil.which` already consults the current PATH, but on
    a non-activated venv (e.g. when calling the CLI via its full
    `.venv/bin/openapi-to-sila2` path) PATH does NOT contain the venv
    bin directory and the subprocess fails with `command not found`.
    Resolve via the sibling of `sys.executable` first.
    """

    sibling = Path(sys.executable).parent / "sila2-codegen"
    if sibling.exists():
        return str(sibling)
    on_path = shutil.which("sila2-codegen")
    if on_path:
        return on_path
    return "sila2-codegen"  # let subprocess raise FileNotFoundError downstream


def _run_codegen(output_dir: Path) -> None:
    """Run sila2-codegen on generated FDL files."""

    typer.echo("🔧 Running sila2-codegen on generated FDL files...")

    codegen_bin = _resolve_sila2_codegen()

    try:
        for feature_file in output_dir.glob("*.xml"):
            typer.echo(f"  Processing: {feature_file.name}")

            result = subprocess.run(
                [
                    codegen_bin,
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
    warnings: bool = typer.Option(
        False,
        "--warnings",
        help="Scan the spec for lossy constructs (oneOf/allOf/anyOf, formats, SSE, octet-stream, callbacks, ...) and print a report.",
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

        _run_fdl_generation(input_file, output_dir, collect_warnings=warnings)

        if codegen:
            _run_codegen(output_dir)

        if types:
            if not codegen:
                typer.echo("⚠️  --types requires --codegen flag", err=True)
                raise typer.Exit(code=1)

            _run_type_generation(output_dir)

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
def validate(
    path: Path = typer.Argument(
        ...,
        help="Path to an FDL XML file or a directory containing *.xml feature files",
        exists=True,
    ),
    level: ValidationLevel = typer.Option(
        ValidationLevel.XSD,
        "--level",
        "-l",
        help="Validation thoroughness. xsd is fast schema validation; codegen runs sila2-codegen; full runs both.",
    ),
) -> None:
    """
    Validate FDL feature files against the official SiLA 2 schema (and optionally sila2-codegen).

    Exits non-zero if any file fails validation, with one issue printed per line.
    """

    result = validate_fdl_dir(path, level=level) if path.is_dir() else validate_fdl(path, level=level)

    if result.valid:
        typer.echo(f"✅ FDL validation passed ({level})")
        return

    typer.echo(f"❌ FDL validation failed ({len(result.issues)} issue(s)):", err=True)

    for issue in result.issues:
        location = f"{issue.feature_file}:{issue.line}" if issue.line else issue.feature_file
        typer.echo(f"  [{issue.level}] {location}: {issue.message}", err=True)

    raise typer.Exit(code=1)


@app.command()
def version() -> None:
    """Print the version of openapi-to-sila2."""

    typer.echo(f"openapi-to-sila2 version: {__version__}")


def main() -> None:
    """Entry point for the CLI application."""

    app()


if __name__ == "__main__":
    main()
