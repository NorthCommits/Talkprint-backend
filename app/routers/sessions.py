from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from loguru import logger
from app.database import supabase
from app.dependencies import get_current_user
from app.services.transcription import transcribe_audio
from app.services.diarization import diarize_speakers
from app.services.dynamics import analyze_dynamics
from app.services.enrichment import enrich_conversation

import uuid

router = APIRouter()


async def process_audio(session_id: str, audio_bytes: bytes, filename: str):
    """Background task — transcribe, diarize, analyze, store results."""
    try:
        logger.info(f"Background processing started for session {session_id}")

        # Step 1 — Transcribe
        transcription = transcribe_audio(audio_bytes, filename)

        # Step 2 — Diarize
        diarization = diarize_speakers(
            transcription["segments"],
            transcription["transcript"]
        )

        # Step 3 — Store speakers
        speaker_id_map = {}
        for spk in diarization["speakers"]:
            spk_id = str(uuid.uuid4())
            speaker_id_map[spk["label"]] = spk_id
            supabase.table("speakers").insert({
                "id": spk_id,
                "session_id": session_id,
                "label": spk["label"],
                "talk_time_seconds": spk["talk_time_seconds"],
                "talk_time_percent": spk["talk_time_percent"]
            }).execute()

        # Step 4 — Store segments
        for seg in diarization["segments"]:
            supabase.table("segments").insert({
                "id": str(uuid.uuid4()),
                "session_id": session_id,
                "speaker_id": speaker_id_map[seg["speaker"]],
                "start_time": seg["start"],
                "end_time": seg["end"],
                "transcript": seg["text"]
            }).execute()

        # Step 5 — Analyze dynamics
        dynamics = analyze_dynamics(
            diarization["segments"],
            diarization["speakers"]
        )

        # Step 6 — Store analysis
        supabase.table("analysis").insert({
            "id": str(uuid.uuid4()),
            "session_id": session_id,
            "dominance_ratio": dynamics["dominance_ratio"],
            "interruption_count": dynamics["interruption_count"],
            "turn_taking_score": dynamics["turn_taking_score"],
            "topic_coherence_score": dynamics["topic_coherence_score"],
            "overall_health_score": dynamics["overall_health_score"]
        }).execute()


        # Step 7 — Enrich with GPT-4o
        logger.info(f"Running GPT-4o enrichment for session {session_id}")
        enrichment = enrich_conversation(
            transcription["transcript"],
            diarization["segments"],
            diarization["speakers"]
        )

        supabase.table("enrichments").insert({
            "id": str(uuid.uuid4()),
            "session_id": session_id,
            "summary": enrichment.get("summary"),
            "keywords": enrichment.get("keywords"),
            "topics": enrichment.get("topics"),
            "emotion_per_speaker": enrichment.get("emotion_per_speaker"),
            "personality_per_speaker": enrichment.get("personality_per_speaker"),
            "conversation_moments": enrichment.get("conversation_moments"),
            "conversation_arc": enrichment.get("conversation_arc")
        }).execute()

        logger.info(f"Enrichment stored for session {session_id}")


        # Step 8 — Update session status and duration
        supabase.table("sessions").update({
            "status": "done",
            "duration_seconds": transcription["duration"]
        }).eq("id", session_id).execute()

        logger.info(f"Processing complete for session {session_id}")

    except Exception as e:
        logger.error(f"Background processing failed for session {session_id}: {str(e)}")
        supabase.table("sessions").update({"status": "failed"})\
            .eq("id", session_id).execute()


@router.post("/upload")
async def upload_session(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user=Depends(get_current_user)
):
    logger.info(f"User {current_user.id} is uploading file {file.filename}")

    if not file.filename.endswith((".mp3", ".mp4", ".wav", ".m4a", ".webm")):
        raise HTTPException(status_code=400, detail="Unsupported file type")

    audio_bytes = await file.read()
    file_size_mb = round(len(audio_bytes) / (1024 * 1024), 2)
    logger.info(f"File received — {file.filename} ({file_size_mb} MB)")

    session_id = str(uuid.uuid4())
    supabase.table("sessions").insert({
        "id": session_id,
        "user_id": str(current_user.id),
        "filename": file.filename,
        "status": "processing"
    }).execute()

    # Kick off background processing
    background_tasks.add_task(process_audio, session_id, audio_bytes, file.filename)

    logger.info(f"Session {session_id} created, background processing started")

    return {
        "session_id": session_id,
        "filename": file.filename,
        "size_mb": file_size_mb,
        "status": "processing",
        "message": "File uploaded, analysis running in background"
    }


@router.get("/")
def get_sessions(current_user=Depends(get_current_user)):
    logger.info(f"Fetching all sessions for user {current_user.id}")
    result = supabase.table("sessions")\
        .select("*")\
        .eq("user_id", str(current_user.id))\
        .order("created_at", desc=True)\
        .execute()
    logger.info(f"Found {len(result.data)} sessions")
    return result.data


@router.get("/{session_id}")
def get_session(session_id: str, current_user=Depends(get_current_user)):
    logger.info(f"Fetching session {session_id}")
    result = supabase.table("sessions")\
        .select("*")\
        .eq("id", session_id)\
        .eq("user_id", str(current_user.id))\
        .single()\
        .execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Session not found")
    return result.data


@router.delete("/{session_id}")
def delete_session(session_id: str, current_user=Depends(get_current_user)):
    logger.info(f"Deleting session {session_id}")
    supabase.table("sessions")\
        .delete()\
        .eq("id", session_id)\
        .eq("user_id", str(current_user.id))\
        .execute()
    logger.info(f"Session {session_id} deleted")
    return {"message": "Session deleted successfully"}