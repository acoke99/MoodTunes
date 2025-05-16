from util import Util


class TestUtil:
    def test_is_safe_path_valid(self):
        """Test is_safe_path with valid paths."""
        assert Util.is_safe_path('/home') is True
        assert Util.is_safe_path('/api/tracks') is True
        assert Util.is_safe_path('/') is True

    def test_is_safe_path_invalid(self):
        """Test is_safe_path with invalid paths."""
        # The actual behavior is that empty string returns None or False
        # The exact result doesn't matter as much as the truthiness
        result = Util.is_safe_path('')
        assert not result, f"Expected empty string to return falsy value, got {result}"

        # None should also return a falsy value
        assert not Util.is_safe_path(None)

        # Paths without leading slash
        assert Util.is_safe_path('home') is False
        assert Util.is_safe_path('api/tracks') is False

        # Paths with schemes
        assert Util.is_safe_path('http://example.com') is False
        assert Util.is_safe_path('https://example.com/api') is False
        assert Util.is_safe_path('ftp://example.com/files') is False

    def test_sanitise_data_strings(self):
        """Test sanitise_data with string inputs."""
        # Normal string
        assert Util.sanitise_data("Hello World") == "Hello World"

        # String with HTML - note: the implementation preserves safe HTML tags
        # Testing the actual behavior of bleach.clean with default settings
        cleaned_script = Util.sanitise_data("<script>alert('XSS')</script>")
        assert "<script>" not in cleaned_script
        assert "alert('XSS')" in cleaned_script

        # Bold tag is allowed by default in bleach
        assert "<b>" in Util.sanitise_data("<b>Bold</b> text")

        # JavaScript in attributes should be removed
        cleaned_link = Util.sanitise_data('<a href="javascript:alert(1)">Click me</a>')
        assert "javascript:alert" not in cleaned_link
        assert "Click me" in cleaned_link

    def test_sanitise_data_numbers(self):
        """Test sanitise_data with numeric inputs."""
        assert Util.sanitise_data(42) == 42
        assert Util.sanitise_data(3.14) == 3.14
        assert Util.sanitise_data(0) == 0
        assert Util.sanitise_data(-10) == -10

    def test_sanitise_data_booleans(self):
        """Test sanitise_data with boolean inputs."""
        assert Util.sanitise_data(True) is True
        assert Util.sanitise_data(False) is False

    def test_sanitise_data_none(self):
        """Test sanitise_data with None input."""
        assert Util.sanitise_data(None) is None

    def test_sanitise_data_lists(self):
        """Test sanitise_data with list inputs."""
        # List of strings
        result = Util.sanitise_data(["Hello", "<script>alert('XSS')</script>"])
        assert result[0] == "Hello"
        assert "<script>" not in result[1]
        assert "alert('XSS')" in result[1]

        # Mixed list
        assert Util.sanitise_data([1, "Hello", True, None]) == [1, "Hello", True, None]

        # Nested list
        result = Util.sanitise_data([1, ["<b>Bold</b>", 2]])
        assert result[0] == 1
        assert "<b>" in result[1][0]  # bleach preserves <b> tags by default
        assert result[1][1] == 2

    def test_sanitise_data_dicts(self):
        """Test sanitise_data with dictionary inputs."""
        # Simple dict
        assert Util.sanitise_data({"name": "John", "age": 30}) == {"name": "John", "age": 30}

        # Dict with HTML values
        result = Util.sanitise_data({"html": "<script>alert('XSS')</script>"})
        assert "<script>" not in result["html"]
        assert "alert('XSS')" in result["html"]

        # Nested dict
        nested_dict = {
            "user": {
                "name": "<b>John</b>",
                "profile": "<a href='javascript:alert(1)'>Profile</a>"
            },
            "settings": {
                "theme": "dark",
                "notifications": True
            }
        }
        result = Util.sanitise_data(nested_dict)

        # Check that sanitization was applied
        assert "<b>" in result["user"]["name"]  # <b> is preserved by bleach
        assert "javascript:alert" not in result["user"]["profile"]
        assert "Profile" in result["user"]["profile"]
        assert result["settings"]["theme"] == "dark"
        assert result["settings"]["notifications"] is True

    def test_sanitise_data_complex(self):
        """Test sanitise_data with complex nested structures."""
        complex_data = {
            "users": [
                {
                    "name": "<b>Alice</b>",
                    "age": 25,
                    "preferences": {
                        "theme": "<script>dark</script>",
                        "notifications": True
                    }
                },
                {
                    "name": "<i>Bob</i>",
                    "age": 30,
                    "preferences": None
                }
            ],
            "settings": {
                "global": True,
                "version": "1.0",
                "html_content": "<div onclick='alert(1)'>Content</div>"
            }
        }

        result = Util.sanitise_data(complex_data)

        # Check structure is preserved
        assert len(result["users"]) == 2
        assert result["users"][0]["age"] == 25
        assert result["users"][1]["age"] == 30
        assert result["users"][1]["preferences"] is None

        # Check HTML sanitization
        assert "<b>" in result["users"][0]["name"]  # <b> is preserved
        assert "<i>" in result["users"][1]["name"]  # <i> is preserved
        assert "<script>" not in result["users"][0]["preferences"]["theme"]
        assert "dark" in result["users"][0]["preferences"]["theme"]
        assert "onclick=" not in result["settings"]["html_content"]
        assert "Content" in result["settings"]["html_content"]

        # Check non-string values
        assert result["settings"]["global"] is True
        assert result["settings"]["version"] == "1.0"
