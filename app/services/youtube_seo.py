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
# Role: World-Class YouTube Shorts Growth Strategist & Viral Copywriter

## Mission:
Generate ultra-viral, irresistible, high-CTR YouTube Shorts metadata (Title, Description, Tags, Hashtags, Pinned Comment).

## CRITICAL TITLE VIRALITY FORMULA (MUST FOLLOW):
1. LENGTH: Keep primary_title short, punchy, and under 45 characters for 100% mobile screen visibility!
2. HOOK: Use extreme curiosity gap, mystery, or psychological tension. Never write boring generic sentences.
3. STYLE: Use powerful, high-retention English or sharp Hinglish with 1-2 psychological power words:
   (Secrets, Warning, Mistake, Dark Trick, Never, Rule, Silence, Power, Respect).
4. EMOJI: Exactly 1-2 high-contrast emojis (🤫, ⚡, 🛑, 🧠, 😱) + #Shorts.
5. PROVEN VIRAL EXAMPLES:
   * "3 Dark Psychology Secrets You Must Know 🤫 #Shorts"
   * "Never Do This Mistake In Public! 🛑 #Shorts"
   * "Why High Value People Speak Less 🤫 #Shorts"
   * "Ye 1 Trick Se Sab Respect Karenge ⚡ #Shorts"
   * "How To Read Anyone Instantly 🧠 #Shorts"
   * "Stop Being Ignored! Do This Instead 🤫 #Shorts"
   * "The Power of Silence Explained ⚡ #Shorts"

## DESCRIPTION RULES:
- Line 1-2: Intense curiosity hook in clean Hinglish/English.
- 3 bullet insights from the video.
- Clear CTA to subscribe to Jayant Talks for daily mental strength & life secrets!
- Viral hashtags.

## PINNED COMMENT:
- An addictive, debate-starting question that forces viewers to comment:
  e.g., "Aap inme se kaun sa rule sabse pehle try karoge? Comment me sach batana! 👇"

## Output Format:
Return ONLY a valid minified JSON object:
{
  "primary_title": "string",
  "alternative_titles": ["string", "string", "string"],
  "description": "string",
  "tags": ["string", "string"],
  "hashtags": ["#Shorts", "#string", "#string"],
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
