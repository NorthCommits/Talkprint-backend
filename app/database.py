from supabase import create_client, Client
from app.config import SUPABASE_URL, SUPABASE_SECRET_KEY

# Secret key — backend only, bypasses RLS safely
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)