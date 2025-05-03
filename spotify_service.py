import spotipy
import secrets
from flask import session
from spotipy import Spotify, SpotifyException
from spotipy.oauth2 import SpotifyOAuth


# Authentication exception class
class AuthenticationException(Exception):
    pass


# Application exception class
class ApplicationException(Exception):
    pass


# Spotify service class
class SpotifyService:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str) -> None:
        # Spotify OAuth setup
        self.oauth = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope="user-read-playback-state user-modify-playback-state user-top-read",
            cache_handler=spotipy.cache_handler.FlaskSessionCacheHandler(session),
            show_dialog=True
        )

    # Get Spotify authorisation URL
    def get_auth_url(self) -> str:
        # Generate a secure random state value for CSRF protection
        state: str = str(secrets.token_urlsafe(16))
        session['oauth_state'] = state

        # Return URL
        return self.oauth.get_authorize_url(state=state)

    # Handles Spotify callback
    def handle_callback(self, oauth_state: str, oauth_code: str):
        # Validate the state parameter to prevent CSRF
        if not oauth_state or oauth_state != session.get('oauth_state'):
            raise AuthenticationException("Invalid state parameter. Please try logging in again.")

        # Get access token using OAuth authorisation code
        token_info = self.oauth.get_access_token(oauth_code)
        if not token_info:
            raise AuthenticationException("Failed to retrieve access token.")

        # Store token in session
        session['token_info'] = token_info
        session['logged_in'] = True
        token_info = self.oauth.get_access_token(oauth_code)

    # Get Spotify client
    def get_client(self):
        # Get token from session
        token_info = session.get('token_info', None)
        if not token_info:
            raise AuthenticationException("You are not logged in. Please log in to continue.")

        # Refresh the token if needed
        if self.oauth.is_token_expired(token_info):
            token_info = self.oauth.refresh_access_token(token_info['refresh_token'])
            session['token_info'] = token_info

        # Create Spotify client
        return Spotify(auth=token_info['access_token'])

    # Get information about a list of tracks
    def get_tracks(self, track_ids: list[str]) -> list[dict]:
        # Get Spotify client
        spotify = self.get_client()

        # Get tracks
        tracks = spotify.tracks(track_ids)

        # Return tracks
        return tracks['tracks']

    # Add tracks to queue
    def queue_tracks(self, uris: list[str]) -> bool:
        # Get Spotify client
        spotify = self.get_client()

        # Get active devices
        devices = spotify.devices()
        num_devices = len(devices['devices'])
        if num_devices == 0:
            raise ApplicationException(
                "No active Spotify device found. Please open Spotify on one of your devices and try again.")

        # Get first device ID
        device_id = devices['devices'][0]['id']

        # Start playback of selected tracks on device
        try:
            spotify.start_playback(device_id, None, uris)
        except SpotifyException as e:
            raise ApplicationException(f"Spotify error: {str(e)}")

        # Return
        return True
