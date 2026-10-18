"""
YouTube Direct Auto-Upload Service for MoneyPrinterTurbo
Supports OAuth 2.0 Client credentials (client_secret.json)
Generates permanent reusable youtube_token.json
Uploads Shorts directly to channel with title, description, tags and privacy status.
"""
import os
import sys
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CLIENT_SECRET_FILE = PROJECT_ROOT / "client_secret.json"
TOKEN_FILE = PROJECT_ROOT / "youtube_token.json"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly"
]


def is_authenticated() -> bool:
    """Check if youtube_token.json exists and credentials are valid/refreshable."""
    if not TOKEN_FILE.exists():
        if os.environ.get("YOUTUBE_TOKEN_JSON"):
            try:
                token_info = json.loads(os.environ["YOUTUBE_TOKEN_JSON"])
                with open(TOKEN_FILE, "w", encoding="utf-8") as f:
                    f.write(json.dumps(token_info))
            except Exception:
                return False
        else:
            return False

    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        if not creds:
            return False
        if creds.valid:
            return True
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(TOKEN_FILE, "w", encoding="utf-8") as f:
                    f.write(creds.to_json())
                return True
            except Exception as e:
                logger.warning(f"YouTube refresh token expired or revoked: {e}")
                return False
        return False
    except Exception as e:
        logger.warning(f"Error checking YouTube token: {e}")
        return False


def get_authenticated_service(interactive: bool = False):
    """
    Load or create authenticated YouTube API service.
    First checks youtube_token.json.
    If missing or expired:
      - If interactive=True: runs local browser OAuth flow using client_secret.json.
      - If interactive=False: does NOT block/freeze; returns None.
    """
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    creds = None
    if TOKEN_FILE.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        except Exception as e:
            logger.warning(f"Could not load credentials from token file: {e}")
    elif os.environ.get("YOUTUBE_TOKEN_JSON"):
        try:
            token_info = json.loads(os.environ["YOUTUBE_TOKEN_JSON"])
            creds = Credentials.from_authorized_user_info(token_info, SCOPES)
            with open(TOKEN_FILE, "w", encoding="utf-8") as f:
                f.write(json.dumps(token_info))
            logger.info("Loaded YouTube credentials from YOUTUBE_TOKEN_JSON environment variable.")
        except Exception as e:
            logger.warning(f"Could not load credentials from YOUTUBE_TOKEN_JSON env var: {e}")

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing expired YouTube access token...")
            try:
                creds.refresh(Request())
                with open(TOKEN_FILE, "w", encoding="utf-8") as f:
                    f.write(creds.to_json())
                logger.success("Refreshed YouTube access token successfully.")
            except Exception as e:
                logger.error(f"Failed to refresh YouTube token: {e}")
                creds = None

        if not creds:
            if not interactive:
                logger.warning("YouTube credentials are invalid or expired, and running in non-interactive mode. Skipping interactive OAuth flow.")
                return None

            if not CLIENT_SECRET_FILE.exists():
                raise FileNotFoundError(
                    f"Neither valid token nor '{CLIENT_SECRET_FILE.name}' found in project root. "
                    f"Please download client_secret.json from Google Cloud Console."
                )
            logger.info(f"Initiating OAuth flow using {CLIENT_SECRET_FILE.name}...")
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET_FILE), SCOPES)
            creds = flow.run_local_server(port=0, prompt="consent", access_type="offline")

            # Save credentials for future use
            with open(TOKEN_FILE, "w", encoding="utf-8") as f:
                f.write(creds.to_json())
            logger.success(f"YouTube credentials saved to {TOKEN_FILE.name}")

    if not creds or not creds.valid:
        return None

    return build("youtube", "v3", credentials=creds)


def upload_short(
    video_path: str,
    title: str,
    description: str,
    tags: Optional[List[str]] = None,
    category_id: str = "27",  # 27 = Education, 22 = People & Blogs, 24 = Entertainment
    privacy_status: str = "public",  # "public", "unlisted", "private"
) -> Dict[str, Any]:
    """
    Upload a short video directly to YouTube channel.
    Returns: {"success": True, "video_id": "...", "url": "https://youtube.com/shorts/...", ...}
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    from googleapiclient.http import MediaFileUpload

    logger.info(f"Authenticating with YouTube API...")
    youtube = get_authenticated_service(interactive=False)
    if not youtube:
        raise RuntimeError("YouTube API service could not be authenticated. Refresh token may be expired.")

    # YouTube max title length is 100
    safe_title = title.strip()[:100]
    # Ensure #Shorts is present in title or description
    if "#Shorts" not in safe_title and "#shorts" not in safe_title:
        if len(safe_title) <= 92:
            safe_title += " #Shorts"

    body = {
        "snippet": {
            "title": safe_title,
            "description": description[:5000],
            "tags": tags[:30] if tags else ["Shorts", "Viral", "Hindi"],
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
        },
    }

    logger.info(f"Uploading '{safe_title}' to YouTube (Privacy: {privacy_status})...")
    media = MediaFileUpload(
        video_path,
        chunksize=1024 * 1024 * 4,  # 4MB chunks
        resumable=True,
        mimetype="video/mp4",
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            logger.info(f"Uploaded {int(status.progress() * 100)}%...")

    video_id = response.get("id")
    video_url = f"https://youtube.com/shorts/{video_id}"
    logger.success(f"Video successfully uploaded to YouTube! URL: {video_url}")

    return {
        "success": True,
        "video_id": video_id,
        "url": video_url,
        "title": safe_title,
        "privacy": privacy_status,
    }


if __name__ == "__main__":
    if "--auth" in sys.argv or "-a" in sys.argv:
        try:
            print("Authenticating with YouTube...")
            srv = get_authenticated_service(interactive=True)
            channels = srv.channels().list(part="snippet,statistics", mine=True).execute()
            items = channels.get("items", [])
            if items:
                ch = items[0]
                print(f"Logged in successfully as: {ch['snippet']['title']} (Subscribers: {ch['statistics'].get('subscriberCount')})")
            else:
                print("Logged in, but no channel found for this Google account.")
        except Exception as err:
            print(f"Auth error: {err}")
