"""Custom exceptions for Universal Lab Parser."""


class UniversalLabParserError(Exception):
    """Base exception for all Universal Lab Parser errors."""
    pass


class ParserNotFoundError(UniversalLabParserError):
    """Raised when no suitable parser is found for a file."""
    pass


class FileFormatError(UniversalLabParserError):
    """Raised when file format is invalid or corrupted."""
    pass


class UnsupportedFormatError(UniversalLabParserError):
    """Raised when file format is not yet supported."""
    pass


class ParseError(UniversalLabParserError):
    """Raised when parsing fails."""
    pass
