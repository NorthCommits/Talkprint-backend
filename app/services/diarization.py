from loguru import logger


def diarize_speakers(segments: list, transcript: str) -> dict:
    """
    Simple speaker diarization using segment-level heuristics.
    Groups segments into speakers based on pause patterns and segment boundaries.
    In Phase 2 this will be replaced with pyannote.audio for true speaker separation.
    """
    logger.info("Running speaker diarization on transcript segments")

    if not segments:
        return {"speakers": [], "segments": []}

    diarized = []
    current_speaker = 1
    prev_end = 0
    speaker_segments = []

    for seg in segments:
        # If gap between segments > 1.5 seconds, potentially new speaker
        gap = seg["start"] - prev_end
        if gap > 1.5 and prev_end > 0:
            current_speaker = 2 if current_speaker == 1 else 1

        speaker_segments.append({
            "speaker": f"Speaker {current_speaker}",
            "start": seg["start"],
            "end": seg["end"],
            "text": seg["text"],
            "duration": round(seg["end"] - seg["start"], 2)
        })

        prev_end = seg["end"]

    # Calculate talk time per speaker
    speaker_stats = {}
    for seg in speaker_segments:
        spk = seg["speaker"]
        if spk not in speaker_stats:
            speaker_stats[spk] = 0.0
        speaker_stats[spk] += seg["duration"]

    total_time = sum(speaker_stats.values())
    speakers = []
    for spk, time in speaker_stats.items():
        speakers.append({
            "label": spk,
            "talk_time_seconds": round(time, 2),
            "talk_time_percent": round((time / total_time) * 100, 1) if total_time > 0 else 0
        })

    logger.info(f"Diarization complete — {len(speakers)} speakers detected")

    return {
        "speakers": speakers,
        "segments": speaker_segments
    }