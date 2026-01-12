"""Command-line interface for Universal Lab Parser."""

import click
from pathlib import Path
from universal_lab_parser import __version__, parse_file, batch_parse
from universal_lab_parser.parsers import list_parsers


@click.group()
@click.version_option(version=__version__)
def main():
    """Universal Lab Parser - Parse proprietary lab instrument data."""
    pass


@main.command()
@click.argument('filepath', type=click.Path(exists=True))
@click.option(
    '--format', '-f',
    type=click.Choice(['csv', 'json', 'parquet'], case_sensitive=False),
    default='csv',
    help='Output format (default: csv)'
)
@click.option(
    '--output', '-o',
    type=click.Path(),
    help='Output file path (default: auto-generated)'
)
@click.option(
    '--parser', '-p',
    type=str,
    help='Force specific parser (waters, agilent, thermo)'
)
@click.option(
    '--auto-detect/--no-auto-detect',
    default=True,
    help='Auto-detect instrument type (default: True)'
)
def parse(filepath, format, output, parser, auto_detect):
    """Parse a single instrument data file."""
    try:
        click.echo(f"Parsing {filepath}...")

        # Parse the file
        parser_type = None if auto_detect else parser
        data = parse_file(filepath, parser_type=parser_type)

        # Generate output filename if not provided
        if output is None:
            input_path = Path(filepath)
            output = str(input_path.with_suffix(f'.{format}'))

        # Export to requested format
        if format == 'csv':
            data.to_csv(output)
        elif format == 'json':
            data.to_json(output)
        elif format == 'parquet':
            data.to_parquet(output)

        click.echo(f"✓ Successfully parsed to {output}")
        click.echo(f"  Sample: {data.metadata.sample_name}")
        click.echo(f"  Instrument: {data.metadata.instrument_model}")
        click.echo(f"  Peaks detected: {len(data.peaks)}")

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


@main.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False))
@click.option(
    '--pattern',
    default='*',
    help='File pattern to match (default: *)'
)
@click.option(
    '--format', '-f',
    type=click.Choice(['csv', 'json', 'parquet'], case_sensitive=False),
    default='csv',
    help='Output format (default: csv)'
)
@click.option(
    '--output-dir', '-o',
    type=click.Path(),
    help='Output directory (default: ./parsed/)'
)
def batch(directory, pattern, format, output_dir):
    """Batch parse all files in a directory."""
    try:
        click.echo(f"Batch parsing {directory} with pattern '{pattern}'...")

        # Create output directory
        if output_dir is None:
            output_dir = Path('./parsed')
        else:
            output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True, parents=True)

        # Parse all files
        results = batch_parse(directory, pattern=pattern)

        if not results:
            click.echo(f"No files found matching pattern '{pattern}'")
            return

        click.echo(f"Found {len(results)} files to parse...")

        # Export each result
        for data in results:
            input_name = Path(data.source_file).stem
            output_path = output_dir / f"{input_name}.{format}"

            if format == 'csv':
                data.to_csv(str(output_path))
            elif format == 'json':
                data.to_json(str(output_path))
            elif format == 'parquet':
                data.to_parquet(str(output_path))

            click.echo(f"  ✓ {input_name} -> {output_path}")

        click.echo(f"\n✓ Successfully parsed {len(results)} files to {output_dir}")

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


@main.command()
def formats():
    """List supported instrument formats."""
    parsers = list_parsers()

    click.echo("Supported Instrument Formats:\n")
    click.echo("Parser       Vendor           Status")
    click.echo("-" * 50)

    parser_info = {
        "waters": ("Waters", "🚧 In Progress"),
        "agilent": ("Agilent", "📋 Planned"),
        "thermo": ("Thermo Fisher", "📋 Planned"),
    }

    for parser_name in parsers:
        vendor, status = parser_info.get(parser_name, ("Unknown", "Unknown"))
        click.echo(f"{parser_name:<12} {vendor:<16} {status}")

    click.echo("\nRequest a new format:")
    click.echo("https://github.com/yourusername/universal-lab-parser/issues")


@main.command()
@click.argument('filepath', type=click.Path(exists=True))
def info(filepath):
    """Show information about a file without parsing."""
    from universal_lab_parser.utils.file_detection import detect_file_type

    try:
        click.echo(f"Analyzing {filepath}...\n")

        file_type = detect_file_type(filepath)

        if file_type:
            click.echo(f"Detected format: {file_type}")
            click.echo("✓ This file can be parsed")
        else:
            click.echo("✗ Format not recognized")
            click.echo("\nSupported formats:")
            for parser in list_parsers():
                click.echo(f"  - {parser}")

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)


if __name__ == '__main__':
    main()
