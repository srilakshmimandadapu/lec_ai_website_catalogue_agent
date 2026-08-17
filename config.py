from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    seed_url: str = os.getenv("SEED_URL", "https://books.toscrape.com/")
    max_pages: int = int(os.getenv("MAX_PAGES", "30"))
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "15"))
    user_agent: str = os.getenv(
        "USER_AGENT", "LEC-AI-Catalogue-Agent/1.0"
    )
    database_path: str = os.getenv(
        "DATABASE_PATH", "data/catalogue.sqlite3"
    )

settings = Settings()
