# MoodTunes

**MoodTunes** is a mood-aware music recommendation web app that uses basic machine learning techniques and Spotify integration to suggest songs based on the user's mood and preferences. It helps listeners discover music that matches how they feel—or how they want to feel.

## 🎧 Background

Traditional music recommendation systems rely heavily on user history, genre preferences, or popularity trends. These approaches often overlook a key influence: **emotional state**. MoodTunes bridges that gap by incorporating the listener’s **valence** (positivity) and **energy** (level of alertness) to recommend music that aligns with or gradually shifts their mood—an idea inspired by music therapy.

## 🧠 Datasets

Two Kaggle datasets were used to build the core track database:

- **Primary dataset**:  
  📁 `spotify_data.csv` from ["Spotify 1M Tracks"](https://www.kaggle.com/datasets/amitanshjoshi/spotify-1million-tracks/data)  
  Used as the main dataset for filtering and recommending tracks based on mood and preferences.

- **Supporting dataset**:  
  📁 `artists.csv` from ["Spotify Dataset 1921–2020 (600k Tracks)"](https://www.kaggle.com/datasets/yamaerenay/spotify-dataset-19212020-600k-tracks)  
  Used to **remap and supplement genre information** by linking artist-level genre tags to tracks.

## 🤖 Recommendation Logic

Users enter their **current mood** and select a **goal** (e.g., “I want to feel happy”), which is translated into a **target mood** (valence and energy). The system uses this along with user preferences (genres, artists, track features) to compute similarity scores and recommend a sequence of tracks that reflect or gently transition toward the desired emotional state.

User preferences are stored during the session to improve the user experience. Preferences are saved, but the user ID is hashed to ensure no personally identifiable information is stored.

Two Jupyter notebooks explain the recommendation algorithm in detail:

- `basic recommendation algorithm.ipynb`: Matches songs to the user’s current mood using cosine similarity and nearest-neighbour techniques.
- `final recommendation algorithm.ipynb`: Recommends a sequence of songs that gradually shift the mood toward a target emotional state, taking user preferences into account.

## 🔍 Features

- 🎛️ Mood input sliders for valence and energy
- 🎯 "I want to feel..." goal selection to influence target mood
- 🎵 Artist and genre preference filtering
- 🧠 Intelligent, progressive mood-shifting recommendations
- 🔒 No personally identifiable data stored beyond session
- 🎶 Queue and play tracks directly on your Spotify account
- 🖥️ Clean, responsive UI built with HTML, CSS, JS, and Flask

## 🌍 Live App

You can try the live version of the app here:  
🔗 https://moodtunes-acoke99.pythonanywhere.com/

## ⚙️ Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd MoodTunes
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate   # On Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up a Spotify developer app and environment variables
   - Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/) and log in.
   - Click **"Create an App"**, then provide a name and description.
   - In the app settings, add a redirect URI (e.g. `http://localhost:5000/callback`) under **Edit Settings > Redirect URIs** and save.
   - Copy your **Client ID** and **Client Secret** from the app dashboard.

   Create a `.env` file in your project root (or export the variables) with the following:

```env
SPOTIPY_CLIENT_ID=your_client_id
SPOTIPY_CLIENT_SECRET=your_client_secret
SPOTIPY_REDIRECT_URI=http://localhost:5000/callback
FLASK_SECRET_KEY=your_secret_key
FLASK_ENV=development
```

For more info, see the [Spotify Web API documentation](https://developer.spotify.com/documentation/web-api).

5. Add `spotify_data.csv` and `artists.csv` to the datasets folder. Then run the `data_wrangling.ipynb` Jupyter notebook to generate the final dataset, `track_data.csv`, used by the recommendation engine.

6. Run the app
```
flask run
```

## 🚀 Usage

1. Start the app and open http://localhost:5000/
2. Log in with your Spotify account
3. Enter your current valence and energy
4. Choose your mood goal
5. Optionally select preferred artists and genres
6. Submit to view recommendations and queue them to Spotify

## 📁 Project Structure

```
├── datasets/               # Data files used for recommendations  
├── notebooks/              # Jupyter notebooks for data wrangling and exploration  
├── sql/                    # SQL script for database setup
├── static/                 # Static files (CSS, JS, images)
├── templates/              # HTML templates (Jinja2)
├── app.py                  # Main Flask application
├── app_factory.py          # App factory and configuration
├── exceptions.py           # Custom exception classes for error handling
├── recommend.py            # Recommendation engine logic
├── requirements.txt        # Python dependencies
├── spotify_service.py      # Spotify API integration
├── track_data.py           # Track data loading and processing
├── user_store.py           # Handles user data and session management
├── util.py                 # Utility functions
```

## 📦 Dependencies

Key libraries:

- Flask
- Spotipy – Python client for the Spotify Web API
- pandas, numpy, scikit-learn
- flask-session, Flask-CORS, Flask-WTF, Flask-Talisman, Flask-CSP
- bleach

See `requirements.txt` for the full list.

## 🔒 Privacy & Security

- Mood input and Spotify ID may be used temporarily to generate recommendations.
- Some user preferences are stored to improve your experience.
- No personally identifiable data is stored beyond your session.
- For privacy, use an incognito window and log out of Spotify when finished.
- Spotify authentication follows OAuth2 best practices.


## 📘 About This Project

This project was developed by **Aidan Choy** in 2025 as the Major Project for the **HSC Software Engineering course (NSW)**, meeting the requirements set by NESA in the official course outline:  
🔗 [HSC Software Engineering Course Overview](https://curriculum.nsw.edu.au/learning-areas/tas/software-engineering-11-12-2022/overview#course-structure-and-requirements-software_engineering_11_12_2022)

## 📄 License

This project is licensed under the terms of the LICENSE file.
