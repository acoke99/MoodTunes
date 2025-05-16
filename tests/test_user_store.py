import pytest
import json
import hashlib
from unittest.mock import MagicMock, patch
from user_store import UserStore
from exceptions import ApplicationException


class TestUserStore:
    @pytest.fixture
    def mock_app(self):
        """Create a mock Flask app with database connection."""
        app = MagicMock()
        db_conn = MagicMock()
        app.get_db.return_value = db_conn
        return app

    @pytest.fixture
    def user_store(self, mock_app):
        """Create a UserStore instance with a mock app."""
        return UserStore(mock_app)

    @pytest.fixture
    def mock_session(self):
        """Mock Flask session dictionary."""
        with patch('user_store.session', {}) as mock_session:
            yield mock_session

    def test_init(self, user_store):
        """Test UserStore initialization."""
        assert hasattr(user_store, 'app')
        assert hasattr(user_store, 'default_preferences')
        assert user_store.default_preferences == {
            "artists": [],
            "genres": [],
            "popularity": 80,
            "instrumentalness": 0.2
        }

    def test_hash_user_id(self, user_store):
        """Test that user IDs are hashed correctly."""
        user_id = "test_user"
        expected_hash = hashlib.sha256(user_id.encode('utf-8')).hexdigest()
        assert user_store.hash_user_id(user_id) == expected_hash

    def test_user_exists_true(self, user_store, mock_app):
        """Test user_exists when user exists in database."""
        # Setup mock to return a user
        mock_result = MagicMock()
        mock_result.fetchone.return_value = {"spotify_user": "hashed_id"}
        mock_app.get_db().execute.return_value = mock_result
        
        assert user_store.user_exists("test_user") is True
        # Verify correct SQL query was executed
        mock_app.get_db().execute.assert_called_once()
        args = mock_app.get_db().execute.call_args[0]
        assert "SELECT * FROM user WHERE spotify_user = ?" in args[0]

    def test_user_exists_false(self, user_store, mock_app):
        """Test user_exists when user does not exist."""
        # Setup mock to return None (user not found)
        mock_app.get_db().execute().fetchone.return_value = None
        
        assert user_store.user_exists("test_user") is False

    def test_initialise_user_new(self, user_store, mock_app):
        """Test initializing a new user."""
        # Setup mock to indicate user doesn't exist
        with patch.object(user_store, 'user_exists', return_value=False):
            user_store.initialise_user("test_user")
            
            # Verify user was inserted
            mock_app.get_db().execute.assert_called_once()
            args = mock_app.get_db().execute.call_args[0]
            assert "INSERT INTO user (spotify_user) VALUES (?)" in args[0]
            mock_app.get_db().commit.assert_called_once()

    def test_initialise_user_existing(self, user_store, mock_app):
        """Test initializing an existing user (should do nothing)."""
        # Setup mock to indicate user already exists
        with patch.object(user_store, 'user_exists', return_value=True):
            user_store.initialise_user("test_user")
            
            # Verify no database operations were performed
            mock_app.get_db().execute.assert_not_called()
            mock_app.get_db().commit.assert_not_called()

    def test_initialise_user_error(self, user_store, mock_app):
        """Test error handling when initializing a user fails."""
        # Setup mock to indicate user doesn't exist but DB insert fails
        with patch.object(user_store, 'user_exists', return_value=False):
            mock_app.get_db().execute.side_effect = Exception("DB error")
            
            with pytest.raises(ApplicationException) as excinfo:
                user_store.initialise_user("test_user")
            
            assert "Your MoodTunes User account could not be created" in str(excinfo.value)

    def test_load_preferences_user_not_found(self, user_store):
        """Test load_preferences when user doesn't exist."""
        with patch.object(user_store, 'user_exists', return_value=False):
            with pytest.raises(ApplicationException) as excinfo:
                user_store.load_preferences("test_user")
            
            assert "Your MoodTunes User account could not be found" in str(excinfo.value)

    def test_load_preferences_from_session(self, user_store, mock_session):
        """Test loading preferences from session."""
        # Setup mocks
        with patch.object(user_store, 'user_exists', return_value=True):
            # Set preferences in session
            mock_session['preferences'] = {"artists": ["test_artist"]}
            
            # Call should return early without DB access
            user_store.load_preferences("test_user")
            
            # Verify no DB query was executed
            user_store.app.get_db().execute.assert_not_called()

    def test_load_preferences_from_db(self, user_store, mock_app, mock_session):
        """Test loading preferences from database."""
        # Setup mocks
        with patch.object(user_store, 'user_exists', return_value=True):
            # No preferences in session
            # Mock DB to return preferences
            preferences = {"artists": ["test_artist"], "genres": ["pop"]}
            mock_app.get_db().execute().fetchone.return_value = {
                "preferences_json": json.dumps(preferences)
            }
            
            user_store.load_preferences("test_user")
            
            # Verify preferences were loaded into session
            assert mock_session['preferences'] == preferences
            assert mock_session['preferences_loaded'] is True

    def test_load_preferences_default(self, user_store, mock_app, mock_session):
        """Test loading default preferences when none in DB."""
        # Setup mocks
        with patch.object(user_store, 'user_exists', return_value=True):
            # No preferences in session
            # Mock DB to return no preferences
            mock_app.get_db().execute().fetchone.return_value = {
                "preferences_json": None
            }
            # Mock Spotify service
            mock_app.spotify_service.get_top_artists.return_value = ["top_artist"]
            
            user_store.load_preferences("test_user")
            
            # Verify default preferences were loaded with top artists
            expected_prefs = user_store.default_preferences.copy()
            expected_prefs["artists"] = ["top_artist"]
            assert mock_session['preferences'] == expected_prefs
            assert mock_session['preferences_loaded'] is False

    def test_load_preferences_db_error(self, user_store, mock_app, mock_session):
        """Test handling DB errors when loading preferences."""
        # Setup mocks
        with patch.object(user_store, 'user_exists', return_value=True):
            # No preferences in session
            # Mock DB to raise exception
            mock_app.get_db().execute.side_effect = Exception("DB error")
            # Mock Spotify service
            mock_app.spotify_service.get_top_artists.return_value = ["top_artist"]
            
            # Should not raise exception, but fall back to defaults
            user_store.load_preferences("test_user")
            
            # Verify default preferences were loaded
            expected_prefs = user_store.default_preferences.copy()
            expected_prefs["artists"] = ["top_artist"]
            assert mock_session['preferences'] == expected_prefs
            assert mock_session['preferences_loaded'] is False

    def test_save_preferences_success(self, user_store, mock_app, mock_session):
        """Test successfully saving preferences."""
        # Setup mocks
        with patch.object(user_store, 'user_exists', return_value=True):
            with patch('user_store.Util.sanitise_data', side_effect=lambda x: x):  # Pass through
                preferences = {"artists": ["test_artist"], "genres": ["pop"]}
                
                user_store.save_preferences("test_user", preferences)
                
                # Verify preferences were saved to DB
                mock_app.get_db().execute.assert_called_once()
                args = mock_app.get_db().execute.call_args[0]
                assert "UPDATE user SET preferences_json = ? WHERE spotify_user = ?" in args[0]
                mock_app.get_db().commit.assert_called_once()
                
                # Verify preferences were saved to session
                assert mock_session['preferences'] == preferences

    def test_save_preferences_user_not_found(self, user_store):
        """Test save_preferences when user doesn't exist."""
        with patch.object(user_store, 'user_exists', return_value=False):
            with pytest.raises(ApplicationException) as excinfo:
                user_store.save_preferences("test_user", {})
            
            assert "Your MoodTunes User account could not be found" in str(excinfo.value)

    def test_save_preferences_invalid_format(self, user_store):
        """Test save_preferences with invalid preferences format."""
        with patch.object(user_store, 'user_exists', return_value=True):
            # Test with non-dict preferences
            with pytest.raises(ValueError) as excinfo:
                user_store.save_preferences("test_user", "not_a_dict")
            
            assert "Invalid preferences format" in str(excinfo.value)

    def test_save_preferences_db_error(self, user_store, mock_app):
        """Test handling DB errors when saving preferences."""
        # Setup mocks
        with patch.object(user_store, 'user_exists', return_value=True):
            with patch('user_store.Util.sanitise_data', side_effect=lambda x: x):  # Pass through
                # Mock DB to raise exception
                mock_app.get_db().execute.side_effect = Exception("DB error")
                
                with pytest.raises(ApplicationException) as excinfo:
                    user_store.save_preferences("test_user", {"artists": []})
                
                assert "Your preferences could not be saved" in str(excinfo.value)
