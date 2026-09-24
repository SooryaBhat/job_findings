import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")  # optional fallback LLM

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY", "")
JOOBLE_API_KEY = os.getenv("JOOBLE_API_KEY", "")

# Big/very-hard-to-break-into companies -> "reach" tier by default when a
# company isn't manually tagged. Feel free to edit this list.
REACH_KEYWORDS = [
    "google", "microsoft", "amazon", "meta", "apple", "netflix", "nvidia",
    "goldman sachs", "jpmorgan", "morgan stanley", "mckinsey", "bcg", "bain",
    "citi", "barclays", "deutsche bank", "blackrock", "oracle", "salesforce",
    "walmart global tech", "flipkart", "adobe",
]

COMPETITIVE_KEYWORDS = [
    "razorpay", "phonepe", "swiggy", "zomato", "cred", "groww", "postman",
    "freshworks", "zoho", "chargebee", "whatfix", "sarvam", "krutrim",
    "observe.ai", "yellow.ai", "netradyne", "meesho", "myntra",
]
