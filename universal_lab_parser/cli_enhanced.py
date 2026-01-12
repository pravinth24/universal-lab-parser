"""Enhanced CLI with better UX, progress bars, and colors."""

import click
import sys
from pathlib import Path
from typing import Optional
from tqdm import tqdm
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint

from universal_lab_parser import __version__, parse_file
from universal_lab_parser.parsers import list_parsers
from universal_lab_parser.utils.logger import setup_logger, get_logger
from universal_lab_parser.core.exceptions import UniversalLabParserError

console = Console()
logger = get_logger(__name__)


@click.group()
@click.version_option(version=__version__)
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--quiet', '-q', is_flag=True, help='Suppress all output except errors')
@click.option('--log-file', type=click.Path(), help='Write logs to file')
@click.pass_context
def main(ctx, verbose, quiet, log_file):
    """Universal Lab Parser - Parse proprietary lab instrument data.

    \b
    Examples:
      ulp parse sample.arw
      ulp parse sample.arw --format json --output results.json
      ulp batch ./data/ --pattern "*.arw"
      ulp formats
    """
    # Store options in context
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['quiet'] = quiet

    # Configure logging
    import logging
    level = logging.DEBUG if verbose else (logging.ERROR if quiet else logging.INFO)
    setup_logger(level=level, log_file=Path(log_file) if log_file else None)


@main.command()
@click.argument('filepath', type=click.Path(exists=True))
@click.option(
    '--format', '-f',
    type=click.Choice(['csv', 'json', 'parquet'], case_sensitive=False),
    default='csv',
    help='Output format'
)
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.option('--parser', '-p', type=str, help='Force specific parser')
@click.option('--auto-detect/--no-auto-detect', default=True)
@click.option('--show-metadata', is_flag=True, help='Display metadata after parsing')
@click.pass_context
def parse(ctx, filepath, format, output, parser, auto_detect, show_metadata):
    """Parse a single instrument data file with enhanced output."""

    try:
        # Show parsing progress
        with console.status(f"[bold green]Parsing {Path(filepath).name}...") as status:
            parser_type = None if auto_detect else parser
            data = parse_file(filepath, parser_type=parser_type)

            # Generate output filename if not provided
            if output is None:
                input_path = Path(filepath)
                output = str(input_path.with_suffix(f'.{format}'))

            # Export to requested format
            status.update(f"[bold blue]Exporting to {format.upper()}...")
            if format == 'csv':
                data.to_csv(output)
            elif format == 'json':
                data.to_json(output)
            elif format == 'parquet':
                data.to_parquet(output)

        # Success message
        console.print(f"✓ [bold green]Successfully parsed to {output}[/bold green]")

        # Show metadata if requested
        if show_metadata or ctx.obj.get('verbose'):
            display_metadata_table(data)
        else:
            # Quick summary
            console.print(f"  Sample: [cyan]{data.metadata.sample_name}[/cyan]")
            console.print(f"  Instrument: [cyan]{data.metadata.instrument_model}[/cyan]")
            if data.peaks:
                console.print(f"  Peaks detected: [yellow]{len(data.peaks)}[/yellow]")

    except FileNotFoundError:
        console.print(f"[bold red]✗ Error: File not found: {filepath}[/bold red]")
        sys.exit(1)
    except UniversalLabParserError as e:
        console.print(f"[bold red]✗ Parse Error: {e}[/bold red]")
        logger.error(f"Parsing failed: {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]✗ Unexpected Error: {e}[/bold red]")
        logger.exception("Unexpected error during parsing")
        sys.exit(1)


@main.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False))
@click.option('--pattern', default='*', help='File pattern to match (e.g., *.arw)')
@click.option(
    '--format', '-f',
    type=click.Choice(['csv', 'json', 'parquet'], case_sensitive=False),
    default='csv'
)
@click.option('--output-dir', '-o', type=click.Path(), help='Output directory')
@click.option('--parallel', '-j', type=int, default=1, help='Number of parallel workers')
@click.option('--fail-fast', is_flag=True, help='Stop on first error')
@click.pass_context
def batch(ctx, directory, pattern, format, output_dir, parallel, fail_fast):
    """Batch parse all files in a directory with progress bars."""

    import glob
    from concurrent.futures import ThreadPoolExecutor, as_completed

    # Create output directory
    if output_dir is None:
        output_dir = Path('./parsed')
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)

    # Find all matching files
    directory_path = Path(directory)
    files = list(glob.glob(str(directory_path / pattern)))

    if not files:
        console.print(f"[yellow]No files found matching pattern '{pattern}'[/yellow]")
        return

    console.print(f"[bold]Found {len(files)} files to parse[/bold]\n")

    # Parse with progress bar
    success_count = 0
    error_count = 0
    errors = []

    def parse_single_file(filepath):
        """Parse a single file and return result."""
        try:
            data = parse_file(filepath)
            input_name = Path(filepath).stem
            output_path = output_dir / f"{input_name}.{format}"

            if format == 'csv':
                data.to_csv(str(output_path))
            elif format == 'json':
                data.to_json(str(output_path))
            elif format == 'parquet':
                data.to_parquet(str(output_path))

            return {'success': True, 'file': filepath, 'output': output_path}
        except Exception as e:
            return {'success': False, 'file': filepath, 'error': str(e)}

    # Process files with progress bar
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:

        if parallel > 1:
            # Parallel processing
            task = progress.add_task(f"[cyan]Processing {len(files)} files...", total=len(files))

            with ThreadPoolExecutor(max_workers=parallel) as executor:
                futures = {executor.submit(parse_single_file, f): f for f in files}

                for future in as_completed(futures):
                    result = future.result()
                    progress.advance(task)

                    if result['success']:
                        success_count += 1
                        console.print(f"  ✓ [green]{Path(result['file']).name}[/green]")
                    else:
                        error_count += 1
                        errors.append(result)
                        console.print(f"  ✗ [red]{Path(result['file']).name}: {result['error']}[/red]")

                        if fail_fast:
                            executor.shutdown(wait=False, cancel_futures=True)
                            break
        else:
            # Serial processing with detailed progress
            for filepath in tqdm(files, desc="Parsing files", unit="file"):
                result = parse_single_file(filepath)

                if result['success']:
                    success_count += 1
                    if ctx.obj.get('verbose'):
                        console.print(f"  ✓ [green]{Path(result['file']).name} -> {result['output']}[/green]")
                else:
                    error_count += 1
                    errors.append(result)
                    console.print(f"  ✗ [red]{Path(result['file']).name}: {result['error']}[/red]")

                    if fail_fast:
                        break

    # Summary
    console.print()
    console.print(f"[bold]Batch Processing Complete[/bold]")
    console.print(f"  Success: [green]{success_count}[/green]")
    console.print(f"  Errors: [red]{error_count}[/red]")
    console.print(f"  Output: [cyan]{output_dir}[/cyan]")

    # Show errors if any
    if errors and not ctx.obj.get('quiet'):
        console.print("\n[bold red]Errors:[/bold red]")
        for error in errors[:5]:  # Show first 5 errors
            console.print(f"  • {Path(error['file']).name}: {error['error']}")
        if len(errors) > 5:
            console.print(f"  ... and {len(errors) - 5} more errors")


@main.command()
def formats():
    """List supported instrument formats with rich table."""

    parsers = list_parsers()

    # Create rich table
    table = Table(title="Supported Instrument Formats", show_header=True, header_style="bold magenta")
    table.add_column("Parser", style="cyan", width=15)
    table.add_column("Vendor", style="green", width=20)
    table.add_column("Status", style="yellow", width=20)
    table.add_column("Extensions", style="blue")

    parser_info = {
        "waters": ("Waters", "🚧 In Progress", ".arw, .raw"),
        "agilent": ("Agilent", "📋 Planned", ".d, .ch"),
        "thermo": ("Thermo Fisher", "📋 Planned", ".raw"),
    }

    for parser_name in parsers:
        vendor, status, extensions = parser_info.get(parser_name, ("Unknown", "Unknown", ""))
        table.add_row(parser_name, vendor, status, extensions)

    console.print(table)
    console.print("\n[bold]Request a new format:[/bold]")
    console.print("  https://github.com/pravinth24/universal-lab-parser/issues")


@main.command()
@click.argument('filepath', type=click.Path(exists=True))
def info(filepath):
    """Show detailed information about a file."""

    from universal_lab_parser.utils.file_detection import detect_file_type

    filepath = Path(filepath)

    console.print(f"[bold]File Information:[/bold] {filepath.name}\n")

    # File stats
    console.print(f"  Size: [cyan]{filepath.stat().st_size / 1024:.2f} KB[/cyan]")
    console.print(f"  Extension: [cyan]{filepath.suffix}[/cyan]")

    # Detect format
    file_type = detect_file_type(str(filepath))

    if file_type:
        console.print(f"  Detected format: [green]{file_type}[/green] ✓")
        console.print(f"\n[green]✓ This file can be parsed with:[/green]")
        console.print(f"  ulp parse {filepath}")
    else:
        console.print(f"  Detected format: [red]Unknown[/red] ✗")
        console.print(f"\n[yellow]Format not recognized. Supported formats:[/yellow]")
        for parser in list_parsers():
            console.print(f"  - {parser}")


def display_metadata_table(data):
    """Display metadata in a nice table."""
    table = Table(title="Metadata", show_header=True, header_style="bold cyan")
    table.add_column("Field", style="yellow")
    table.add_column("Value", style="green")

    metadata = data.metadata
    fields = [
        ("Sample", metadata.sample_name),
        ("Instrument", metadata.instrument_model),
        ("Serial", metadata.instrument_serial),
        ("Method", metadata.method_name),
        ("Operator", metadata.operator),
        ("Run Date", metadata.run_date),
        ("Runtime", f"{metadata.runtime_minutes} min" if metadata.runtime_minutes else None),
        ("Injection Volume", f"{metadata.injection_volume} {metadata.injection_volume_units}" if metadata.injection_volume else None),
    ]

    for field, value in fields:
        if value:
            table.add_row(field, str(value))

    console.print(table)


if __name__ == '__main__':
    main(obj={})
