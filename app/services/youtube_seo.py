"""
YouTube SEO & Viral Metadata Generator Service
Generates high-CTR viral titles, SEO-optimized descriptions, tags, hashtags, and pinned comments.
"""
import json
import re
from typing import Dict, Any, List
from loguru import logger
from app.services import llm


SEO_SYSTEM_PROMPT = """
# Role: Elite YouTube Shorts SEO & Viral Growth Strategist (India / Hinglish Specialist)

## Objective:
Generate high-CTR, algorithm-optimized YouTube Shorts metadata (Title, Description, Tags, Hashtags, Pinned Comment) based on the video subject and script.

## LANGUAGE REQUIREMENT (MANDATORY):
- Titles, Description, and Pinned Comment MUST ALWAYS be written in punchy HINGLISH (Hindi written in Roman/English alphabet, e.g. "Log Aapki Izzat Karna Shuru Kar Denge! 🤫 #Shorts").
- Do NOT use Devanagari script for titles and descriptions; use clean Hinglish that Indian audiences type in YouTube search.

## Rules for YouTube Shorts Virality:
1. TITLES:
   - Must be explosive, curiosity-driven, and scroll-stopping (< 60 characters).
   - Use high-emotion words, relevant emojis (🤫, 😱, 🔥, ⚠️), and end with #Shorts.
   - Examples:
     * "Log Aapki Izzat Karna Shuru Kar Denge! 🤫 #Shorts"
     * "Ye 3 Dark Psychology Secrets Koi Nahi Batayega! 🔥 #Shorts"
     * "Stop Doing This 1 Mistake In Public! 😱 #Shorts"
2. DESCRIPTION:
   - First 2 lines in catchy Hinglish to hook search viewers.
   - Include 3 bullet takeaways in Hinglish.
   - Include an engagement question asking viewers to comment.
   - Include trending hashtags.
3. TAGS:
   - 15-20 comma-separated high-ranking search terms in English and Hinglish (e.g. "dark psychology tricks", "izzat pane ke tarike", "psychology facts in hindi", "body language tips").
4. HASHTAGS:
   - 5-8 high-volume trending hashtags (e.g. #Shorts, #PsychologyFacts, #Mindset, #Viral, #LifeHacks).
5. PINNED COMMENT:
   - A captivating question in Hinglish to blow up the comments section (e.g. "Aap inme se kaun sa rule sabse pehle try karoge? Comment me sach-sach batao! 👇").

## Output Format:
Return ONLY a valid JSON object matching this exact structure:
{
  "primary_title": "string",
  "alternative_titles": ["string", "string", "string"],
  "description": "string",
  "tags": ["string", "string"],
  "hashtags": ["#string", "#string"],
  "pinned_comment": "string"
}
""".strip()


def generate_youtube_metadata(video_subject: str, video_script: str) -> Dict[str, Any]:
    """
    Generate viral YouTube Shorts metadata (Title, Description, Tags, Hashtags).
    """
    logger.info(f"Generating YouTube SEO metadata for subject: {video_subject}")
    
    prompt = f"""
{SEO_SYSTEM_PROMPT}

### Context:
- Video Subject: {video_subject}
- Video Script:
{video_script}

Remember: Output ONLY valid JSON, with no markdown code fences or explanatory text.
""".strip()

    for attempt in range(3):
        try:
            response = llm._generate_response(prompt)
            if not response:
                continue

            cleaned = response.strip()
            # Remove markdown json fences if any
            if cleaned.startswith("```"):
                cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
                cleaned = re.sub(r"\s*```$", "", cleaned)
            
            data = json.loads(cleaned)
            if "primary_title" in data and "description" in data:
                logger.success(f"YouTube SEO metadata generated successfully: {data['primary_title']}")
                return data
        except Exception as e:
            logger.warning(f"Error parsing YouTube metadata (attempt {attempt + 1}): {e}")

    # Fallback default metadata
    clean_subj = video_subject.strip()
    return {
        "primary_title": f"{clean_subj} 😱 #Shorts",
        "alternative_titles": [
            f"Secret Trick You Never Knew! 🤫 #Shorts",
            f"99% People Don't Know This! 🔥 #Shorts",
            f"Stop Doing This Mistake! ⚠️ #Shorts"
        ],
        "description": f"{clean_subj}\n\nWatch till the end to discover the secret!\n\nSubscribe for daily viral psychology & self-growth shorts!\n\n#Shorts #Viral #Psychology",
        "tags": [clean_subj, "psychology facts", "shorts", "viral shorts", "mindset", "life hacks", "motivation"],
        "hashtags": ["#Shorts", "#Viral", "#Psychology", "#Mindset", "#Trending"],
        "pinned_comment": "Which secret was your favorite? Let me know in the comments below! 👇"
    }
