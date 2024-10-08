import os
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
S3_BUCKET = os.environ.get("S3_BUCKET")
