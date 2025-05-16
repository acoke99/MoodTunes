import pytest
import json
from unittest.mock import MagicMock, patch


class TestApp:
    @pytest.fixture
    def client(self):
        """Create a test client for the app."""
        # Import here to avoid circular imports
        from app import app
        
        # Configure app for testing
        app.config.update({
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,  # Disable CSRF for testing
            "SERVER_NAME": "localhost",  # Required for url_for with external=True
        })
        
        # Create test client
        with app.test_client() as client:
            # Establish application context
            with app.app_context():
                yield client

    @pytest.fixture
    def mock_spotify_service(self):
        """Create a mock Spotify service."""
        mock = MagicMock()
        mock.get_auth_url.return_value = "https://spotify.auth.url"
        mock.get_user_id.return_value = "test_user_id"
        return mock

    @pytest.fixture
    def mock_user_store(self):
        """Create a mock user store."""
        mock = MagicMock()
        return mock

    @pytest.fixture
    def mock_recommender(self):
        """Create a mock recommendation engine."""
        mock = MagicMock()
        mock.get_recommendations.return_value = [
            {
                "track_id": "spotify:track:1",
                "track_name": "Test Track 1",
                "artist": "Test Artist 1",
                "valence": 0.5,
                "energy": 0.5
            },
            {
                "track_id": "spotify:track:2",
                "track_name": "Test Track 2",
                "artist": "Test Artist 2",
                "valence": 0.7,
                "energy": 0.7
            }
        ]
        return mock

    @pytest.fixture
    def mock_track_data(self):
        """Create a mock track data service."""
        mock = MagicMock()
        mock.get_all_artists.return_value = ["Artist 1", "Artist 2", "Artist 3"]
        return mock

    def test_home_page_unauthenticated(self, client):
        """Test the home page when user is not logged in."""
        response = client.get('/')
        assert response.status_code == 200
        # Check that session is initialized
        with client.session_transaction() as sess:
            assert sess.get('session_initialised') is True

    def test_home_page_authenticated(self, client):
        """Test the home page when user is logged in (should redirect to mood page)."""
        with client.session_transaction() as sess:
            sess['logged_in'] = True
        
        response = client.get('/')
        assert response.status_code == 302
        assert response.location == '/mood'

    def test_mood_page_unauthenticated(self, client):
        """Test the mood page when user is not logged in (should redirect to home)."""
        response = client.get('/mood')
        assert response.status_code == 302
        assert response.location == '/'

    def test_mood_page_authenticated(self, client):
        """Test the mood page when user is logged in."""
        with client.session_transaction() as sess:
            sess['logged_in'] = True
        
        response = client.get('/mood')
        assert response.status_code == 200

    def test_mood_page_post(self, client):
        """Test submitting the mood form."""
        with client.session_transaction() as sess:
            sess['logged_in'] = True
        
        response = client.post('/mood', data={
            'valence': '75',
            'energy': '50'
        })
        
        assert response.status_code == 302
        assert response.location == '/goal'
        
        # Check that session values are set correctly
        with client.session_transaction() as sess:
            assert sess['valence'] == 0.75
            assert sess['energy'] == 0.5

    def test_goal_page_unauthenticated(self, client):
        """Test the goal page when user is not logged in (should redirect to home)."""
        response = client.get('/goal')
        assert response.status_code == 302
        assert response.location == '/'

    def test_goal_page_authenticated(self, client):
        """Test the goal page when user is logged in."""
        with client.session_transaction() as sess:
            sess['logged_in'] = True
        
        response = client.get('/goal')
        assert response.status_code == 200

    @patch('app.app.user_store')
    def test_goal_page_post_with_preferences(self, mock_user_store, client):
        """Test submitting the goal form when user has preferences."""
        mock_user_store.load_preferences.return_value = None
        
        with client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['user_id'] = 'test_user_id'
            sess['preferences_loaded'] = True
        
        response = client.post('/goal', data={
            'goal': 'lift_me_up'
        })
        
        assert response.status_code == 302
        assert response.location == '/recommendations'
        
        # Check that session values are set correctly
        with client.session_transaction() as sess:
            assert sess['goal'] == 'lift_me_up'
        
        # Verify user store was called
        mock_user_store.load_preferences.assert_called_once_with('test_user_id')

    @patch('app.app.user_store')
    def test_goal_page_post_without_preferences(self, mock_user_store, client):
        """Test submitting the goal form when user doesn't have preferences."""
        mock_user_store.load_preferences.return_value = None
        
        with client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['user_id'] = 'test_user_id'
            sess['preferences_loaded'] = False
        
        response = client.post('/goal', data={
            'goal': 'chill_me_out'
        })
        
        assert response.status_code == 302
        assert response.location == '/preferences'
        
        # Check that session values are set correctly
        with client.session_transaction() as sess:
            assert sess['goal'] == 'chill_me_out'
        
        # Verify user store was called
        mock_user_store.load_preferences.assert_called_once_with('test_user_id')

    def test_preferences_page_unauthenticated(self, client):
        """Test the preferences page when user is not logged in (should redirect to home)."""
        response = client.get('/preferences')
        assert response.status_code == 302
        assert response.location == '/'

    @patch('app.app.user_store')
    def test_preferences_page_authenticated(self, mock_user_store, client):
        """Test the preferences page when user is logged in."""
        # Set up the mock to properly handle load_preferences
        mock_user_store.load_preferences.return_value = None
        
        with client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['user_id'] = 'test_user_id'
            sess['preferences'] = {
                'artists': ['Artist 1'],
                'genres': ['Pop'],
                'popularity': 80,
                'instrumentalness': 0.2
            }
        
        response = client.get('/preferences')
        assert response.status_code == 200
        
        # Verify user store was called
        mock_user_store.load_preferences.assert_called_once_with('test_user_id')

    @patch('app.app.user_store')
    def test_preferences_page_post(self, mock_user_store, client):
        """Test submitting the preferences form."""
        mock_user_store.save_preferences.return_value = None
        
        with client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['user_id'] = 'test_user_id'
        
        response = client.post('/preferences', data={
            'artists': ['Artist 1', 'Artist 2'],
            'genres': ['Pop', 'Rock'],
            'popularity': '70',
            'instrumentalness': '0.3',
            'source': '/recommendations'
        })
        
        assert response.status_code == 302
        assert response.location == '/recommendations'
        
        # Verify user store was called with correct preferences
        mock_user_store.save_preferences.assert_called_once_with(
            'test_user_id',
            {
                'artists': ['Artist 1', 'Artist 2'],
                'genres': ['Pop', 'Rock'],
                'popularity': 70,
                'instrumentalness': 0.3
            }
        )

    def test_recommendations_page_unauthenticated(self, client):
        """Test the recommendations page when user is not logged in (should redirect to home)."""
        response = client.get('/recommendations')
        assert response.status_code == 302
        assert response.location == '/'

    @patch('app.app.recommender')
    def test_recommendations_page_authenticated(self, mock_recommender, client):
        """Test the recommendations page when user is logged in with all required session data."""
        mock_recommender.get_recommendations.return_value = [
            {
                "track_id": "spotify:track:1",
                "track_name": "Test Track 1",
                "artist": "Test Artist 1",
                "valence": 0.5,
                "energy": 0.5
            },
            {
                "track_id": "spotify:track:2",
                "track_name": "Test Track 2",
                "artist": "Test Artist 2",
                "valence": 0.7,
                "energy": 0.7
            }
        ]
        
        with client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['valence'] = 0.6
            sess['energy'] = 0.4
            sess['goal'] = 'lift_me_up'
            sess['preferences'] = {
                'artists': ['Artist 1'],
                'genres': ['Pop'],
                'popularity': 80,
                'instrumentalness': 0.2
            }
            sess['recommended_ids'] = []
        
        response = client.get('/recommendations')
        assert response.status_code == 200
        
        # Verify recommender was called with correct parameters
        mock_recommender.get_recommendations.assert_called_once_with(
            0.6, 0.4, 'lift_me_up',
            {
                'artists': ['Artist 1'],
                'genres': ['Pop'],
                'popularity': 80,
                'instrumentalness': 0.2
            },
            []
        )
        
        # Check that session values are updated correctly
        with client.session_transaction() as sess:
            assert sess['recommended_ids'] == ['spotify:track:1', 'spotify:track:2']

    def test_recommendations_page_missing_data(self, client):
        """Test the recommendations page when required session data is missing."""
        with client.session_transaction() as sess:
            sess['logged_in'] = True
            # Missing valence and energy
        
        response = client.get('/recommendations')
        assert response.status_code == 302
        assert response.location == '/mood'
        
        # Test with valence/energy but missing goal
        with client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['valence'] = 0.6
            sess['energy'] = 0.4
            # Missing goal
        
        response = client.get('/recommendations')
        assert response.status_code == 302
        assert response.location == '/goal'
        
        # Test with valence/energy/goal but missing preferences
        with client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['valence'] = 0.6
            sess['energy'] = 0.4
            sess['goal'] = 'lift_me_up'
            # Missing preferences
        
        response = client.get('/recommendations')
        assert response.status_code == 302
        assert response.location == '/preferences'

    @patch('app.app.spotify_service')
    def test_login(self, mock_spotify_service, client):
        """Test the login route."""
        mock_spotify_service.get_auth_url.return_value = "https://spotify.auth.url"
        
        response = client.get('/login')
        assert response.status_code == 302
        assert response.location == "https://spotify.auth.url"
        
        # Verify Spotify service was called
        mock_spotify_service.get_auth_url.assert_called_once()

    @patch('app.app.spotify_service')
    @patch('app.app.user_store')
    def test_callback_success(self, mock_user_store, mock_spotify_service, client):
        """Test the callback route with successful authentication."""
        mock_spotify_service.handle_callback.return_value = None
        mock_spotify_service.get_user_id.return_value = "test_user_id"
        mock_user_store.initialise_user.return_value = None
        
        response = client.get('/callback?state=test_state&code=test_code')
        assert response.status_code == 302
        assert response.location == '/mood'
        
        # Verify services were called
        mock_spotify_service.handle_callback.assert_called_once_with('test_state', 'test_code')
        mock_spotify_service.get_user_id.assert_called_once()
        mock_user_store.initialise_user.assert_called_once_with('test_user_id')
        
        # Check that session values are set correctly
        with client.session_transaction() as sess:
            assert sess['user_id'] == 'test_user_id'

    @patch('app.app.spotify_service')
    def test_callback_failure(self, mock_spotify_service, client):
        """Test the callback route with failed authentication."""
        mock_spotify_service.handle_callback.side_effect = Exception("Authentication failed")
        
        response = client.get('/callback?state=test_state&code=test_code')
        assert response.status_code == 302
        assert response.location == '/'

    def test_logout(self, client):
        """Test the logout route."""
        with client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['user_id'] = 'test_user_id'
        
        response = client.get('/logout')
        assert response.status_code == 200
        
        # Check that session is cleared
        with client.session_transaction() as sess:
            assert 'logged_in' not in sess
            assert 'user_id' not in sess

    @patch('app.app.track_data')
    def test_artists_api(self, mock_track_data, client):
        """Test the artists API endpoint."""
        mock_track_data.get_all_artists.return_value = ["Artist 1", "Artist 2", "Artist 3"]
        
        response = client.get('/api/artists')
        assert response.status_code == 200
        
        # Check response data
        data = json.loads(response.data)
        assert data == ["Artist 1", "Artist 2", "Artist 3"]
        
        # Verify track data service was called
        mock_track_data.get_all_artists.assert_called_once()

    @patch('app.app.spotify_service')
    def test_queue_api_success(self, mock_spotify_service, client):
        """Test the queue API endpoint with successful queuing."""
        mock_spotify_service.queue_tracks.return_value = True
        
        response = client.post('/api/queue', 
                              json=["spotify:track:1", "spotify:track:2"],
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "message" in data
        
        # Verify Spotify service was called
        mock_spotify_service.queue_tracks.assert_called_once_with(["spotify:track:1", "spotify:track:2"])

    @patch('app.app.spotify_service')
    def test_queue_api_failure(self, mock_spotify_service, client):
        """Test the queue API endpoint with failed queuing."""
        mock_spotify_service.queue_tracks.return_value = False
        
        response = client.post('/api/queue', 
                              json=["spotify:track:1", "spotify:track:2"],
                              content_type='application/json')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert "error" in data
        
        # Verify Spotify service was called
        mock_spotify_service.queue_tracks.assert_called_once_with(["spotify:track:1", "spotify:track:2"])

    @patch('app.app.spotify_service')
    def test_queue_api_no_uris(self, mock_spotify_service, client):
        """Test the queue API endpoint with no URIs provided."""
        response = client.post('/api/queue', 
                              json=[],
                              content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
        
        # Verify Spotify service was not called
        mock_spotify_service.queue_tracks.assert_not_called()

    @patch('app.app.spotify_service')
    def test_playback_controls(self, mock_spotify_service, client):
        """Test the playback control API endpoints."""
        # Test pause
        mock_spotify_service.pause_track.return_value = True
        response = client.post('/api/pause')
        assert response.status_code == 204
        mock_spotify_service.pause_track.assert_called_once()
        
        # Test play
        mock_spotify_service.play_track.return_value = True
        response = client.post('/api/play')
        assert response.status_code == 204
        mock_spotify_service.play_track.assert_called_once()
        
        # Test next
        mock_spotify_service.next_track.return_value = True
        response = client.post('/api/next')
        assert response.status_code == 204
        mock_spotify_service.next_track.assert_called_once()
        
        # Test previous
        mock_spotify_service.previous_track.return_value = True
        response = client.post('/api/previous')
        assert response.status_code == 204
        mock_spotify_service.previous_track.assert_called_once()

    @patch('app.app.spotify_service')
    def test_playback_controls_error(self, mock_spotify_service, client):
        """Test the playback control API endpoints with errors."""
        # Test pause with error
        mock_spotify_service.pause_track.side_effect = Exception("No active device")
        response = client.post('/api/pause')
        assert response.status_code == 403
        assert response.data == b'Action not possible'
        
        # Reset mock for next test
        mock_spotify_service.pause_track.reset_mock()
        mock_spotify_service.pause_track.side_effect = None
