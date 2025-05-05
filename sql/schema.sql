/* 
  Table: user
  Stores user records for the MoodTunes application.

  Fields:
    id               - Internal app user ID (autoincremented)
    spotify_user     - Hashed Spotify user ID for anonymized identification
    preferences_json - JSON string of the user's selected preferences
*/
CREATE TABLE `user` (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `spotify_user` TEXT NOT NULL,
    `preferences_json` TEXT
);