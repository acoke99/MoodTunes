from urllib.parse import urlparse


# Utility functions
class Util:
    # Check if a path is safe
    # Must be a relative path starting with '/' and no scheme (i.e., no http://)
    @staticmethod
    def is_safe_path(path: str) -> bool:
        return path and urlparse(path).scheme == '' and path.startswith('/')
