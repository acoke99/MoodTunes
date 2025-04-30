import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler

# Global variables for track database and scaler
track_df = None
scaler = None
taste_features = ["popularity", "instrumentalness"]


# Load and prepare the track dataset
def load_and_prepare_data(filepath):
    global track_df, scaler, taste_features

    # Select columns to load:
    # - track_id: Spotify track ID
    # - track_name: Track name
    # - artist_name: Artist name
    # - new_genre: Genre (Pop, Rock, etc.)
    # - valence: Positivity (0.0 = sad, 1.0 = happy)
    # - energy: Intensity (0.0 = calm, 1.0 = energetic)
    # - popularity: Popularity score (0 to 100)
    # - instrumentalness: How instrumental (0.0 = vocal, 1.0 = fully instrumental)
    usecols = ["track_id", "track_name", "artist_name", "new_genre",
               "valence", "energy", "popularity", "instrumentalness"]

    # Load track data
    track_df = pd.read_csv(
        filepath,
        usecols=usecols,
        dtype={'popularity': 'float64'}
    )

    # Rename columns
    track_df.rename(columns={'artist_name': 'artist', 'new_genre': 'genre'}, inplace=True)

    # Normalize taste features for similarity comparison (mean = 0, std = 1).
    # Ensures all features are on the same scale and contribute equally.
    scaler = StandardScaler()
    track_df.loc[:, taste_features] = scaler.fit_transform(track_df[taste_features].values)


# Get recommendations based on mood and user preferences
def get_recommendations(valence, energy, goal, preferences, recommended_ids=None):
    # Ensure the track database has been loaded
    if track_df is None:
        raise ValueError("Track database not loaded.")

    # Filter dataset by genre
    if preferences['genres']:
        filtered_df = track_df[track_df['genre'].isin(preferences['genres'])].copy()
    else:
        filtered_df = track_df

    # If no tracks match the genre filter, return an empty list
    if filtered_df.empty:
        return []

    # Extract taste features (e.g. popularity, instrumentalness) from tracks for similarity comparison.
    # Mood features (valence, energy, goal) are processed separately.
    track_vectors = filtered_df[taste_features].values

    # Build and scale the user's taste vector
    user_vector = [preferences[f] for f in taste_features]
    user_vector_scaled = scaler.transform([user_vector])[0]

    # Compute cosine similarity between the user's taste vector and all track vectors
    similarity_matrix = cosine_similarity(track_vectors, [user_vector_scaled])
    similarity_scores = similarity_matrix.flatten()

    # Boost similarity scores for preferred artists.
    # Apply a small boost to tracks that match user's preferred artists.
    similarity_scores = apply_artist_boost(filtered_df, similarity_scores, preferences["artists"])

    # Adjust recommendations towards user's target mood.
    # Determine mood adjustments based on user's goal (e.g., lift me up, chill me out).
    target_mood = get_target_mood(goal, valence, energy)

    # Recommend songs by combining similarity and mood progression
    rec_df = recommend_songs(filtered_df, similarity_scores, valence, energy, target_mood, recommended_ids, top_n=10)

    # Format output for Spotify playback
    # Convert track IDs to Spotify URIs
    rec_df['uri'] = 'spotify:track:' + rec_df['track_id']

    # Return the final list of recommendations as a list of dictionaries
    return rec_df.to_dict(orient='records')


# Get target mood based on goal
def get_target_mood(goal, start_valence, start_energy):
    # Target mood parameters:
    # - target_valence: target positivity (0.0 = sad, 1.0 = happy)
    # - target_energy: target energy level (0.0 = calm, 1.0 = energetic)
    # - valence_adjustment: % change toward target valence per song
    # - energy_adjustment: % change toward target energy per song
    target_mood = {}
    match goal:
        case "lift_me_up":
            target_mood = {"target_valence": 0.8, "target_energy": 0.65,
                           "valence_adjustment": 15, "energy_adjustment": 12}
        case "chill_me_out":
            target_mood = {"target_valence": 0.7, "target_energy": 0.3,
                           "valence_adjustment": 7, "energy_adjustment": -20}
        case "fire_me_up":
            target_mood = {"target_valence": 0.8, "target_energy": 0.8,
                           "valence_adjustment": 12, "energy_adjustment": 22}
        case "keep_me_here":
            target_mood = {"target_valence": start_valence, "target_energy": start_energy,
                           "valence_adjustment": 2, "energy_adjustment": 2}
        case "surprise_me" | _:
            target_mood = {"target_valence": 0.8, "target_energy": 0.6,
                           "valence_adjustment": 12, "energy_adjustment": 12}
    return target_mood


# Boost similarity scores if track artist matches user preference
def apply_artist_boost(df, similarity_scores, preferred_artists):
    boost_factor = 1.3

    if preferred_artists:
        # Identify matching artists
        artist_matches = df['artist'].isin(preferred_artists)

        # Apply boost to matching scores
        similarity_scores *= (artist_matches.values * (boost_factor - 1)) + 1

    return similarity_scores


# Recommend songs by combining taste similarity and progressive mood adjustment
def recommend_songs(df, similarity_scores, start_valence, start_energy, target_mood, recommended_ids=None, top_n=10):
    # Initialize variables
    recommended_tracks = []
    used_indices = set()

    # Filter out tracks already recommended if provided
    if recommended_ids is not None:
        mask = ~df['track_id'].isin(recommended_ids)
        df = df[mask].reset_index(drop=True)
        similarity_scores = np.asarray(similarity_scores)[mask.to_numpy()]

    # Extract valence and energy values from all tracks
    track_vectors = df[["valence", "energy"]].values

    # Define goal mood vector
    goal_vector = np.array([target_mood['target_valence'], target_mood['target_energy']])

    # Calculate per-step mood adjustments
    val_adj = target_mood['valence_adjustment'] / 100
    nrg_adj = target_mood['energy_adjustment'] / 100

    # Generate top_n song recommendations
    for step in range(top_n):
        # Gradually adjust target mood at each recommendation step
        step_valence = np.clip(start_valence + val_adj * step, 0, 1)
        step_energy = np.clip(start_energy + nrg_adj * step, 0, 1)
        step_vector = np.array([step_valence, step_energy])

        # Stop if the mood has reached the goal
        if np.linalg.norm(step_vector - goal_vector) < 0.01:
            break

        # Calculate the Euclidean distance between the track mood and the current step's target mood
        distances = np.linalg.norm(track_vectors - step_vector, axis=1)

        # Normalize distances to compute mood closeness (1 = exact match, 0 = no closeness).
        # Assumes valence and energy are both in [0, 1], so the maximum possible distance is sqrt(2).
        closeness = np.clip(1 - (distances / np.sqrt(2)), 0, 1)

        # Combine user taste similarity with mood closeness
        combined_scores = 0.6 * similarity_scores + 0.4 * closeness

        # Mask out tracks that have already been recommended
        if used_indices:
            combined_scores[list(used_indices)] = -np.inf

        # Exit if no valid tracks remain
        if np.all(combined_scores == -np.inf):
            break

        # Select best track for this step
        best_index = int(np.argmax(combined_scores))
        used_indices.add(best_index)

        # Add the selected track to recommendations
        recommended_tracks.append(df.iloc[best_index][["track_name", "artist", "track_id", "valence", "energy"]])

    # Fill remaining tracks using goal mood
    remaining_n = top_n - len(recommended_tracks)
    if remaining_n > 0:
        # Calculate the Euclidean distance between the track mood and the goal mood
        distances = np.linalg.norm(track_vectors - goal_vector, axis=1)

        # Calculate mood closeness
        closeness = np.clip(1 - (distances / np.sqrt(2)), 0, 1)

        # Combine user taste similarity with mood closeness
        combined_scores = 0.6 * similarity_scores + 0.4 * closeness

        # Mask out tracks that have already been recommended
        combined_scores[list(used_indices)] = -np.inf

        # Select top remaining tracks based on combined score
        top_indices = np.argpartition(combined_scores, -remaining_n)[-remaining_n:]
        top_indices = top_indices[np.argsort(combined_scores[top_indices])[::-1]]

        # Add remaining tracks to the recommendation list
        for idx in top_indices:
            used_indices.add(idx)
            recommended_tracks.append(df.iloc[idx][["track_name", "artist", "track_id", "valence", "energy"]])

    # Return recommendations as a DataFrame
    return pd.DataFrame(recommended_tracks)


# Get list of all artists in the dataset
def get_all_artists():
    if track_df is None:
        return []

    # Get unique artists from the dataset.
    # Remove any null values.
    artists = track_df['artist'].dropna().unique().tolist()

    # Sort artists alphabetically
    return sorted(artists, key=str.lower)
