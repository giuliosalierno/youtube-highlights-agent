from googleapiclient.discovery import build
from google.adk.tools import FunctionTool
import os 

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

def search_youtube(query: str) -> list:
    if not YOUTUBE_API_KEY:
        raise RuntimeError("YOUTUBE_API_KEY not set.")
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=YOUTUBE_API_KEY)
    response = youtube.search().list(
        q=query,
        part="snippet",
        type="video",
        maxResults=5,
        videoEmbeddable="true"
    ).execute()
    return [
        {
            "video_id": item['id']['videoId'],
            'title': item['snippet']['title'],
            'url': f'https://www.youtube.com/watch?v={item["id"]["videoId"]}'
        }
        for item in response.get('items', [])
    ]


def convert_mmss_to_seconds(mmss: str) -> int:
    minutes, seconds = map(int, mmss.split(':'))
    return minutes * 60 + seconds
