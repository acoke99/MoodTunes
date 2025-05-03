import pandas as pd
from sklearn.preprocessing import StandardScaler


# Track data class
class TrackData:
    def __init__(self):
        self.df = None
        self.scaler = StandardScaler()
        self.taste_features = ["popularity", "instrumentalness"]

    # Load and prepare the track data from CSV file
    def load_csv(self, filepath: str) -> None:
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
        df = pd.read_csv(filepath, usecols=usecols, dtype={'popularity': 'float64'})

        # Rename columns
        df.rename(columns={'artist_name': 'artist', 'new_genre': 'genre'}, inplace=True)

        # Normalize taste features for similarity comparison (mean = 0, std = 1).
        # Ensures all features are on the same scale and contribute equally.
        df[self.taste_features] = self.scaler.fit_transform(df[self.taste_features])
        self.df = df

    # Get list of all artists in the dataset
    def get_all_artists(self) -> list[str]:
        if self.df is None:
            return []

        # Get unique artists from the dataset.
        # Remove any null values.
        artists = self.df['artist'].dropna().unique().tolist()

        # Sort artists alphabetically
        return sorted(artists, key=str.lower)
