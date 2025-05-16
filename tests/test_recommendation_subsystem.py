import os
import pytest
import tempfile
from unittest.mock import patch
from flask import Flask, session
from track_data import TrackData
from spotify_service import SpotifyService
from recommend import RecommendationEngine

"""
Integration tests for the recommendation pipeline.

These tests use:
1. Real TrackData with a test CSV file
2. Real RecommendationEngine implementation
3. Controlled SpotifyService with minimal mocking
"""


@pytest.fixture
def app():
    """Create a Flask app for testing."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test_secret_key'
    app.config['TESTING'] = True
    return app


@pytest.fixture
def real_track_data():
    """Create a real TrackData instance with a test CSV file."""
    # Create a temporary CSV file with test data
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as temp_file:
        temp_file.write("""track_id,track_name,artist_name,new_genre,valence,energy,popularity,instrumentalness
spotify:track:1,Happy Song,Happy Artist,Pop,0.9,0.8,80,0.1
spotify:track:2,Sad Song,Sad Artist,Rock,0.2,0.3,60,0.3
spotify:track:3,Energetic Song,Energy Artist,Dance,0.6,0.9,75,0.05
spotify:track:4,Chill Song,Chill Artist,Indie,0.5,0.4,65,0.2
spotify:track:5,Angry Song,Angry Artist,Metal,0.3,0.8,70,0.1
spotify:track:6,Happy Dance,Happy Artist,Dance,0.8,0.9,85,0.05
spotify:track:7,Melancholy,Sad Artist,Indie,0.3,0.4,55,0.4
spotify:track:8,Party Anthem,Energy Artist,Pop,0.7,0.9,90,0.02
spotify:track:9,Relaxing Tune,Chill Artist,Ambient,0.6,0.2,50,0.6
spotify:track:10,Rock Ballad,Rock Artist,Rock,0.4,0.6,75,0.1
spotify:track:11,Summer Hit,Pop Artist,Pop,0.8,0.7,88,0.05
spotify:track:12,Winter Blues,Jazz Artist,Jazz,0.4,0.3,65,0.2
spotify:track:13,Workout Mix,EDM Artist,Dance,0.6,1.0,80,0.1
spotify:track:14,Study Music,Ambient Artist,Ambient,0.5,0.2,45,0.8
spotify:track:15,Road Trip,Rock Artist,Rock,0.7,0.8,70,0.1
""")
        temp_path = temp_file.name

    try:
        # Create and load a real TrackData instance
        track_data = TrackData()
        track_data.load_csv(temp_path)
        yield track_data
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)


@pytest.fixture
def controlled_spotify_service(app):
    """
    Create a SpotifyService with minimal mocking.

    This uses the real SpotifyService class but controls the external API calls
    to avoid hitting the actual Spotify API.
    """
    with app.test_request_context():
        # Set up a session to simulate being logged in
        session['logged_in'] = True
        session['token_info'] = {
            'access_token': 'test_token',
            'refresh_token': 'test_refresh',
            'expires_at': 9999999999  # Far future
        }

        # Create a real SpotifyService instance
        spotify_service = SpotifyService(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:5000/callback"
        )

        # Patch only the get_tracks method to return controlled data
        # This is minimal mocking - we're using the real class but controlling just the external API
        with patch.object(spotify_service, 'get_tracks') as mock_get_tracks:
            # Define the mock return value
            mock_tracks = [
                {
                    'id': '1',
                    'name': 'Happy Song',
                    'artists': [{'name': 'Happy Artist'}],
                    'album': {'images': [{'url': 'image1_small.jpg'}, {'url': 'image1.jpg'}]}
                },
                {
                    'id': '2',
                    'name': 'Sad Song',
                    'artists': [{'name': 'Sad Artist'}],
                    'album': {'images': [{'url': 'image2_small.jpg'}, {'url': 'image2.jpg'}]}
                },
                {
                    'id': '3',
                    'name': 'Energetic Song',
                    'artists': [{'name': 'Energy Artist'}],
                    'album': {'images': [{'url': 'image3_small.jpg'}, {'url': 'image3.jpg'}]}
                },
                {
                    'id': '4',
                    'name': 'Chill Song',
                    'artists': [{'name': 'Chill Artist'}],
                    'album': {'images': [{'url': 'image4_small.jpg'}, {'url': 'image4.jpg'}]}
                },
                {
                    'id': '5',
                    'name': 'Angry Song',
                    'artists': [{'name': 'Angry Artist'}],
                    'album': {'images': [{'url': 'image5_small.jpg'}, {'url': 'image5.jpg'}]}
                },
                {
                    'id': '6',
                    'name': 'Happy Dance',
                    'artists': [{'name': 'Happy Artist'}],
                    'album': {'images': [{'url': 'image6_small.jpg'}, {'url': 'image6.jpg'}]}
                },
                {
                    'id': '7',
                    'name': 'Melancholy',
                    'artists': [{'name': 'Sad Artist'}],
                    'album': {'images': [{'url': 'image7_small.jpg'}, {'url': 'image7.jpg'}]}
                },
                {
                    'id': '8',
                    'name': 'Party Anthem',
                    'artists': [{'name': 'Energy Artist'}],
                    'album': {'images': [{'url': 'image8_small.jpg'}, {'url': 'image8.jpg'}]}
                },
                {
                    'id': '9',
                    'name': 'Relaxing Tune',
                    'artists': [{'name': 'Chill Artist'}],
                    'album': {'images': [{'url': 'image9_small.jpg'}, {'url': 'image9.jpg'}]}
                },
                {
                    'id': '10',
                    'name': 'Rock Ballad',
                    'artists': [{'name': 'Rock Artist'}],
                    'album': {'images': [{'url': 'image10_small.jpg'}, {'url': 'image10.jpg'}]}
                },
                {
                    'id': '11',
                    'name': 'Summer Hit',
                    'artists': [{'name': 'Pop Artist'}],
                    'album': {'images': [{'url': 'image11_small.jpg'}, {'url': 'image11.jpg'}]}
                },
                {
                    'id': '12',
                    'name': 'Winter Blues',
                    'artists': [{'name': 'Jazz Artist'}],
                    'album': {'images': [{'url': 'image12_small.jpg'}, {'url': 'image12.jpg'}]}
                },
                {
                    'id': '13',
                    'name': 'Workout Mix',
                    'artists': [{'name': 'EDM Artist'}],
                    'album': {'images': [{'url': 'image13_small.jpg'}, {'url': 'image13.jpg'}]}
                },
                {
                    'id': '14',
                    'name': 'Study Music',
                    'artists': [{'name': 'Ambient Artist'}],
                    'album': {'images': [{'url': 'image14_small.jpg'}, {'url': 'image14.jpg'}]}
                },
                {
                    'id': '15',
                    'name': 'Road Trip',
                    'artists': [{'name': 'Rock Artist'}],
                    'album': {'images': [{'url': 'image15_small.jpg'}, {'url': 'image15.jpg'}]}
                }
            ]

            # Configure the mock to return specific tracks based on the input track_ids
            def get_tracks_side_effect(track_ids):
                # Convert track_ids to simple ids (remove spotify:track: prefix)
                simple_ids = [tid.replace('spotify:track:', '') for tid in track_ids]
                # Return only the tracks that match the requested ids
                return [track for track in mock_tracks if track['id'] in simple_ids]

            mock_get_tracks.side_effect = get_tracks_side_effect

            yield spotify_service


@pytest.fixture
def real_recommendation_engine(real_track_data, controlled_spotify_service):
    """Create a real RecommendationEngine with real components."""
    return RecommendationEngine(real_track_data, controlled_spotify_service)


class TestRecommendationIntegration:
    """Integration tests for the recommendation pipeline."""

    def test_happy_mood_recommendations(self, real_recommendation_engine, app):
        """Test getting recommendations for a happy mood."""
        with app.test_request_context():
            # Set up session data
            session['logged_in'] = True

            # Test user preferences
            preferences = {
                "artists": ["Happy Artist"],
                "genres": ["Pop"],
                "popularity": 70,
                "instrumentalness": 0.1
            }

            # Get recommendations for a happy mood
            recommendations = real_recommendation_engine.get_recommendations(
                valence=0.8,  # Happy
                energy=0.7,   # Moderately energetic
                goal="lift_me_up",
                preferences=preferences,
                recommended_ids=[]
            )

            # Verify we got recommendations
            assert len(recommendations) > 0

            # Verify the recommendations have the expected structure
            for rec in recommendations:
                assert "track_id" in rec
                assert "track_name" in rec
                assert "artist" in rec
                assert "valence" in rec
                assert "energy" in rec
                assert "album_image_url" in rec

    def test_sad_mood_recommendations(self, real_recommendation_engine, app):
        """Test getting recommendations for a sad mood."""
        with app.test_request_context():
            # Set up session data
            session['logged_in'] = True

            # Test user preferences
            preferences = {
                "artists": ["Sad Artist"],
                "genres": ["Rock"],
                "popularity": 60,
                "instrumentalness": 0.3
            }

            # Get recommendations for a sad mood
            recommendations = real_recommendation_engine.get_recommendations(
                valence=0.2,  # Sad
                energy=0.3,   # Low energy
                goal="stay_with_me",
                preferences=preferences,
                recommended_ids=[]
            )

            # Verify we got recommendations
            assert len(recommendations) > 0

            # Verify the recommendations have the expected structure
            for rec in recommendations:
                assert "track_id" in rec
                assert "track_name" in rec
                assert "artist" in rec
                assert "valence" in rec
                assert "energy" in rec
                assert "album_image_url" in rec

    def test_energetic_mood_recommendations(self, real_recommendation_engine, app):
        """Test getting recommendations for an energetic mood."""
        with app.test_request_context():
            # Set up session data
            session['logged_in'] = True

            # Test user preferences
            preferences = {
                "artists": ["Energy Artist"],
                "genres": ["Dance"],
                "popularity": 75,
                "instrumentalness": 0.05
            }

            # Get recommendations for an energetic mood
            recommendations = real_recommendation_engine.get_recommendations(
                valence=0.6,  # Moderately happy
                energy=0.9,   # Very energetic
                goal="pump_me_up",
                preferences=preferences,
                recommended_ids=[]
            )

            # Verify we got recommendations
            assert len(recommendations) > 0

            # Verify the recommendations have the expected structure
            for rec in recommendations:
                assert "track_id" in rec
                assert "track_name" in rec
                assert "artist" in rec
                assert "valence" in rec
                assert "energy" in rec
                assert "album_image_url" in rec

    def test_recommendations_with_previous_tracks(self, real_recommendation_engine, app):
        """Test getting recommendations with previously recommended tracks."""
        with app.test_request_context():
            # Set up session data
            session['logged_in'] = True

            # Test user preferences
            preferences = {
                "artists": ["Happy Artist", "Energy Artist"],
                "genres": ["Pop", "Dance"],
                "popularity": 75,
                "instrumentalness": 0.1
            }

            # Previously recommended tracks
            previous_recommendations = ["spotify:track:1", "spotify:track:3"]

            # Get recommendations excluding previously recommended tracks
            recommendations = real_recommendation_engine.get_recommendations(
                valence=0.7,
                energy=0.7,
                goal="lift_me_up",
                preferences=preferences,
                recommended_ids=previous_recommendations
            )

            # Verify we got recommendations
            assert len(recommendations) > 0

            # Verify none of the recommendations are in the previously recommended list
            for rec in recommendations:
                assert rec["track_id"] not in previous_recommendations

            # Now test with all tracks in the previously recommended list
            # This should return an empty list since no tracks are available
            all_tracks = ["spotify:track:1", "spotify:track:2", "spotify:track:3", "spotify:track:4",
                          "spotify:track:5", "spotify:track:6", "spotify:track:7", "spotify:track:8",
                          "spotify:track:9", "spotify:track:10", "spotify:track:11", "spotify:track:12",
                          "spotify:track:13", "spotify:track:14", "spotify:track:15"]
            empty_recommendations = real_recommendation_engine.get_recommendations(
                valence=0.7,
                energy=0.7,
                goal="lift_me_up",
                preferences=preferences,
                recommended_ids=all_tracks
            )

            # Verify we got an empty list
            assert len(empty_recommendations) == 0


# This allows running the tests directly
if __name__ == '__main__':
    pytest.main(['-xvs', __file__])
