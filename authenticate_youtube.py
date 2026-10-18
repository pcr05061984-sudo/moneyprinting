"""
YouTube OAuth Authentication & Token Refresher for MoneyPrinterTurbo
Run this script whenever you need to connect or refresh your YouTube account.
"""
import sys
import shutil
from pathlib import Path
from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services import youtube_upload

def main():
    print("=" * 60)
    print("🔑 YOUTUBE CHANNEL AUTHENTICATION & TOKEN REFRESHER")
    print("=" * 60)
    print("A browser window will open shortly. Please sign in with")
    print("the Google account that owns your YouTube channel (Jayant Talks)")
    print("and grant permissions to upload videos.")
    print("=" * 60)

    try:
        service = youtube_upload.get_authenticated_service(interactive=True)
        if not service:
            print("❌ Authentication failed. Could not create YouTube service.")
            return

        res = service.channels().list(part="snippet,statistics", mine=True).execute()
        items = res.get("items", [])
        if items:
            ch = items[0]
            title = ch.get("snippet", {}).get("title", "Unknown")
            subscribers = ch.get("statistics", {}).get("subscriberCount", "0")
            print("\n" + "=" * 60)
            print(f"🎉 SUCCESS! AUTHENTICATED WITH CHANNEL:")
            print(f"📺 Channel Name: {title}")
            print(f"👥 Subscribers : {subscribers}")
            print("=" * 60)

            # Sync to render directory as well
            token_src = PROJECT_ROOT / "youtube_token.json"
            token_dst = PROJECT_ROOT / "render" / "youtube_token.json"
            if token_src.exists():
                shutil.copy2(token_src, token_dst)
                print(f"✅ Synced fresh token to render/youtube_token.json")
                
            print("\n💡 TIP TO PREVENT TOKEN EXPIRY EVERY 7 DAYS:")
            print("1. Go to https://console.cloud.google.com/apis/credentials/consent")
            print("2. Under 'Publishing status', click 'PUBLISH APP' (change from Testing to Production).")
            print("3. Once set to Production, your refresh token NEVER expires!")
            print("=" * 60)
        else:
            print("⚠️ Authenticated, but no YouTube channel found for this Google account.")

    except Exception as e:
        print(f"\n❌ Error during authentication: {e}")

if __name__ == "__main__":
    main()
