class MeritStatusException(Exception):
    """Merit Status is not a valid option."""


class SearchQueryException(Exception):
    """Search query must be longer than 3 characters."""

class RequestedPermissionException(Exception):
    """Requested Permission is not a valid option."""
