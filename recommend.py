import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from spotify_service import SpotifyService
from track_data import TrackData


# Recommendation engine class
class RecommendationEngine:
    def __init__(self, track_data: TrackData, spotify_service: SpotifyService):
        self.df = track_data.df
        self.spotify_service = spotify_service
        self.scaler = track_data.scaler
        self.taste_features = track_data.taste_features

        # Boost factor for preferred artists
        self.artist_boost_factor = 1.2

        # Weights for mood and non-mood features
        self.weights = {
            "mood": 0.5,
            "non_mood": 0.5
        }

    # Get recommendations based on mood and user preferences
    def get_recommendations(self,
                            valence: float,
                            energy: float,
                            goal: str,
                            preferences: dict,
                            recommended_ids=list[str] | None) -> list[dict]:

        # Ensure the track database has been loaded
        if self.df is None:
            raise ValueError("Track database not loaded.")

        # Filter dataset by genre
        if preferences['genres']:
            filtered_df = self.df[self.df['genre'].isin(preferences['genres'])].copy()
        else:
            filtered_df = self.df

        # If no tracks match the genre filter, return an empty list
        if filtered_df.empty:
            return []

        # Extract taste features (e.g. popularity, instrumentalness) from tracks for similarity comparison.
        # Mood features (valence, energy, goal) are processed separately.
        track_vectors = filtered_df[self.taste_features].values

        # Build and scale the user's taste vector
        user_vector = [preferences[f] for f in self.taste_features]
        user_vector_scaled = self.scaler.transform([user_vector])[0]

        # Compute cosine similarity between the user's taste vector and all track vectors
        similarity_matrix = cosine_similarity(track_vectors, [user_vector_scaled])
        similarity_scores = similarity_matrix.flatten()

        # Boost similarity scores for preferred artists.
        # Apply a small boost to tracks that match user's preferred artists.
        similarity_scores = self._apply_artist_boost(filtered_df, similarity_scores, preferences["artists"])

        # Adjust recommendations towards user's target mood.
        # Determine mood adjustments based on user's goal (e.g., lift me up, chill me out).
        target_mood = self._get_target_mood(goal, valence, energy)

        # Recommend songs by combining similarity and mood progression
        rec_df = self._recommend_songs(filtered_df, similarity_scores, valence,
                                       energy, target_mood, recommended_ids, top_n=10)

        # Format output for Spotify playback
        # Convert track IDs to Spotify URIs
        rec_df['uri'] = 'spotify:track:' + rec_df['track_id']

        # Get track information
        tracks = self.spotify_service.get_tracks(rec_df['track_id'].tolist())

        # Map track ID to image URL
        track_to_image = {
            track['id']: track['album']['images'][1]['url']
            for track in tracks if track['album']['images']
        }

        # Map image URLs back to the DataFrame by track ID
        rec_df['album_image_url'] = rec_df['track_id'].map(track_to_image)

        # Return the final list of recommendations as a list of dictionaries
        return rec_df.to_dict(orient='records')

    # Get target mood based on goal
    def _get_target_mood(self, goal: str, start_valence: float, start_energy: float) -> dict:
        # Target mood parameters:
        # - target_valence: target positivity (0.0 = sad, 1.0 = happy)
        # - target_energy: target energy level (0.0 = calm, 1.0 = energetic)
        target_mood = {}
        match goal:
            case "lift_me_up":
                target_mood = {"target_valence": 0.8, "target_energy": 0.65}
            case "chill_me_out":
                target_mood = {"target_valence": 0.7, "target_energy": 0.3}
            case "fire_me_up":
                target_mood = {"target_valence": 0.8, "target_energy": 0.8}
            case "keep_me_here":
                target_mood = {"target_valence": start_valence, "target_energy": start_energy}
            case "surprise_me" | _:
                target_mood = {"target_valence": 0.8, "target_energy": 0.6}
        return target_mood

    # Boost similarity scores if track artist matches user preference
    def _apply_artist_boost(self,
                            df: pd.DataFrame,
                            similarity_scores: np.ndarray,
                            preferred_artists: list[str]) -> np.ndarray:

        if preferred_artists:
            # Identify matching artists
            artist_matches = df['artist'].isin(preferred_artists)

            # Count number of matches
            count_matches = artist_matches.sum()

            # Generate random boost factors for matching artists (from 1 to artist_boost_factor)
            random_boosts = np.ones(len(df))
            random_boosts[artist_matches.values] = np.random.uniform(1, self.artist_boost_factor, count_matches)

            # Apply boost to matching scores
            similarity_scores *= random_boosts

        return similarity_scores

    # Recommend songs by combining taste similarity and progressive mood adjustment
    def _recommend_songs(self,
                         df: pd.DataFrame,
                         similarity_scores: np.ndarray,
                         start_valence: float,
                         start_energy: float,
                         target_mood: dict,
                         recommended_ids=list[str] | None,
                         top_n=10) -> list[dict]:

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

        # Calculate per-step mood adjustments
        val_adj = (target_mood['target_valence'] - start_valence) / top_n
        nrg_adj = (target_mood['target_energy'] - start_energy) / top_n

        # Generate top_n song recommendations
        for step in range(top_n):
            # Gradually adjust target mood at each recommendation step
            step_valence = start_valence + val_adj * step
            step_energy = start_energy + nrg_adj * step
            step_vector = np.array([step_valence, step_energy])

            # Calculate the Euclidean distance between the track mood and the current step's target mood
            distances = np.linalg.norm(track_vectors - step_vector, axis=1)

            # Normalize distances to compute mood closeness (1 = exact match, 0 = no closeness).
            # Assumes valence and energy are both in [0, 1], so the maximum possible distance is sqrt(2).
            closeness = np.clip(1 - (distances / np.sqrt(2)), 0, 1)

            # Combine scores for mood and non-mood features
            combined_scores = closeness * self.weights['mood'] + similarity_scores * self.weights['non_mood']

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

        # Return recommendations as a DataFrame
        return pd.DataFrame(recommended_tracks)
