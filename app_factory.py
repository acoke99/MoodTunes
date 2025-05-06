import json
import logging
import os
import secrets
import sqlite3 as sql
import time

from datetime import timedelta
from flask import Flask, g
from flask_session import Session
from flask_talisman import Talisman
from flask_wtf import CSRFProtect
from logging.handlers import RotatingFileHandler
from recommend import RecommendationEngine
from spotify_service import SpotifyService
from track_data import TrackData
from user_store import UserStore


# Factory class for creating the Flask app
class AppFactory:
    def __init__(self):
        # Initialize the Flask application
        self.app = Flask(__name__, instance_relative_config=True)

        # Get the Flask environment (development or production)
        self.app.env = os.environ.get('FLASK_ENV')

        # Setup logging
        self._setup_logging()

        # Set the secret key used for:
        # 1. Session security - encrypts session data
        # 2. CSRF token generation - creates unique tokens for form protection
        self.app.secret_key = os.environ.get('FLASK_SECRET_KEY')
        if not self.app.secret_key:
            if self.app.env == 'development':
                self.app.secret_key = secrets.token_hex(16)
            else:
                raise RuntimeError("FLASK_SECRET_KEY is not set")

        # Set cache settings
        if self.app.env == 'development':
            self.app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0  # No caching
        else:
            self.app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 31536000  # Cache static files for 1 year

        # Set session settings
        self.app.config['SESSION_COOKIE_NAME'] = 'MoodTunesAppSession'  # Name of the session cookie
        self.app.config["SESSION_TYPE"] = "filesystem"  # Store sessions server-side
        self.app.config["SESSION_PERMANENT"] = True  # Enable session expiration
        self.app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)  # Auto-expire after 30 minutes

        # Configure sessions for the app
        Session(self.app)

        # Cleanup expired sessions
        self._cleanup_sessions()

        # Initialize CSRF protection for the app
        self.app.csrf = CSRFProtect(self.app)

        # Load CSP settings from JSON
        if self.app.env == 'development':
            csp_file = "config/csp_dev.json"
        else:
            csp_file = "config/csp_prod.json"

        with open(csp_file) as f:
            csp_settings = json.load(f)

        # Apply CSP settings to the app
        self.app.csp = Talisman(self.app, content_security_policy=csp_settings)

        # Load Spotify credentials from environment
        sp_client_id = os.environ.get('SPOTIFY_CLIENT_ID')
        sp_client_secret = os.environ.get('SPOTIFY_CLIENT_SECRET')
        sp_redirect_uri = os.environ.get('SPOTIFY_REDIRECT_URI')

        if not all([sp_client_id, sp_client_secret, sp_redirect_uri]):
            raise RuntimeError("Missing Spotify credentials.")

        # Initialize Spotify service
        spotify_service = SpotifyService(
            client_id=sp_client_id,
            client_secret=sp_client_secret,
            redirect_uri=sp_redirect_uri
        )

        # Load and prepare track data
        track_data = TrackData()
        track_data.load_csv('datasets/track_data.csv')

        # Initialise recommender
        recommender = RecommendationEngine(track_data, spotify_service)

        # Create instance of user store
        user_store = UserStore(self.app)

        # Initialize MoodTunes database
        self.app.db_path = os.path.join(self.app.instance_path, 'moodtunes.db')
        self.app.db_schema_path = 'sql/schema.sql'
        self._initialise_db()

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

    # Setup logging
    def _setup_logging(self):
        os.makedirs(self.app.instance_path, exist_ok=True)
        log_path = os.path.join(self.app.instance_path, "app.log")

        handler = RotatingFileHandler(
            log_path, maxBytes=10240, backupCount=5, encoding="utf-8"
        )
        handler.setLevel(logging.INFO)
        handler.setFormatter(logging.Formatter(
            "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
        ))

        self.app.logger.setLevel(logging.INFO)
        self.app.logger.addHandler(handler)
        self.app.logger.info("Application started.")

    # Cleanup expired sessions
    def _cleanup_sessions(self):
        session_dir = self.app.config.get("SESSION_FILE_DIR", os.path.join(os.getcwd(), "flask_session"))
        lifetime = self.app.permanent_session_lifetime
        if isinstance(lifetime, timedelta):
            lifetime_seconds = lifetime.total_seconds()
        else:
            lifetime_seconds = int(lifetime)
        now = time.time()
        for filename in os.listdir(session_dir):
            file_path = os.path.join(session_dir, filename)
            if os.path.isfile(file_path):
                file_mtime = os.path.getmtime(file_path)
                if now - file_mtime > lifetime_seconds:
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        print(f"Failed to remove expired session file {file_path}: {e}")

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
