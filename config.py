import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DOWNLOAD_PATH = os.getenv("DOWNLOAD_PATH", "./downloads")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 50)) * 1024 * 1024
COBALT_API_URL = os.getenv("COBALT_API_URL", "https://cobalt-production-e3de.up.railway.app/")

TELEGRAM_TIMEOUT = 300
