# SpoYT - Spotify Playlist to YouTube Music Importer

### Setup Instructions

1. **Clone the repository:**

   ```bash
   git clone https://github.com/gekyxme/spoyt.git
   cd spotyt-importer
   ```

2. **Create and activate a virtual environment:**

   ```bash
   python -m venv spoyt-venv
   # Windows
   .\spoyt-venv\Scripts\activate
   # Mac/Linux
   source spoyt-venv/bin/activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Prepare environment variables:**

   - Copy `.env.example` to `.env`.
   - Fill in your Spotify API credentials inside `.env`.

5. **Place the `client_secret.json` file:**

   - Download from Google Cloud Console.
   - Put it in the project root.

6. **Spotify Developer Setup (3 minutes):**

   - Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).
   - CREATE AN APP → Give it any name.
   - Settings → Redirect URIs → Add `http://127.0.0.1:8080` → Save.
   - Copy your Client ID and Client Secret.
   - Fill your `.env` file:

     ```env
     SPOTIPY_CLIENT_ID=your_client_id_here
     SPOTIPY_CLIENT_SECRET=your_client_secret_here
     SPOTIPY_REDIRECT_URI=http://127.0.0.1:8080
     ```

7. **Google / YouTube Music Setup (5 minutes):**

   - Enable [YouTube Data API v3](https://console.cloud.google.com/apis/library/youtube.googleapis.com) → Enable.
   - Configure OAuth consent screen:
     - User type: External.
     - Fill product name (e.g., "PlaylistMover") and save.
     - Testing users → Add your Gmail address.
   - Create OAuth Client:
     - Credentials → + CREATE CREDENTIALS → OAuth client ID → Desktop application.
     - Download the JSON file and save it as `client_secret.json` in your project folder.

### How to Run

```bash
python main.py --spotify-playlist YOUR_SPOTIFY_PLAYLIST_ID --youtube-playlist YOUR_YOUTUBE_PLAYLIST_ID
```

**To import a specific range:**

```bash
python main.py --spotify-playlist YOUR_SPOTIFY_PLAYLIST_ID --youtube-playlist YOUR_YOUTUBE_PLAYLIST_ID --slice START_INDEX END_INDEX
```

Replace `YOUR_SPOTIFY_PLAYLIST_ID` and `YOUR_YOUTUBE_PLAYLIST_ID` with your real playlist IDs.

---

- `.env` and `client_secret.json` must not be committed.
- Quota errors reset after 24 hours.
- Playlist IDs should not include `?si=...` or extra URL parameters.
