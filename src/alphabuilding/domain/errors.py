class DomainError(Exception):
    """Base exception for errors in the domain layer."""

    pass


class SplitError(DomainError):
    """
    Raised when a dataset cannot be split according to the given specification.

    This typically occurs if the dataset is too short to produce meaningful,
    non-empty splits for all requested ratios.
    """

    pass


class NotFittedError(DomainError):
    """
    Raised when a scaler is not fitted on any data

    """

    pass


class CurriculumValidationError(DomainError):
    """Base exception for errors raised during curriculum validation."""

    pass


class HorizonsNotEqualError(CurriculumValidationError):
    """
    Raised when the datamodule's current horizon does not match the model's horizon.
    This is critical for ensuring the model's output matches the expected target shape.
    """

    pass


class DataModuleMaxHorizonLessThanModuleHorizonError(CurriculumValidationError):
    """
    Raised when the datamodule's configured maximum horizon is smaller than
    the model's current horizon, making it impossible for the curriculum to ever
    reach the model's expected input size.
    """

    pass
