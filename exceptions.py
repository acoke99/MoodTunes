# Authentication exception class
class AuthenticationException(Exception):
    def __init__(self, message: str, details: str | None = None):
        super().__init__(message)
        self.details = details


# Application exception class
class ApplicationException(Exception):
    def __init__(self, message: str, details: str | None = None):
        # Check if this is an unregistered user error
        if details and "user may not be registered" in details:
            message = ('Playback is currently only available to approved users during testing. '
                       'Please contact the developer if you need access, or explore the app in demo mode.')
        super().__init__(message)
        self.details = details
