import json
from openai import OpenAI
from app.config import OPENAI_API_KEY
from loguru import logger

client = OpenAI(api_key=OPENAI_API_KEY)


def enrich_conversation(transcript: str, speaker_segments: list, speakers: list) -> dict:
    """
    Single GPT-4o call that extracts all enrichment features:
    - Summary
    - Keywords and topics
    - Emotion tone per speaker
    - Personality insights per speaker
    - Conversation moments
    - Conversation arc
    """
    logger.info("Starting GPT-4o enrichment pass")

    # Build a readable version of the conversation for GPT-4o
    conversation_text = "\n".join([
        f"[{seg['speaker']} | {seg['start']}s - {seg['end']}s]: {seg['text']}"
        for seg in speaker_segments
    ])

    speaker_labels = [spk["label"] for spk in speakers]

    prompt = f"""
You are an expert conversation analyst. Analyze the following conversation transcript and return a single JSON object with all the fields described below. Return ONLY valid JSON, no explanation, no markdown, no backticks.

SPEAKERS IN THIS CONVERSATION: {", ".join(speaker_labels)}

CONVERSATION TRANSCRIPT:
{conversation_text}

FULL TRANSCRIPT:
{transcript}

Return a JSON object with exactly these fields:

{{
  "summary": "A 3-5 sentence human-readable summary of what was discussed, key points made, and overall outcome of the conversation.",

  "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],

  "topics": [
    {{"topic": "Topic name", "description": "One sentence about this topic", "speakers_involved": ["Speaker 1"]}}
  ],

  "emotion_per_speaker": {{
    "Speaker 1": {{
      "dominant_emotion": "confident",
      "secondary_emotion": "enthusiastic",
      "emotional_range": "narrow or wide",
      "description": "One sentence describing their emotional tone throughout"
    }}
  }},

  "personality_per_speaker": {{
    "Speaker 1": {{
      "style": "assertive / passive / collaborative / analytical / storyteller / direct",
      "traits": ["trait1", "trait2", "trait3"],
      "description": "One sentence personality summary based on how they speak"
    }}
  }},

  "conversation_moments": [
    {{
      "type": "peak_energy / longest_monologue / most_collaborative / dead_air / turning_point",
      "timestamp_start": 0.0,
      "timestamp_end": 0.0,
      "speaker": "Speaker 1 or Both",
      "description": "What happened at this moment"
    }}
  ],

  "conversation_arc": [
    {{
      "phase": "opening / buildup / peak / resolution / closing",
      "timestamp_start": 0.0,
      "timestamp_end": 0.0,
      "energy_level": "low / medium / high",
      "description": "What was happening in this phase"
    }}
  ]
}}
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are an expert conversation analyst. Always respond with valid JSON only."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3,
        response_format={"type": "json_object"}
    )

    raw = response.choices[0].message.content
    result = json.loads(raw)

    logger.info(
        f"Enrichment complete — "
        f"{len(result.get('keywords', []))} keywords, "
        f"{len(result.get('topics', []))} topics, "
        f"{len(result.get('conversation_moments', []))} moments detected"
    )

    return result