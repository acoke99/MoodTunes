import spotipy
import secrets
from flask import session
from spotipy import Spotify, SpotifyException
from spotipy.oauth2 import SpotifyOAuth
from exceptions import AuthenticationException, ApplicationException


# Spotify service class
class SpotifyService:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
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
    def handle_callback(self, oauth_state: str, oauth_code: str) -> None:
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
    def get_client(self) -> Spotify:
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

    # Get Spotify user ID
    def get_user_id(self) -> str:
        # Get Spotify client
        spotify = self.get_client()

        # Get user ID
        user = spotify.current_user()
        return user['id']

    # Get information about a list of tracks
    def get_tracks(self, track_ids: list[str]) -> list[dict]:
        # Get Spotify client
        spotify = self.get_client()

        # Get tracks
        tracks = spotify.tracks(track_ids)

        # Return tracks
        return tracks['tracks']

    # Get active device
    def get_active_device(self, spotify: Spotify | None = None) -> str:
        # Get Spotify client
        if spotify is None:
            spotify = self.get_client()

        # Get active devices
        devices = spotify.devices()
        num_devices = len(devices['devices'])
        if num_devices == 0:
            raise ApplicationException(
                "No active Spotify device found. Please open Spotify on one of your devices and try again.")

        # Get first device ID
        device_id = devices['devices'][0]['id']
        return device_id

    # Add tracks to queue
    def queue_tracks(self, uris: list[str]) -> bool:
        spotify = self.get_client()
        device_id = self.get_active_device(spotify)
        try:
            spotify.start_playback(device_id, None, uris)
        except SpotifyException as e:
            raise ApplicationException("There was an error adding the tracks to the queue.", details=str(e))
        return True

    # Pause playback on the active device
    def pause_track(self) -> bool:
        spotify = self.get_client()
        device_id = self.get_active_device(spotify)
        try:
            spotify.pause_playback(device_id=device_id)
        except SpotifyException as e:
            raise ApplicationException("There was an error pausing the track.", details=str(e))
        return True

    # Resume playback on the active device
    def play_track(self) -> bool:
        spotify = self.get_client()
        device_id = self.get_active_device(spotify)
        try:
            spotify.start_playback(device_id=device_id)
        except SpotifyException as e:
            raise ApplicationException("There was an error resuming the track.", details=str(e))
        return True

    # Skip to the next track on the active device
    def next_track(self) -> bool:
        spotify = self.get_client()
        device_id = self.get_active_device(spotify)
        try:
            spotify.next_track(device_id=device_id)
        except SpotifyException as e:
            raise ApplicationException("There was an error skipping to the next track.", details=str(e))
        return True

    # Skip to the previous track on the active device
    def previous_track(self) -> bool:
        spotify = self.get_client()
        device_id = self.get_active_device(spotify)
        try:
            spotify.previous_track(device_id=device_id)
        except SpotifyException as e:
            raise ApplicationException("There was an error skipping to the previous track.", details=str(e))
        return True

    # Get user's top artists
    def get_top_artists(self) -> list[str]:
        spotify = self.get_client()
        try:
            top_artists = spotify.current_user_top_artists(limit=10)
            artist_names = [artist['name'] for artist in top_artists['items']]
            return artist_names
        except SpotifyException as e:
            raise ApplicationException("There was an error retrieving your top artists.", details=str(e))
