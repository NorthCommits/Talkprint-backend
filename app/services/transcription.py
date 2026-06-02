from openai import OpenAI
from app.config import OPENAI_API_KEY
from loguru import logger

client = OpenAI(api_key=OPENAI_API_KEY)


def transcribe_audio(audio_bytes: bytes, filename: str) -> dict:
    """
    Transcribe audio using OpenAI Whisper.
    Returns transcript with word-level timestamps and detected language.
    """
    logger.info(f"Sending {filename} to OpenAI Whisper for transcription")

    # Whisper needs a file-like object with a name
    import io
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = filename

    response = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        response_format="verbose_json",
        timestamp_granularities=["segment"]
    )

    segments = []
    for seg in response.segments:
        segments.append({
            "start": round(seg.start, 2),
            "end": round(seg.end, 2),
            "text": seg.text.strip()
        })

    logger.info(f"Transcription complete — {len(segments)} segments, language: {response.language}")

    return {
        "transcript": response.text,
        "language": response.language,
        "duration": round(response.duration, 2),
        "segments": segments
    }