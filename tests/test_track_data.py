import pytest
import pandas as pd
from track_data import TrackData
from sklearn.preprocessing import StandardScaler


class TestTrackData:
    def test_init(self):
        td = TrackData()
        assert td.df is None
        assert isinstance(td.scaler, StandardScaler)
        assert td.taste_features == ["popularity", "instrumentalness"]

    def test_load_csv_success(self, tmp_path):
        # Prepare a CSV file in a temp directory
        csv_content = (
            "track_id,track_name,artist_name,new_genre,valence,energy,popularity,instrumentalness\n"
            "1,Song A,Artist X,Pop,0.5,0.6,80,0.1\n"
            "2,Song B,Artist Y,Rock,0.8,0.7,65,0.3\n"
        )
        csv_path = tmp_path / "tracks.csv"
        csv_path.write_text(csv_content)

        td = TrackData()
        td.load_csv(str(csv_path))

        # Check DataFrame loaded
        assert isinstance(td.df, pd.DataFrame)
        assert list(td.df.columns) == [
            "track_id", "track_name", "artist", "genre",
            "valence", "energy", "popularity", "instrumentalness"
        ]
        assert len(td.df) == 2
        assert td.df.loc[0, "track_name"] == "Song A"
        assert td.df.loc[1, "artist"] == "Artist Y"

    def test_load_csv_missing_column(self, tmp_path):
        # Missing 'popularity' column
        csv_content = (
            "track_id,track_name,artist_name,new_genre,valence,energy,instrumentalness\n"
            "1,Song A,Artist X,Pop,0.5,0.6,0.1\n"
        )
        csv_path = tmp_path / "bad_tracks.csv"
        csv_path.write_text(csv_content)

        td = TrackData()
        with pytest.raises(ValueError):
            td.load_csv(str(csv_path))

    def test_load_csv_invalid_path(self):
        td = TrackData()
        with pytest.raises(FileNotFoundError):
            td.load_csv("nonexistent_file.csv")

    def test_get_all_artists_empty(self):
        td = TrackData()
        # Should return empty list if df is None
        assert td.get_all_artists() == []

    def test_get_all_artists_populated(self, tmp_path):
        csv_content = (
            "track_id,track_name,artist_name,new_genre,valence,energy,popularity,instrumentalness\n"
            "1,Song A,Artist X,Pop,0.5,0.6,80,0.1\n"
            "2,Song B,Artist Y,Rock,0.8,0.7,65,0.3\n"
            "3,Song C,Artist X,Pop,0.4,0.5,90,0.2\n"
            "4,Song D,,Jazz,0.6,0.4,70,0.3\n"  # Null artist
        )
        csv_path = tmp_path / "tracks.csv"
        csv_path.write_text(csv_content)

        td = TrackData()
        td.load_csv(str(csv_path))
        artists = td.get_all_artists()
        # Should return unique, sorted, non-null artists
        assert artists == ["Artist X", "Artist Y"]
