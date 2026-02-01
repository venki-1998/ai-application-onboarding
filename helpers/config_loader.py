import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

# Load environment variables once
load_dotenv()

# --------------------------------------------------
# ✅ Global Configuration Setup
# --------------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise EnvironmentError("❌ GROQ_API_KEY not found. Please set it in your .env file.")

# Initialize Groq LLM once globally
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=GROQ_API_KEY
)

# --------------------------------------------------
# ✅ Helper Accessors
# --------------------------------------------------
def get_llm():
    """Return the globally initialized LLM client."""
    return llm

def get_env(var_name: str, default=None):
    """Get any environment variable with optional default."""
    return os.getenv(var_name, default)
