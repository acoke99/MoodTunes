import json
from flask import render_template, request, redirect, jsonify, session, flash
from app_factory import AppFactory
from util import Util


# Create the Flask app
factory = AppFactory()
app = factory.get_app()


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
        session['valence'] = float(request.form['valence']) / 100
        session['energy'] = float(request.form['energy']) / 100
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
        try:
            app.user_store.load_preferences(session.get('user_id'))
        except Exception as e:
            flash(str(e), "error")
            return render_template('goal.html')

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

    # Handle POST request
    if request.method == 'POST':
        # Get preferences from form submission
        prefs = {
            'artists': request.form.getlist('artists'),
            'genres': request.form.getlist('genres'),
            'popularity': int(request.form.get('popularity')),
            'instrumentalness': float(request.form.get('instrumentalness'))
        }

        # Save user preferences
        try:
            app.user_store.save_preferences(session.get('user_id'), prefs)
        except Exception as e:
            flash(str(e), "error")
            return render_template('preferences.html', source=source, preferences=prefs)

        # Redirect to recommendations page if source is preferences page or not specified
        if not source or source == 'None' or source == '/preferences':
            return redirect('/recommendations')
        elif Util.is_safe_path(source):
            return redirect(source)

    # Load preferences from database if required.
    try:
        app.user_store.load_preferences(session.get('user_id'))
        prefs = session.get('preferences')
    except Exception as e:
        flash(str(e), "error")

    # Render preferences page
    return render_template('preferences.html', source=source, preferences=prefs)


# Get music recommendations
@app.route('/recommendations')
def recommendations():
    # Check if user is logged in
    if not session.get('logged_in'):
        return redirect('/')

    # Get session variables
    valence = session.get('valence')  # User's valence (0-100)
    energy = session.get('energy')  # User's energy (0-100)
    goal = session.get('goal')  # User's goal (lift_me_up, chill_me_out, etc.)
    preferences = session.get('preferences')  # User's preferences (artists, genres, popularity, instrumental)
    recommended_ids = session.get('recommended_ids', [])  # List of recommended track IDs

    # Validate session variables
    if not valence or not energy:
        return redirect('/mood')
    elif not goal:
        return redirect('/goal')
    elif not preferences:
        return redirect('/preferences')

    # Get recommendations and render page
    recommendations = app.recommender.get_recommendations(valence, energy, goal, preferences, recommended_ids)

    # Store recommended track IDs in the session
    new_ids = [track['track_id'] for track in recommendations]
    session['recommended_ids'] = recommended_ids + new_ids

    # Render recommendations page
    return render_template('recommendations.html', recommendations=recommendations)


# Handle Spotify login
@app.route('/login')
def login():
    return redirect(app.spotify_service.get_auth_url())


# Handle Spotify callback
@app.route('/callback')
def callback():
    # Get callback parameters
    state = request.args.get('state')
    code = request.args.get('code')

    try:
        # Call client method to handle callback
        app.spotify_service.handle_callback(state, code)

        # Get user ID
        user_id = app.spotify_service.get_user_id()
        session['user_id'] = user_id

        # Initialise user
        app.user_store.initialise_user(user_id)

    except Exception as e:
        flash(str(e), "error")
        return redirect('/')

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
    return json.dumps(app.track_data.get_all_artists(), separators=(',', ':'))


# Add tracks to queue.
# Expects a list of Spotify track URIs in the request body.
@app.route('/api/queue', methods=['POST'])
def queue():
    try:
        # Get track URIs from request
        uris = request.get_json(silent=True)
        if not uris:
            return jsonify({"error": "No track URIs provided."}), 400

        # Add tracks to queue
        success = app.spotify_service.queue_tracks(uris)
        if success:
            return jsonify({"message": "The selected tracks have been added to your queue."}), 200
        else:
            return jsonify({"error": "Failed to add tracks to queue."}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Pause playback
@app.route('/api/pause', methods=['POST'])
def pause_track():
    try:
        app.spotify_service.pause_track()
        return '', 204
    except Exception:
        return '', 500


# Resume playback
@app.route('/api/play', methods=['POST'])
def play_track():
    try:
        app.spotify_service.play_track()
        return '', 204
    except Exception:
        return '', 500


# Skip to next track
@app.route('/api/next', methods=['POST'])
def next_track():
    try:
        app.spotify_service.next_track()
        return '', 204
    except Exception:
        return '', 500


# Skip to previous track
@app.route('/api/previous', methods=['POST'])
def previous_track():
    try:
        app.spotify_service.previous_track()
        return '', 204
    except Exception:
        return '', 500


# Start the Flask server (only when running this script directly)
if __name__ == '__main__':
    app.run(debug=True)
