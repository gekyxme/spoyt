import os
import sys
import time
import logging
import argparse
from typing import List, Tuple, Dict, Optional, Set

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s  %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

SCOPES = ["https://www.googleapis.com/auth/youtube", "https://www.googleapis.com/auth/youtube.readonly"]
YT_INSERT_PARTS = "snippet"
YT_SEARCH_PARTS = "snippet"
YT_THROTTLE_SEC = 0.2

# Authentication functions
def spotify_client() -> spotipy.Spotify:
    auth = SpotifyOAuth(scope="playlist-read-private playlist-read-collaborative")
    return spotipy.Spotify(auth_manager=auth)

def youtube_client() -> "googleapiclient.discovery.Resource":
    creds: Optional[Credentials] = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token_file:
            token_file.write(creds.to_json())
    return build("youtube", "v3", credentials=creds, cache_discovery=False)

# Fetch all track details from Spotify playlist
def fetch_spotify_tracks(sp: spotipy.Spotify, playlist_id: str) -> List[Dict]:
    logging.info("Fetching Spotify playlist...")
    results = sp.playlist_items(playlist_id, additional_types=["track"], limit=100)
    tracks = results["items"]
    while results["next"]:
        results = sp.next(results)
        tracks.extend(results["items"])
    simplified = []
    for item in tracks:
        track = item["track"]
        if not track:
            continue
        artist = track["artists"][0]["name"] if track["artists"] else ""
        simplified.append({
            "title": track["name"],
            "artist": artist,
            "album": track["album"]["name"],
            "duration_ms": track["duration_ms"],
        })
    logging.info("Fetched %d tracks from Spotify", len(simplified))
    return simplified

# Fetch existing video IDs from YouTube playlist
def fetch_existing_playlist_videos(yt, playlist_id: str) -> Set[str]:
    video_ids = set()
    request = yt.playlistItems().list(
        part="contentDetails",
        playlistId=playlist_id,
        maxResults=50,
    )
    while request:
        response = request.execute()
        for item in response.get("items", []):
            video_ids.add(item["contentDetails"]["videoId"])
        request = yt.playlistItems().list_next(request, response)
    return video_ids

# Search for the video ID based on title and artist
def youtube_search_track(yt, title: str, artist: str) -> Optional[str]:
    query = f"{title} {artist} audio"
    request = yt.search().list(
        part=YT_SEARCH_PARTS,
        q=query,
        type="video",
        videoCategoryId="10",
        maxResults=5,
    )
    response = request.execute()
    for item in response.get("items", []):
        vid_id = item["id"]["videoId"]
        res_title = item["snippet"]["title"].lower()
        if title.lower().split()[0] in res_title:
            return vid_id
    return None

# Add video to YouTube playlist
def youtube_add_to_playlist(yt, playlist_id: str, video_id: str) -> None:
    body = {
        "snippet": {
            "playlistId": playlist_id,
            "resourceId": {
                "kind": "youtube#video",
                "videoId": video_id,
            },
        }
    }
    yt.playlistItems().insert(part=YT_INSERT_PARTS, body=body).execute()
    time.sleep(YT_THROTTLE_SEC)

# Main import function
def import_playlist(spotify_playlist_id: str, youtube_playlist_id: str, slice_range: Optional[Tuple[int, int]] = None) -> None:
    sp = spotify_client()
    yt = youtube_client()
    
    existing_videos = fetch_existing_playlist_videos(yt, youtube_playlist_id)

    tracks = fetch_spotify_tracks(sp, spotify_playlist_id)
    if slice_range:
        start, end = slice_range
        tracks = tracks[start - 1: end]
        logging.info("Importing slice %d–%d (%d tracks)", start, end, len(tracks))

    imported, skipped = [], []

    for idx, track in enumerate(tqdm(tracks, desc="Importing", unit="song")):
        try:
            video_id = youtube_search_track(yt, track["title"], track["artist"])
            if video_id:
                if video_id in existing_videos:
                    skipped.append((track, "Already exists"))
                else:
                    youtube_add_to_playlist(yt, youtube_playlist_id, video_id)
                    existing_videos.add(video_id)
                    imported.append(track)
            else:
                skipped.append((track, "Not found"))
        except Exception as e:
            skipped.append((track, str(e)))

    print("\n\u2500\u2500\u2500\u2500\u2500\u2500 IMPORT COMPLETE \u2500\u2500\u2500\u2500\u2500\u2500")
    print(f"Total attempted : {len(tracks)}")
    print(f"Successfully added : {len(imported)}")
    print(f"Skipped / failed  : {len(skipped)}")
    if skipped:
        print("\nSkipped list:")
        for t, reason in skipped:
            print(f"- {t['title']} – {t['artist']}  ({reason})")

# CLI parsing
def parse_args():
    parser = argparse.ArgumentParser(description="Copy a Spotify playlist (or slice) to YouTube Music.")
    parser.add_argument("--spotify-playlist", required=True, help="Spotify playlist ID")
    parser.add_argument("--youtube-playlist", required=True, help="YouTube playlist ID")
    parser.add_argument("--slice", nargs=2, metavar=("START", "END"), type=int, help="Optional inclusive index range")
    return parser.parse_args()

if __name__ == "__main__":
    cli = parse_args()
    slice_tuple = tuple(cli.slice) if cli.slice else None
    import_playlist(cli.spotify_playlist, cli.youtube_playlist, slice_tuple)
