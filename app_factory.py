import os
import secrets
import sqlite3 as sql
from flask import Flask, g
from flask_session import Session
from spotify_service import SpotifyService
from datetime import timedelta
from track_data import TrackData
from recommend import RecommendationEngine
from user_store import UserStore


# Factory class for creating the Flask app
class AppFactory:
    def __init__(self):
        # Initialize the Flask application
        self.app = Flask(__name__, instance_relative_config=True)

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
        track_data.load_csv('datasets/track_data.csv')

        # Initialise recommender
        recommender = RecommendationEngine(track_data, spotify_service)

        # Initialize MoodTunes database
        self.app.db_path = os.path.join(self.app.instance_path, 'moodtunes.db')
        self.app.db_schema_path = 'sql/schema.sql'
        self._initialise_db()

        # Create instance of user store
        user_store = UserStore(self.app)

        # Attach services to the app
        self.app.spotify_service = spotify_service
        self.app.track_data = track_data
        self.app.recommender = recommender
        self.app.user_store = user_store
        self.app.get_db = self.get_db
        self.app.close_db = self.close_db

        # Register the database teardown function
        self.app.teardown_appcontext(self.close_db)

    # Get the Flask app
    def get_app(self):
        return self.app

    # Get the database connection
    def get_db(self):
        # Reuse the database connection from the global object.
        # Create a new connection if it doesn't exist.
        if 'db' not in g:
            # Connect to the database
            g.db = sql.connect(self.app.db_path)
            # Return rows as dictionaries for easier column access
            g.db.row_factory = sql.Row
        return g.db

    # Close the database connection
    def close_db(self, e=None):
        # Remove the database connection from the global object.
        # Close the connection if it exists.
        db = g.pop('db', None)
        if db is not None:
            db.close()

    # Initialise the database
    def _initialise_db(self):
        try:
            # Ensure the database directory exists
            os.makedirs(os.path.dirname(self.app.db_path), exist_ok=True)

            # If the database doesn't exist, create it from the schema SQL file
            if not os.path.exists(self.app.db_path):
                print(f"Creating database from {self.app.db_schema_path}...")
                with sql.connect(self.app.db_path) as conn:
                    with open(self.app.db_schema_path, 'r') as f:
                        conn.executescript(f.read())
                    conn.commit()
        except Exception as e:
            raise RuntimeError(e)
