import bleach
from urllib.parse import urlparse


# Utility functions
class Util:
    # Check if a path is safe
    # Must be a relative path starting with '/' and no scheme (i.e., no http://)
    @staticmethod
    def is_safe_path(path: str) -> bool:
        return path and urlparse(path).scheme == '' and path.startswith('/')

    # Sanitise data to prevent XSS attacks
    def sanitise_data(obj):
        if isinstance(obj, dict):
            return {k: Util.sanitise_data(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [Util.sanitise_data(v) for v in obj]
        elif isinstance(obj, str):
            return bleach.clean(obj, strip=True)
        else:
            return obj  # Leave numbers, booleans, etc. unchanged
