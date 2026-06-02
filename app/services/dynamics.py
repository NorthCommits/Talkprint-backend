from loguru import logger


def analyze_dynamics(speaker_segments: list, speakers: list) -> dict:
    """
    Analyze conversation dynamics from diarized segments.
    Computes dominance, interruptions, turn taking, and overall health.
    """
    logger.info("Analyzing conversation dynamics")

    if not speaker_segments or not speakers:
        return {}

    # Dominance ratio — who talked what percent
    dominance_ratio = {
        spk["label"]: spk["talk_time_percent"]
        for spk in speakers
    }

    # Turn taking — count how many times speaker switches
    turns = []
    prev_speaker = None
    for seg in speaker_segments:
        if seg["speaker"] != prev_speaker:
            turns.append(seg["speaker"])
            prev_speaker = seg["speaker"]

    total_turns = len(turns)

    # Interruptions — segment shorter than 1.5s after a speaker switch
    interruptions = 0
    for i, seg in enumerate(speaker_segments):
        if i > 0:
            prev = speaker_segments[i - 1]
            if seg["speaker"] != prev["speaker"] and seg["duration"] < 1.5:
                interruptions += 1

    # Turn taking score — how balanced is the conversation (0 to 1)
    if len(speakers) >= 2:
        talk_times = [spk["talk_time_percent"] for spk in speakers]
        max_share = max(talk_times)
        # Perfect balance = 50/50, score drops as one person dominates
        turn_taking_score = round(1 - abs(max_share - 50) / 50, 2)
    else:
        turn_taking_score = 0.0

    # Topic coherence — average segment length as a proxy
    # Longer segments = more coherent sustained speech
    avg_segment_duration = sum(
        seg["duration"] for seg in speaker_segments
    ) / len(speaker_segments)
    topic_coherence_score = round(min(avg_segment_duration / 10, 1.0), 2)

    # Overall health score — weighted combination
    overall_health_score = round(
        (turn_taking_score * 0.5) + (topic_coherence_score * 0.3) +
        (min(1.0, total_turns / 20) * 0.2), 2
    )

    logger.info(
        f"Dynamics complete — dominance: {dominance_ratio}, "
        f"interruptions: {interruptions}, "
        f"turn taking: {turn_taking_score}, "
        f"health: {overall_health_score}"
    )

    return {
        "dominance_ratio": dominance_ratio,
        "interruption_count": interruptions,
        "turn_taking_score": turn_taking_score,
        "topic_coherence_score": topic_coherence_score,
        "overall_health_score": overall_health_score,
        "total_turns": total_turns
    }