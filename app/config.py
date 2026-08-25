import os
from datetime import date
from dataclasses import dataclass
from dotenv import load_dotenv
load_dotenv()

@dataclass(frozen=True)
class Settings:
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_base_url: str = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    db_path: str = os.getenv("TRENDLY_DB_PATH", "./trendly.sqlite3")
    orders_path: str = os.getenv("TRENDLY_ORDERS_PATH", "./data/orders.json")
    policy_path: str = os.getenv("TRENDLY_POLICY_PATH", "./data/trendly_policy.md")
    as_of_date: str = os.getenv("TRENDLY_AS_OF_DATE", "2026-08-18")

settings = Settings()
