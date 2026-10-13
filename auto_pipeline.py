"""
Autonomous Daily YouTube Production Engine (MoneyPrinterTurbo)
1. Automatically analyzes channel or selects highest-probability viral topic.
2. Generates ultra-viral Hindi script with 3-second scroll-stopper hook.
3. Generates high-CTR Title, SEO Description, Viral Tags, Hashtags, and Pinned Comment.
4. Renders 1080x1920 9:16 HD Short with Gemini Voice + Fast Cinematic Cuts + Yellow Subtitles + BGM.
5. Saves ready-to-publish production package in storage/production/.
"""
import argparse
import datetime
import json
import os
import subprocess
import sys
from pathlib import Path
from loguru import logger

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from app.services import llm, voice
from app.services.youtube_seo import generate_youtube_metadata
from app.services.youtube_analyzer import YouTubeAnalyzer
from app.services import telegram_notify, youtube_upload
from app.utils import utils


CURATED_VIRAL_NICHES = [
    "3 Dark Psychology Secrets That Command Instant Respect",
    "3 Body Language Signs Someone Is Lying Right To Your Face",
    "Why High Value People Speak Less (The Power of Silence)",
    "3 Psychological Tricks To Read Anyone's Mind In 3 Seconds",
    "3 Signs Someone Is Secretly Jealous Of Your Success",
    "How To Stop Being Ignored In A Group Conversation",
    "The 72-Hour Wealth Rule Used By The Top 1 Percent",
    "3 Dangerous Habits That Destroy Your Confidence Instantly",
]


def pick_topic(custom_topic: str = "", analyze_channel: bool = False) -> str:
    """Select the best viral topic for today."""
    if custom_topic:
        return custom_topic

    if analyze_channel:
        try:
            analyzer = YouTubeAnalyzer()
            # Analyze recent patterns and pick recommended topic
            analysis = analyzer.analyze_channel([], sample_comments=[
                "Bhai psychology tricks par aur banao",
                "How to read body language please",
                "People ignore me, make a video on respect"
            ])
            recs = analysis.get("recommended_next_topics", [])
            if recs and recs[0].get("topic"):
                logger.info(f"Topic chosen from AI Channel Analysis: {recs[0]['topic']}")
                return recs[0]["topic"]
        except Exception as e:
            logger.warning(f"Failed to fetch AI analysis topic: {e}")

    # Rotate topic based on day of year
    day_idx = datetime.datetime.now().timetuple().tm_yday % len(CURATED_VIRAL_NICHES)
    chosen = CURATED_VIRAL_NICHES[day_idx]
    logger.info(f"Rotating curated viral topic: {chosen}")
    return chosen


def run_pipeline(
    subject: str = "",
    analyze_channel: bool = False,
    voice_name: str = "hi-IN-MadhurNeural",
    output_dir: str = "storage/production"
):
    """Run full end-to-end production pipeline."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    target_dir = Path(output_dir) / f"video_{timestamp}"
    target_dir.mkdir(parents=True, exist_ok=True)

    logger.info("==================================================")
    logger.info("🚀 STARTING AUTONOMOUS DAILY YOUTUBE ENGINE")
    logger.info("==================================================")

    # 1. Topic Selection
    chosen_subject = pick_topic(subject, analyze_channel)
    logger.success(f"📌 Today's Topic: {chosen_subject}")
    telegram_notify.notify_status(
        "start",
        "Daily Automation Started 🚀",
        f"📌 <b>Topic:</b> {chosen_subject}\n✍️ Generating viral script & Hinglish SEO..."
    )

    # 2. Script Generation (100% Viral Hindi with 3-second hook)
    logger.info("📝 Step 1: Generating Viral Hindi Script...")
    script = llm.generate_script(video_subject=chosen_subject)
    if not script:
        logger.error("Failed to generate script!")
        telegram_notify.notify_status("error", "Script Generation Failed", f"Topic: {chosen_subject}")
        return None

    script_path = target_dir / "script.txt"
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script)
    logger.success("✅ Viral Script generated and saved.")

    # 3. SEO Metadata Generation
    logger.info("🏷️ Step 2: Generating Viral Titles, Description, Tags, Hashtags...")
    seo_metadata = generate_youtube_metadata(chosen_subject, script)
    metadata_path = target_dir / "metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(seo_metadata, f, ensure_ascii=False, indent=2)

    ready_text_path = target_dir / "PUBLISH_READY.txt"
    with open(ready_text_path, "w", encoding="utf-8") as f:
        f.write(f"=== PRIMARY TITLE ===\n{seo_metadata.get('primary_title')}\n\n")
        f.write(f"=== ALTERNATIVE TITLES ===\n" + "\n".join(seo_metadata.get('alternative_titles', [])) + "\n\n")
        f.write(f"=== DESCRIPTION ===\n{seo_metadata.get('description')}\n\n")
        f.write(f"=== HASHTAGS ===\n{' '.join(seo_metadata.get('hashtags', []))}\n\n")
        f.write(f"=== TAGS ===\n{', '.join(seo_metadata.get('tags', []))}\n\n")
        f.write(f"=== PINNED COMMENT ===\n{seo_metadata.get('pinned_comment')}\n")
    logger.success("✅ YouTube SEO metadata prepared.")

    # 3.5 Prepare Search Terms
    logger.info("🔎 Preparing Video Search Terms for Pexels...")
    terms_list = []
    try:
        terms_list = llm.generate_terms(chosen_subject, script, amount=6)
    except Exception as te:
        logger.warning(f"Terms generation error: {te}")

    if not terms_list:
        subj = (chosen_subject or "dark psychology rules").strip()
        terms_list = [
            f"{subj} cinematic",
            "dark mysterious atmosphere",
            "intense eye contact stare",
            "confident person thinking",
            "dramatic shadows cinematic",
            "luxury modern lifestyle"
        ]
    video_terms_str = ", ".join(terms_list)
    logger.info(f"Using Video Terms: {video_terms_str}")

    telegram_notify.notify_status(
        "script",
        "Script & SEO Metadata Ready 🏷️",
        f"🔥 <b>Title:</b> {seo_metadata.get('primary_title')}\n🎬 Starting HD Video Rendering (Fast Cuts + Madhur Hindi Voice)..."
    )

    # 4. Render Video via CLI
    logger.info("🎬 Step 3: Rendering 1080x1920 HD Short with Fast Cuts...")
    venv_python = Path(".venv") / "Scripts" / "python.exe"
    python_cmd = str(venv_python) if venv_python.exists() else sys.executable

    cmd = [
        python_cmd,
        "cli.py",
        "--video-subject", chosen_subject,
        "--video-script", script,
        "--video-terms", video_terms_str,
        "--video-aspect", "9:16",
        "--voice-name", voice_name,
        "--font-name", "Nirmala.ttc",
        "--font-size", "75",
        "--text-fore-color", "#FFFF00",
        "--stroke-color", "#000000",
        "--stroke-width", "3",
        "--subtitle-enabled",
        "--subtitle-position", "two_thirds_bottom",
        "--subtitle-animation", "none",
        "--video-clip-duration", "3",
        "--video-source", "pexels",
        "--bgm-type", "random",
        "--bgm-volume", "0.18",
        "--n-threads", "1"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        logger.error(f"Video render failed with code {result.returncode}!")
        output_combined = ((result.stderr or "") + "\n" + (result.stdout or "")).strip()
        logger.error(f"Render output snippet:\n{output_combined[-1500:]}")
        import html
        err_snippet = html.escape((output_combined or "No error output")[-500:].strip())
        telegram_notify.notify_status(
            "error",
            "Video Render Failed",
            f"Exit code: <b>{result.returncode}</b>\n\n<pre>{err_snippet}</pre>"
        )
        return None

    # Parse stdout or disk search for output file
    try:
        rendered_video = None
        # Option A: parse JSON from stdout
        lines = [line.strip() for line in result.stdout.strip().split("\n") if line.strip().startswith("{")]
        if lines:
            try:
                task_data = json.loads(lines[-1])
                vids = task_data.get("result", {}).get("videos", [])
                if vids:
                    rendered_video = vids[0]
            except Exception as pe:
                logger.warning(f"Failed to parse task JSON from stdout: {pe}")

        # Option B: Fallback - disk search in storage/tasks for newest final-1.mp4
        if not rendered_video or not Path(rendered_video).exists():
            candidates = list(Path("storage/tasks").glob("*/final-1.mp4"))
            if candidates:
                candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                rendered_video = str(candidates[0])
                logger.info(f"Discovered rendered video via disk search: {rendered_video}")

        if not rendered_video or not Path(rendered_video).exists():
            raise FileNotFoundError("Rendered video file not found in stdout or storage/tasks!")

        # Copy to production folder
        import shutil
        prod_video = target_dir / "final_video.mp4"
        shutil.copy2(rendered_video, prod_video)
        logger.success(f"🎉 Production package completed: {prod_video}")

        # Send video and final completion report to Telegram
        telegram_notify.notify_status(
            "success",
            "Video Render Completed! 🎉",
            f"📹 <b>Title:</b> {seo_metadata.get('primary_title')}\n"
            f"📌 <b>Hashtags:</b> {' '.join(seo_metadata.get('hashtags', []))}\n"
            f"💬 <b>Pinned Comment:</b> {seo_metadata.get('pinned_comment')}\n"
            f"📁 <b>Output Folder:</b> <code>{target_dir}</code>"
        )
        telegram_notify.send_telegram_video(
            str(prod_video),
            caption=f"🔥 {seo_metadata.get('primary_title')}\n\n{' '.join(seo_metadata.get('hashtags', []))}"
        )

        # 5. Autonomous Direct YouTube Upload (100% Autopilot)
        if youtube_upload.is_authenticated():
            try:
                logger.info("🚀 Publishing directly to YouTube channel (Autopilot)...")
                telegram_notify.notify_status(
                    "uploading",
                    "YouTube Upload In Progress 🚀",
                    f"Publishing <b>{seo_metadata.get('primary_title')}</b> directly to channel..."
                )
                upload_res = youtube_upload.upload_short(
                    video_path=str(prod_video),
                    title=seo_metadata.get("primary_title", "Mindset Short #Shorts"),
                    description=seo_metadata.get("description", ""),
                    tags=seo_metadata.get("tags", []),
                    privacy_status="public"
                )
                yt_url = upload_res.get("url")
                telegram_notify.notify_status(
                    "success",
                    "Published LIVE on YouTube! 🎉",
                    f"📺 <b>WATCH SHORT:</b> {yt_url}\n"
                    f"📌 <b>Title:</b> {upload_res.get('title')}\n"
                    f"🌐 <b>Visibility:</b> Public (100% Autopilot)"
                )
                logger.success(f"Video uploaded to YouTube: {yt_url}")
            except Exception as up_err:
                logger.error(f"YouTube auto-upload failed: {up_err}")
                telegram_notify.notify_status("error", "YouTube Auto-Upload Error", str(up_err))
        else:
            logger.info("YouTube not authenticated; skipping auto-upload.")
    except Exception as e:
        logger.warning(f"Could not copy or send final video: {e}")

    logger.info("==================================================")
    logger.info(f"✅ READY FOR PUBLISH: {target_dir}")
    logger.info("==================================================")
    return target_dir


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run autonomous daily YouTube short production engine")
    parser.add_argument("--subject", default="", help="Custom video topic (optional)")
    parser.add_argument("--analyze-channel", action="store_true", help="Use AI channel analyzer for topic discovery")
    parser.add_argument("--voice-name", default="gemini:Puck-Upbeat", help="TTS voice identifier")
    parser.add_argument("--output-dir", default="storage/production", help="Output directory")

    args = parser.parse_args()
    run_pipeline(
        subject=args.subject,
        analyze_channel=args.analyze_channel,
        voice_name=args.voice_name,
        output_dir=args.output_dir
    )
