# beeplan/core/errors.py
class InvalidInputError(Exception):
    """Raised when input config is malformed or incomplete."""

class ConstraintConfigError(Exception):
    """Raised when constraint configuration is inconsistent."""

class SchedulingError(Exception):
    """Raised for unexpected errors during scheduling."""
