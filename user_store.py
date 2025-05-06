import hashlib
import json
from exceptions import ApplicationException
from flask import session
from util import Util


# User store class
class UserStore:
    def __init__(self, app):
        self.app = app

        # Store default user preferences
        self.default_preferences = {
            "artists": [],
            "genres": [],
            "popularity": 80,
            "instrumentalness": 0.2
        }

    # Check if a user exists
    def user_exists(self, user_id: str) -> bool:
        # Hash user ID
        hashed_user_id = self.hash_user_id(user_id)

        # Check if user exists in database
        conn = self.app.get_db()
        result = conn.execute(
            "SELECT * FROM user WHERE spotify_user = ?", (hashed_user_id,)
        ).fetchone()
        return result is not None

    # Create a new user in the database, if they don't already exist
    def initialise_user(self, user_id: str) -> None:
        # Check if user exists
        if self.user_exists(user_id):
            return

        # Hash user ID
        hashed_user_id = self.hash_user_id(user_id)

        # Insert user into database
        conn = self.app.get_db()
        try:
            conn.execute("INSERT INTO user (spotify_user) VALUES (?)", (hashed_user_id,))
            conn.commit()
        except Exception as e:
            raise ApplicationException("Your MoodTunes User account could not be created", str(e))

    # Load a user's preferences from the database
    def load_preferences(self, spotify_user: str, check_session: bool = True) -> None:
        # Check if user exists
        if not self.user_exists(spotify_user):
            raise ApplicationException("Your MoodTunes User account could not be found")

        # Check if preferences are already in session
        if check_session and session.get('preferences'):
            return

        # Hash user ID
        hashed_user_id = self.hash_user_id(spotify_user)

        # Get preferences from database.
        # These are stored as JSON, and must be parsed.
        prefs = None
        conn = self.app.get_db()
        try:
            result = conn.execute(
                "SELECT preferences_json FROM user WHERE spotify_user = ?", (hashed_user_id,)
            ).fetchone()
            if result and result['preferences_json'] is not None:
                prefs = json.loads(result['preferences_json'])
        except Exception:
            pass

        # If none are found, use default preferences.
        # Include artists from the user's listening history.
        if prefs is None:
            prefs = self.default_preferences.copy()
            try:
                prefs['artists'] = self.app.spotify_service.get_top_artists()
            except Exception:
                pass

        # Store preferences in session
        session['preferences'] = prefs

    # Saves a user's preferences to the database
    def save_preferences(self, spotify_user: str, preferences: dict) -> None:
        # Check if user exists
        if not self.user_exists(spotify_user):
            raise ApplicationException("Your MoodTunes User account could not be found")

        # Hash user ID
        hashed_user_id = self.hash_user_id(spotify_user)

        # Check that preferences is a dictionary
        if not isinstance(preferences, dict):
            raise ValueError("Invalid preferences format")

        # Sanitise data
        preferences = Util.sanitise_data(preferences)

        # Convert data to JSON
        try:
            preferences_json = json.dumps(preferences)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Invalid preferences format: {e}")

        # Update preferences in database
        conn = self.app.get_db()
        try:
            conn.execute(
                "UPDATE user SET preferences_json = ? WHERE spotify_user = ?",
                (preferences_json, hashed_user_id)
            )
            conn.commit()
        except Exception as e:
            raise ApplicationException("Your preferences could not be saved", str(e))

        # Store preferences in session
        session['preferences'] = preferences

    # Return a one-way SHA-256 hash of the given Spotify user ID
    def hash_user_id(self, user_id: str) -> str:
        return hashlib.sha256(user_id.encode('utf-8')).hexdigest()
