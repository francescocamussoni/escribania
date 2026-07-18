class EscrituraNotFoundError(Exception):
    """Raised when an escritura does not exist."""


class EscrituraClosedError(Exception):
    """Raised when mutating a closed escritura."""
