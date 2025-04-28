# Returns a list of recommended tracks (mocked for testing)
def get_recommendations(valence, arousal, goal, preferences):
    recommendations = [
        {
            "name": "Sky Full of Stars",
            "artist": "Coldplay",
            "uri": "spotify:track:0FDzzruyVECATHXKHFs9eJ",
        },
        {
            "name": "Yellow",
            "artist": "Coldplay",
            "uri": "spotify:track:3AJwUDP919kvQ9QcozQPxg",
        },
        {
            "name": "Sparks",
            "artist": "Coldplay",
            "uri": "spotify:track:7D0RhFcb3CrfPuTJ0obrod",
        },
        {
            "name": "Photograph",
            "artist": "Ed Sheeran",
            "uri": "spotify:track:1HNkqx9Ahdgi1Ixy2xkKkL",
        },
        {
            "name": "Thinking Out Loud",
            "artist": "Ed Sheeran",
            "uri": "spotify:track:34gCuhDGsG4bRPIf9bb02f"
        }
    ]
    return recommendations


# Returns a list of artists (mocked for testing)
def get_all_artists():
    return ['Coldplay', 'Adele', 'Drake', 'Beyonce', 'The Beatles', 'Ed Sheeran']
