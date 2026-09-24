// Static frontend can't read a .env file, so these two values live here
// directly. The anon key is SAFE to expose in browser JS — that's what it's
// for — as long as you keep RLS policies as set up in supabase/schema.sql
// (this project intentionally has no login, since it's for your personal
// use only).
const SUPABASE_URL = "https://oixthztcwhmvsknmfmwr.supabase.co";
const SUPABASE_ANON_KEY = "sb_publishable_P_xlTDIgUiSZdyF7mc9wdQ_2D0te1rq";

