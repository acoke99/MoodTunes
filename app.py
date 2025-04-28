from flask import Flask, render_template, request, redirect, jsonify, session, flash
from spotipy import Spotify, SpotifyException
from spotipy.oauth2 import SpotifyOAuth
from recommend import get_all_artists, get_recommendations
from flask_session import Session
from datetime import timedelta
from urllib.parse import urlparse

import spotipy
import secrets
import os

# Initialize the Flask application
app = Flask(__name__)

# Set the secret key used for:
# 1. Session security - encrypts session data
# 2. CSRF token generation - creates unique tokens for form protection
app.secret_key = os.environ.get('FLASK_SECRET_KEY') or secrets.token_hex(16)
if not os.environ.get('FLASK_SECRET_KEY'):
    app.logger.warning("Using generated secret key - set FLASK_SECRET_KEY in production")

# Configure sessions for Flask application.
# This helps prevent session hijacking and session fixation.
app.config['SESSION_COOKIE_NAME'] = 'MoodTunesAppSession'  # Name of the session cookie
app.config["SESSION_TYPE"] = "filesystem"  # Store sessions server-side
app.config["SESSION_PERMANENT"] = True  # Enable session expiration
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)  # Auto-expire after 30 minutes
Session(app)

# Spotify OAuth setup
SPOTIFY_CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = os.environ.get('SPOTIFY_REDIRECT_URI')

if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET or not SPOTIFY_REDIRECT_URI:
    raise RuntimeError("Missing Spotify client ID, client secret, or redirect URI.")

cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)

sp_oauth = SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope="user-read-playback-state user-modify-playback-state",
    cache_handler=cache_handler,
    show_dialog=True
)


# Route for home page
@app.route('/')
def home():
    # If user is logged in, redirect to mood page
    if session.get('logged_in'):
        return redirect('/mood')

    # Force session cookie to be set
    session['session_initialised'] = True

    # Render home page
    flash("For the best experience, run this app in a Private (Incognito) window. This avoids sharing your Spotify session with others.", "info")
    return render_template('index.html', home_page=True)


# Handle mood input
@app.route('/mood', methods=['GET', 'POST'])
def mood():
    # Check if user is logged in
    if not session.get('logged_in'):
        return redirect('/')

    # Handle form submission.
    # Redirect to goal page.
    if request.method == 'POST':
        session['valence'] = float(request.form['valence'])
        session['arousal'] = float(request.form['arousal'])
        return redirect('/goal')

    # Render mood page
    return render_template('mood_input.html')


# Handle goal input
@app.route('/goal', methods=['GET', 'POST'])
def goal():
    # Check if user is logged in
    if not session.get('logged_in'):
        return redirect('/')

    # Handle form submission.
    # If preferences are not set, redirect to preferences page.
    # If preferences are set, redirect to recommendations page.
    if request.method == 'POST':
        session['goal'] = request.form['goal']
        if not session.get('preferences'):
            return redirect('/preferences')
        else:
            return redirect('/recommendations')

    # Render goal page
    return render_template('goal.html')


# Handle user preferences
@app.route('/preferences', methods=['GET', 'POST'])
def preferences():
    # Check if user is logged in
    if not session.get('logged_in'):
        return redirect('/')

    # Get source from URL query or form parameters
    source = request.args.get('source') or request.form.get('source')

    # Handle form submission.
    # If preferences are set, redirect to recommendations page.
    if request.method == 'POST':
        # Get preferences from form
        preferences = {
            'artists': request.form.getlist('artists'),
            'genres': request.form.getlist('genres'),
            'popularity': request.form.get('popularity'),
            'instrumental': request.form.get('instrumental')
        }
        session['preferences'] = preferences

        # Redirect to recommendations page if source is preferences page or not specified
        if not source or source == 'None' or source == '/preferences':
            return redirect('/recommendations')
        elif is_safe_path(source):
            return redirect(source)

    # Render preferences page
    return render_template('preferences.html', source=source)


# Get music recommendations
@app.route('/recommendations')
def recommendations():
    # Check if user is logged in
    if not session.get('logged_in'):
        return redirect('/')

    # Get session variables
    valence = session.get('valence')
    arousal = session.get('arousal')
    goal = session.get('goal')
    preferences = session.get('preferences')

    # Validate session variables
    if not valence or not arousal:
        return redirect('/mood')
    elif not goal:
        return redirect('/goal')
    elif not preferences:
        return redirect('/preferences')

    # Get recommendations and render page
    recommendations = get_recommendations(valence, arousal, goal, preferences)
    return render_template('recommendations.html', recommendations=recommendations)


# Handle Spotify login
@app.route('/login')
def login():
    # Generate a secure random state value for CSRF protection
    state = str(secrets.token_urlsafe(16))
    session['oauth_state'] = state

    # Get Spotify authorisation URL and redirect
    auth_url = sp_oauth.get_authorize_url(state=state)
    return redirect(auth_url)


# Handle Spotify callback
@app.route('/callback')
def callback():
    # Validate the state parameter to prevent CSRF
    state = request.args.get('state')
    if not state or state != session.get('oauth_state'):
        flash("Invalid state parameter. Please try logging in again.", "error")
        return redirect('/')

    # Get access token using OAuth authorisation code
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)

    # Store token in session
    session['token_info'] = token_info
    session['logged_in'] = True

    # Redirect to mood page
    return redirect('/mood')


# Handle user logout
@app.route("/logout")
def logout():
    session.clear()
    return render_template('logout.html')


# Get list of artists
@app.route('/api/artists')
def artists():
    artists = get_all_artists()
    return jsonify(artists)


# Add tracks to queue.
# Expects a list of Spotify track URIs in the request body.
@app.route('/api/queue', methods=['POST'])
def queue():
    try:
        # Get Spotify client
        spotify = get_spotify_client()

        # Get track URIs from request
        uris = request.get_json(silent=True)
        if not uris:
            return jsonify({"message": "No track URIs provided."}), 400

        # Add tracks to queue
        devices = spotify.devices()
        num_devices = len(devices['devices'])
        if num_devices == 0:
            return jsonify({"error": "No active Spotify device found. Please open Spotify on one of your devices and try again."}), 400

        # Get first device ID
        device_id = devices['devices'][0]['id']

        # Start playback of selected tracks
        spotify.start_playback(device_id, None, uris)
        return jsonify({"message": "The selected tracks have been added to your queue."})

    except AuthenticationException as e:
        return jsonify({"error": str(e)}), 401
    except SpotifyException as e:
        return jsonify({"error": 'Spotify error: ' + str(e)}), e.http_status


def get_spotify_client():
    # Get token from session
    token_info = session.get('token_info', None)
    if not token_info:
        raise AuthenticationException("You are not logged in. Please log in to continue.")

    # Refresh the token if needed
    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session['token_info'] = token_info

    # Create Spotify client
    return Spotify(auth=token_info['access_token'])


# Custom exception for authentication errors
class AuthenticationException(Exception):
    pass


# Check if a path is safe
# Must be a relative path starting with '/' and no scheme (i.e., no http://)
def is_safe_path(path):
    return path and urlparse(path).scheme == '' and path.startswith('/')


# Run the app
if __name__ == "__main__":
    app.run(debug=True)
