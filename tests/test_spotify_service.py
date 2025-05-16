import pytest
from unittest.mock import patch
from spotipy import SpotifyException
from spotify_service import SpotifyService
from exceptions import AuthenticationException, ApplicationException

# Add the parent directory to sys.path to allow imports from the root directory
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture
def mock_spotify_oauth():
    """Create a mock SpotifyOAuth object."""
    with patch('spotify_service.SpotifyOAuth') as mock_oauth:
        # Configure the mock
        mock_instance = mock_oauth.return_value
        mock_instance.get_authorize_url.return_value = "https://accounts.spotify.com/authorize?mock_url"
        mock_instance.get_access_token.return_value = {
            "access_token": "mock_access_token",
            "refresh_token": "mock_refresh_token",
            "expires_at": 1715000000  # Future timestamp
        }
        mock_instance.is_token_expired.return_value = False
        yield mock_instance


@pytest.fixture
def mock_spotify_client():
    """Create a mock Spotify client."""
    with patch('spotify_service.Spotify') as mock_spotify:
        # Configure the mock
        mock_instance = mock_spotify.return_value

        # Mock current_user
        mock_instance.current_user.return_value = {
            "id": "mock_user_id",
            "display_name": "Mock User"
        }

        # Mock tracks
        mock_instance.tracks.return_value = {
            "tracks": [
                {
                    "id": "track1",
                    "name": "Track 1",
                    "album": {"images": [{"url": "image1_small.jpg"}, {"url": "image1.jpg"}]}
                },
                {
                    "id": "track2",
                    "name": "Track 2",
                    "album": {"images": [{"url": "image2_small.jpg"}, {"url": "image2.jpg"}]}
                }
            ]
        }

        # Mock devices
        mock_instance.devices.return_value = {
            "devices": [
                {
                    "id": "device1",
                    "name": "Device 1",
                    "is_active": True
                }
            ]
        }

        # Mock top artists
        mock_instance.current_user_top_artists.return_value = {
            "items": [
                {"name": "Artist 1"},
                {"name": "Artist 2"},
                {"name": "Artist 3"}
            ]
        }

        yield mock_instance


@pytest.fixture
def spotify_service(mock_spotify_oauth):
    """Create a SpotifyService with mocked dependencies."""
    return SpotifyService(
        client_id="mock_client_id",
        client_secret="mock_client_secret",
        redirect_uri="http://localhost:5000/callback"
    )


@pytest.fixture
def authenticated_session():
    """Create a mock Flask session with authentication data."""
    session_data = {
        "token_info": {
            "access_token": "mock_access_token",
            "refresh_token": "mock_refresh_token",
            "expires_at": 1715000000  # Future timestamp
        },
        "logged_in": True,
        "oauth_state": "mock_state"
    }

    # Use a context manager to mock the Flask session
    with patch('spotify_service.session', session_data):
        yield session_data


class TestSpotifyService:
    """Test the SpotifyService class."""

    def test_init(self, spotify_service, mock_spotify_oauth):
        """Test that the service initializes correctly."""
        assert spotify_service.oauth is mock_spotify_oauth

    def test_get_auth_url(self, spotify_service):
        """Test getting the Spotify authorization URL."""
        with patch('spotify_service.secrets.token_urlsafe', return_value="mock_state"):
            with patch('spotify_service.session', {}) as mock_session:
                auth_url = spotify_service.get_auth_url()

                # Check that the URL was generated
                assert auth_url == "https://accounts.spotify.com/authorize?mock_url"

                # Check that the state was stored in the session
                assert mock_session.get('oauth_state') == "mock_state"

    def test_handle_callback_success(self, spotify_service, authenticated_session):
        """Test successful callback handling."""
        # Set up the test
        oauth_state = "mock_state"
        oauth_code = "mock_code"

        # Call the method
        spotify_service.handle_callback(oauth_state, oauth_code)

        # Verify the OAuth was called correctly
        spotify_service.oauth.get_access_token.assert_called_with(oauth_code)

        # Check that the session was updated
        assert authenticated_session.get('logged_in') is True
        assert 'token_info' in authenticated_session

    def test_handle_callback_invalid_state(self, spotify_service):
        """Test callback handling with invalid state."""
        with patch('spotify_service.session', {'oauth_state': 'correct_state'}):
            with pytest.raises(AuthenticationException) as excinfo:
                spotify_service.handle_callback("wrong_state", "mock_code")

            assert "Invalid state parameter" in str(excinfo.value)

    def test_get_client_not_logged_in(self, spotify_service):
        """Test getting the Spotify client when not logged in."""
        with patch('spotify_service.session', {}):
            with pytest.raises(AuthenticationException) as excinfo:
                spotify_service.get_client()

            assert "You are not logged in" in str(excinfo.value)

    def test_get_client_token_expired(self, spotify_service, authenticated_session):
        """Test getting the Spotify client with an expired token."""
        # Set up the test
        spotify_service.oauth.is_token_expired.return_value = True
        spotify_service.oauth.refresh_access_token.return_value = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_at": 1720000000
        }

        # Call the method
        spotify_service.get_client()

        # Verify the token was refreshed
        spotify_service.oauth.refresh_access_token.assert_called_once()

        # Check that the session was updated with the new token
        assert authenticated_session.get('token_info')['access_token'] == "new_access_token"

    def test_get_client_success(self, spotify_service, authenticated_session):
        """Test successfully getting the Spotify client."""
        # Call the method
        with patch('spotify_service.Spotify') as mock_spotify:
            spotify_service.get_client()

            # Verify Spotify was initialized with the correct token
            mock_spotify.assert_called_with(auth="mock_access_token")

    def test_get_user_id(self, spotify_service, authenticated_session, mock_spotify_client):
        """Test getting the user ID."""
        with patch('spotify_service.Spotify', return_value=mock_spotify_client):
            user_id = spotify_service.get_user_id()

            # Verify the user ID was retrieved
            assert user_id == "mock_user_id"
            mock_spotify_client.current_user.assert_called_once()

    def test_get_tracks(self, spotify_service, authenticated_session, mock_spotify_client):
        """Test getting track information."""
        with patch('spotify_service.Spotify', return_value=mock_spotify_client):
            track_ids = ["track1", "track2"]
            tracks = spotify_service.get_tracks(track_ids)

            # Verify the tracks were retrieved
            assert len(tracks) == 2
            assert tracks[0]["id"] == "track1"
            assert tracks[1]["id"] == "track2"
            mock_spotify_client.tracks.assert_called_with(track_ids)

    def test_get_active_device_no_devices(self, spotify_service, authenticated_session, mock_spotify_client):
        """Test getting the active device when no devices are available."""
        # Modify the mock to return no devices
        mock_spotify_client.devices.return_value = {"devices": []}

        with patch('spotify_service.Spotify', return_value=mock_spotify_client):
            with pytest.raises(ApplicationException) as excinfo:
                spotify_service.get_active_device()

            assert "No active Spotify device found" in str(excinfo.value)

    def test_get_active_device_success(self, spotify_service, authenticated_session, mock_spotify_client):
        """Test successfully getting the active device."""
        with patch('spotify_service.Spotify', return_value=mock_spotify_client):
            device_id = spotify_service.get_active_device()

            # Verify the device ID was retrieved
            assert device_id == "device1"
            mock_spotify_client.devices.assert_called_once()

    def test_queue_tracks(self, spotify_service, authenticated_session, mock_spotify_client):
        """Test adding tracks to the queue."""
        with patch('spotify_service.Spotify', return_value=mock_spotify_client):
            uris = ["spotify:track:track1", "spotify:track:track2"]
            result = spotify_service.queue_tracks(uris)

            # Verify the tracks were added to the queue
            assert result is True
            mock_spotify_client.start_playback.assert_called_with("device1", None, uris)

    def test_queue_tracks_error(self, spotify_service, authenticated_session, mock_spotify_client):
        """Test error handling when adding tracks to the queue."""
        # Modify the mock to raise an exception
        mock_spotify_client.start_playback.side_effect = SpotifyException(
            http_status=404,
            msg="Device not found",
            code=-1
        )

        with patch('spotify_service.Spotify', return_value=mock_spotify_client):
            with pytest.raises(ApplicationException) as excinfo:
                spotify_service.queue_tracks(["spotify:track:track1"])

            assert "There was an error adding the tracks to the queue" in str(excinfo.value)

    def test_pause_track(self, spotify_service, authenticated_session, mock_spotify_client):
        """Test pausing playback."""
        with patch('spotify_service.Spotify', return_value=mock_spotify_client):
            result = spotify_service.pause_track()

            # Verify playback was paused
            assert result is True
            mock_spotify_client.pause_playback.assert_called_with(device_id="device1")

    def test_play_track(self, spotify_service, authenticated_session, mock_spotify_client):
        """Test resuming playback."""
        with patch('spotify_service.Spotify', return_value=mock_spotify_client):
            result = spotify_service.play_track()

            # Verify playback was resumed
            assert result is True
            mock_spotify_client.start_playback.assert_called_with(device_id="device1")

    def test_next_track(self, spotify_service, authenticated_session, mock_spotify_client):
        """Test skipping to the next track."""
        with patch('spotify_service.Spotify', return_value=mock_spotify_client):
            result = spotify_service.next_track()

            # Verify next track was called
            assert result is True
            mock_spotify_client.next_track.assert_called_with(device_id="device1")

    def test_previous_track(self, spotify_service, authenticated_session, mock_spotify_client):
        """Test skipping to the previous track."""
        with patch('spotify_service.Spotify', return_value=mock_spotify_client):
            result = spotify_service.previous_track()

            # Verify previous track was called
            assert result is True
            mock_spotify_client.previous_track.assert_called_with(device_id="device1")

    def test_get_top_artists(self, spotify_service, authenticated_session, mock_spotify_client):
        """Test getting the user's top artists."""
        with patch('spotify_service.Spotify', return_value=mock_spotify_client):
            artists = spotify_service.get_top_artists()

            # Verify the artists were retrieved
            assert len(artists) == 3
            assert artists == ["Artist 1", "Artist 2", "Artist 3"]
            mock_spotify_client.current_user_top_artists.assert_called_with(limit=10)

    def test_get_top_artists_error(self, spotify_service, authenticated_session, mock_spotify_client):
        """Test error handling when getting top artists."""
        # Modify the mock to raise an exception
        mock_spotify_client.current_user_top_artists.side_effect = SpotifyException(
            http_status=500,
            msg="API error",
            code=-1
        )

        with patch('spotify_service.Spotify', return_value=mock_spotify_client):
            with pytest.raises(ApplicationException) as excinfo:
                spotify_service.get_top_artists()

            assert "There was an error retrieving your top artists" in str(excinfo.value)
