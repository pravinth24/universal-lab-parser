"""Parser implementations for different instrument vendors."""

from universal_lab_parser.parsers.waters import WatersParser
from universal_lab_parser.core.exceptions import ParserNotFoundError


# Registry of available parsers
PARSER_REGISTRY = {
    "waters": WatersParser,
    # "agilent": AgilentParser,  # Coming soon
    # "thermo": ThermoParser,    # Coming soon
}


def get_parser(parser_type: str):
    """
    Get a parser instance by type.

    Args:
        parser_type: Parser type ('waters', 'agilent', 'thermo', etc.)

    Returns:
        BaseParser: Parser instance

    Raises:
        ParserNotFoundError: If parser type is not recognized
    """
    parser_class = PARSER_REGISTRY.get(parser_type.lower())
    if parser_class is None:
        available = ", ".join(PARSER_REGISTRY.keys())
        raise ParserNotFoundError(
            f"Parser '{parser_type}' not found. Available parsers: {available}"
        )
    return parser_class()


def list_parsers():
    """List all available parsers."""
    return list(PARSER_REGISTRY.keys())


__all__ = ["WatersParser", "get_parser", "list_parsers"]
