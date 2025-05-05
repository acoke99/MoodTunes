# Authentication exception class
class AuthenticationException(Exception):
    def __init__(self, message: str, details: str | None = None):
        super().__init__(message)
        self.details = details


# Application exception class
class ApplicationException(Exception):
    def __init__(self, message: str, details: str | None = None):
        super().__init__(message)
        self.details = details
