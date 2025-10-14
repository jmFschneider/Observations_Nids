class ObservationError(Exception):
    pass


class ValidationError(ObservationError):
    pass


class ImportationError(ObservationError):
    pass


class ReconciliationError(ImportationError):
    pass
