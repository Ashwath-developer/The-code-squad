import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "quickfire-development-secret-change-me")
    DATABASE = os.getenv("DATABASE_URL", os.path.join(BASE_DIR, "quickfire.db"))
    SMS_MODE = os.getenv("SMS_MODE", "simulation")
    MAX_SMS_RETRIES = int(os.getenv("MAX_SMS_RETRIES", "2"))
    OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY", "")
    SEARCH_API_KEY = os.getenv("SEARCH_API_KEY", "")
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")
