# Talkprint Backend

> Conversation dynamics analysis API — upload an audio file, get back a full report on who spoke, how much, their personality, emotions, and the shape of the conversation.

---

## What is Talkprint?

Talkprint is a backend API that turns raw audio recordings into structured conversation intelligence. Drop in a meeting, podcast, interview, or any multi-speaker audio — Talkprint transcribes it, identifies speakers, measures dynamics, and uses GPT-4o to surface deeper insights like personality traits, emotional tone, key moments, and conversation arc.

---

## Features

- **Transcription** — OpenAI Whisper, multi-language support
- **Speaker Diarization** — Detects and separates speakers, calculates talk time
- **Conversation Dynamics** — Dominance ratio, interruptions, turn-taking score, health score
- **GPT-4o Enrichment**
  - Conversation summary
  - Keywords and topics
  - Emotion tone per speaker
  - Personality insights per speaker
  - Key conversation moments (peak energy, monologues, dead air)
  - Conversation arc (opening → buildup → peak → resolution → closing)
- **Auth** — Supabase Auth with JWT (signup, login, logout)
- **Background Processing** — Non-blocking audio pipeline
- **Clean Logging** — Color-coded sentence logs via Loguru
- **Full Report API** — Single endpoint returns everything

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI |
| Auth & Database | Supabase (Auth + PostgreSQL + RLS) |
| Transcription | OpenAI Whisper (`whisper-1`) |
| Enrichment | OpenAI GPT-4o |
| Background Tasks | FastAPI BackgroundTasks |
| Logging | Loguru |
| Server | Uvicorn |
| Deployment | Render |

---

## Project Structure

```
Talkprint-backend/
├── app/
│   ├── main.py              ← FastAPI entry point, middleware, logging
│   ├── config.py            ← Environment variables
│   ├── database.py          ← Supabase client
│   ├── dependencies.py      ← JWT auth dependency
│   ├── routers/
│   │   ├── auth.py          ← Signup, login, logout
│   │   ├── sessions.py      ← Audio upload + background pipeline
│   │   └── analysis.py      ← Analysis, enrichment, full report
│   ├── services/
│   │   ├── transcription.py ← OpenAI Whisper integration
│   │   ├── diarization.py   ← Speaker separation and talk time
│   │   ├── dynamics.py      ← Conversation dynamics engine
│   │   └── enrichment.py    ← GPT-4o enrichment pass
│   └── models/
│       └── schemas.py       ← Pydantic request/response models
├── .env
├── requirements.txt
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- A Supabase project
- An OpenAI API key

### Installation

```bash
# Clone the repo
git clone https://github.com/yourusername/Talkprint-backend.git
cd Talkprint-backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the root:

```env
OPENAI_API_KEY=sk-...
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_...
SUPABASE_SECRET_KEY=sb_secret_...
```

### Database Setup

Run the following SQL in your Supabase SQL editor:

```sql
-- Sessions
create table sessions (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references auth.users on delete cascade,
    filename text not null,
    duration_seconds float,
    status text default 'pending',
    created_at timestamp with time zone default now()
);

-- Speakers
create table speakers (
    id uuid primary key default gen_random_uuid(),
    session_id uuid references sessions on delete cascade,
    label text,
    talk_time_seconds float,
    talk_time_percent float
);

-- Segments
create table segments (
    id uuid primary key default gen_random_uuid(),
    session_id uuid references sessions on delete cascade,
    speaker_id uuid references speakers on delete cascade,
    start_time float,
    end_time float,
    transcript text
);

-- Analysis
create table analysis (
    id uuid primary key default gen_random_uuid(),
    session_id uuid references sessions on delete cascade,
    dominance_ratio jsonb,
    interruption_count int default 0,
    turn_taking_score float,
    topic_coherence_score float,
    overall_health_score float,
    created_at timestamp with time zone default now()
);

-- Enrichments
create table enrichments (
    id uuid primary key default gen_random_uuid(),
    session_id uuid references sessions on delete cascade,
    summary text,
    keywords jsonb,
    topics jsonb,
    emotion_per_speaker jsonb,
    personality_per_speaker jsonb,
    conversation_moments jsonb,
    conversation_arc jsonb,
    created_at timestamp with time zone default now()
);

-- Enable Row Level Security
alter table sessions enable row level security;
alter table speakers enable row level security;
alter table segments enable row level security;
alter table analysis enable row level security;
alter table enrichments enable row level security;

-- Policies
create policy "users see own sessions" on sessions for all using (auth.uid() = user_id);
create policy "users see own speakers" on speakers for all using (session_id in (select id from sessions where user_id = auth.uid()));
create policy "users see own segments" on segments for all using (session_id in (select id from sessions where user_id = auth.uid()));
create policy "users see own analysis" on analysis for all using (session_id in (select id from sessions where user_id = auth.uid()));
create policy "users see own enrichments" on enrichments for all using (session_id in (select id from sessions where user_id = auth.uid()));

-- Permissions
grant usage on schema public to postgres, anon, authenticated, service_role;
grant all privileges on all tables in schema public to postgres, anon, authenticated, service_role;
grant all privileges on all sequences in schema public to postgres, anon, authenticated, service_role;
```

### Run the Server

```bash
python3 -m uvicorn app.main:app --reload
```

Visit `http://127.0.0.1:8000/docs` for the interactive Swagger UI.

---

## API Reference

### Auth

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/signup` | Create a new account |
| POST | `/auth/login` | Login and receive JWT token |
| POST | `/auth/logout` | Logout current session |

### Sessions

| Method | Endpoint | Description |
|---|---|---|
| POST | `/sessions/upload` | Upload audio file, triggers background analysis |
| GET | `/sessions/` | List all sessions for current user |
| GET | `/sessions/{session_id}` | Get a single session |
| DELETE | `/sessions/{session_id}` | Delete a session |

### Analysis

| Method | Endpoint | Description |
|---|---|---|
| GET | `/analysis/{session_id}` | Get dynamics analysis |
| GET | `/analysis/{session_id}/enrichment` | Get GPT-4o enrichment |
| GET | `/analysis/{session_id}/report` | Get full report (everything in one call) |

---

## Audio Pipeline

When a file is uploaded, the following runs automatically in the background:

```
Upload audio
    ↓
OpenAI Whisper transcription (multi-language)
    ↓
Speaker diarization (talk time, segments)
    ↓
Conversation dynamics (dominance, turns, interruptions, health)
    ↓
GPT-4o enrichment (summary, emotions, personality, moments, arc)
    ↓
All results stored in Supabase
    ↓
Session status → "done"
```

Poll `GET /sessions/{session_id}` to check status. When `status` is `done`, fetch the full report.

---

## Supported Audio Formats

`.mp3` `.mp4` `.wav` `.m4a` `.webm`

---

## Full Report Response Shape

```json
{
  "session": { "id", "filename", "duration_seconds", "status", "created_at" },
  "speakers": [{ "label", "talk_time_seconds", "talk_time_percent" }],
  "segments": [{ "speaker_id", "start_time", "end_time", "transcript" }],
  "analysis": {
    "dominance_ratio": { "Speaker 1": 61.9, "Speaker 2": 38.1 },
    "interruption_count": 0,
    "turn_taking_score": 0.76,
    "topic_coherence_score": 1.0,
    "overall_health_score": 0.76
  },
  "enrichment": {
    "summary": "...",
    "keywords": ["..."],
    "topics": [{ "topic", "description", "speakers_involved" }],
    "emotion_per_speaker": { "Speaker 1": { "dominant_emotion", "description" } },
    "personality_per_speaker": { "Speaker 1": { "style", "traits", "description" } },
    "conversation_moments": [{ "type", "timestamp_start", "timestamp_end", "description" }],
    "conversation_arc": [{ "phase", "energy_level", "timestamp_start", "timestamp_end" }]
  }
}
```

---

## Roadmap

- [ ] Deploy to Render
- [ ] Mac app (SwiftUI)
- [ ] Pyannote.audio for true speaker diarization
- [ ] Webhook support for processing completion
- [ ] Audio storage via Supabase Storage
- [ ] Real-time processing progress via WebSocket
- [ ] Export report as PDF

---

## Author

**Swapnil Bhattacharya**
AI/GenAI Engineer — Multi-agent systems, RAG pipelines, LLM tooling
[GitHub](https://github.com/yourusername) · [LinkedIn](https://linkedin.com/in/yourprofile)

---

## License

MIT