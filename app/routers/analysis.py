from fastapi import APIRouter, HTTPException, Depends
from loguru import logger
from app.database import supabase
from app.dependencies import get_current_user
from app.services.transcription import transcribe_audio
from app.services.diarization import diarize_speakers
from app.services.dynamics import analyze_dynamics
import uuid

router = APIRouter()


@router.post("/{session_id}/run")
async def run_analysis(session_id: str, current_user=Depends(get_current_user)):
    logger.info(f"Starting analysis for session {session_id}")

    # Fetch session
    session = supabase.table("sessions")\
        .select("*")\
        .eq("id", session_id)\
        .eq("user_id", str(current_user.id))\
        .single()\
        .execute()

    if not session.data:
        raise HTTPException(status_code=404, detail="Session not found")

    # Update status to processing
    supabase.table("sessions")\
        .update({"status": "processing"})\
        .eq("id", session_id)\
        .execute()

    logger.info(f"Session {session_id} status set to processing")

    try:
        # We need audio bytes — for now return instructions
        # In next step we'll store and retrieve audio bytes properly
        raise HTTPException(
            status_code=400,
            detail="Audio bytes not stored yet — update sessions router to pass bytes to analysis"
        )

    except HTTPException:
        raise
    except Exception as e:
        supabase.table("sessions")\
            .update({"status": "failed"})\
            .eq("id", session_id)\
            .execute()
        logger.error(f"Analysis failed for session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}")
def get_analysis(session_id: str, current_user=Depends(get_current_user)):
    logger.info(f"Fetching analysis for session {session_id}")

    result = supabase.table("analysis")\
        .select("*")\
        .eq("session_id", session_id)\
        .single()\
        .execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Analysis not found for this session")

    return result.data


@router.get("/{session_id}/enrichment")
def get_enrichment(session_id: str, current_user=Depends(get_current_user)):
    logger.info(f"Fetching enrichment for session {session_id}")

    result = supabase.table("enrichments")\
        .select("*")\
        .eq("session_id", session_id)\
        .single()\
        .execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Enrichment not found for this session")

    return result.data


@router.get("/{session_id}/report")
def get_full_report(session_id: str, current_user=Depends(get_current_user)):
    logger.info(f"Fetching full report for session {session_id}")

    session = supabase.table("sessions")\
        .select("*")\
        .eq("id", session_id)\
        .eq("user_id", str(current_user.id))\
        .single()\
        .execute()

    if not session.data:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.data["status"] != "done":
        return {"status": session.data["status"], "message": "Analysis still in progress"}

    speakers = supabase.table("speakers")\
        .select("*")\
        .eq("session_id", session_id)\
        .execute()

    segments = supabase.table("segments")\
        .select("*")\
        .eq("session_id", session_id)\
        .order("start_time")\
        .execute()

    analysis = supabase.table("analysis")\
        .select("*")\
        .eq("session_id", session_id)\
        .single()\
        .execute()

    enrichment = supabase.table("enrichments")\
        .select("*")\
        .eq("session_id", session_id)\
        .single()\
        .execute()

    logger.info(f"Full report assembled for session {session_id}")

    return {
        "session": session.data,
        "speakers": speakers.data,
        "segments": segments.data,
        "analysis": analysis.data,
        "enrichment": enrichment.data
    }


