import os
import secrets
from flask import Flask
from flask_session import Session
from spotify_service import SpotifyService
from datetime import timedelta
from track_data import TrackData
from recommend import RecommendationEngine


# Factory class for creating the Flask app
class AppFactory:
    def __init__(self):
        # Initialize the Flask application
        self.app = Flask(__name__)

        # Set the secret key used for:
        # 1. Session security - encrypts session data
        # 2. CSRF token generation - creates unique tokens for form protection
        self.app.secret_key = os.environ.get('FLASK_SECRET_KEY') or secrets.token_hex(16)
        if not os.environ.get('FLASK_SECRET_KEY'):
            self.app.logger.warning("Using generated secret key - set FLASK_SECRET_KEY in production")

        # Configure sessions for Flask application.
        # This helps prevent session hijacking and session fixation.
        self.app.config['SESSION_COOKIE_NAME'] = 'MoodTunesAppSession'  # Name of the session cookie
        self.app.config["SESSION_TYPE"] = "filesystem"  # Store sessions server-side
        self.app.config["SESSION_PERMANENT"] = True  # Enable session expiration
        self.app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)  # Auto-expire after 30 minutes
        Session(self.app)

        # Load Spotify credentials from environment
        client_id = os.environ.get('SPOTIFY_CLIENT_ID')
        client_secret = os.environ.get('SPOTIFY_CLIENT_SECRET')
        redirect_uri = os.environ.get('SPOTIFY_REDIRECT_URI')

        if not all([client_id, client_secret, redirect_uri]):
            raise RuntimeError("Missing Spotify credentials.")

        # Initialize Spotify service
        spotify_service = SpotifyService(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri
        )

        # Load and prepare track data
        track_data = TrackData()
        track_data.load_csv('static/dataset/track_data.csv')

        # Initialise recommender
        recommender = RecommendationEngine(track_data, spotify_service)

        # Attach services to the app
        self.app.spotify_service = spotify_service
        self.app.track_data = track_data
        self.app.recommender = recommender

    # Get the Flask app
    def get_app(self):
        return self.app
