from dotenv import load_dotenv, find_dotenv
import os

dotenv_path = find_dotenv()
if dotenv_path:
    print(f"Loading .env file from: {dotenv_path}")
    load_dotenv(dotenv_path)
else:
    print("No .env file found")

class Config:
    ROOKIE_HOST = os.getenv("ROOKIE_HOST", "localhost")
    ROOKIE_PORT = int(os.getenv("ROOKIE_PORT", 10095))
    INTERVIEWER_HOST = os.getenv("INTERVIEWER_HOST", "localhost")
    INTERVIEWER_PORT = int(os.getenv("INTERVIEWER_PORT", 10095))
    CHUNK_SIZE = [int(x) for x in os.getenv("CHUNK_SIZE", "5,10,5").split(",")]
    CHUNK_INTERVAL = int(os.getenv("CHUNK_INTERVAL", 10))
    HOTWORD = os.getenv("HOTWORD", "")
    AUDIO_IN = os.getenv("AUDIO_IN", None)
    AUDIO_FS = int(os.getenv("AUDIO_FS", 48000))
    AUDIO_CHANNEL = int(os.getenv("AUDIO_CHANNEL", 2))
    SEND_WITHOUT_SLEEP = os.getenv("SEND_WITHOUT_SLEEP", "True").lower() in ("true", "1", "yes")
    THREAD_NUM = int(os.getenv("THREAD_NUM", 1))
    WORDS_MAX_PRINT = int(os.getenv("WORDS_MAX_PRINT", 10000))
    OUTPUT_DIR = os.getenv("OUTPUT_DIR", None)
    SSL = int(os.getenv("SSL", 1))  # 整数类型，1 表示启用 SSL，0 表示禁用
    USE_ITN = int(os.getenv("USE_ITN", 1))  # 整数类型，1 表示使用 ITN，0 表示不使用
    MODE = os.getenv("MODE", "2pass")
    INTERVIEWER_WAIT_TIME = int(os.getenv("INTERVIEWER_WAIT_TIME", 5000))
    ROOKIE_WAIT_TIME = int(os.getenv("ROOKIE_WAIT_TIME", 5000))
    ROOKIE_DIALOG_LEN=int(os.getenv("ROOKIE_DIALOG_LEN", 1))
    CHATGPT_DIALOG_LEN=int(os.getenv("CHATGPT_DIALOG_LEN", 2))
    INTERVIEWER_DIALOG_LEN=int(os.getenv("INTERVIEWER_DIALOG_LEN", 3))
    REDIS_HOST=os.getenv("REDIS_HOST", "127.0.0.1")
    REDIS_PORT=int(os.getenv("REDIS_PORT", 6379))
    AGGREGATE_DEVICE_INDEX=int(os.getenv("AGGREGATE_DEVICE_INDEX", 13))
    MIC_DEVICE_INDEX=int(os.getenv("MIC_DEVICE_INDEX", 2))
    MEILISEARCH_HOST=os.getenv("MEILISEARCH_HOST", "127.0.0.1")
    MEILISEARCH_PORT=int(os.getenv("MEILISEARCH_PORT", 7700))
    MEILISEARCH_DEEP=int(os.getenv("MEILISEARCH_DEEP", 1))
    RAG_ENABLED = os.getenv("RAG_ENABLED", "False").lower() in ("true", "1", "yes")
    R2_ACCESS_KEY_ID = os.getenv('R2_ACCESS_KEY_ID')
    R2_SECRET_ACCESS_KEY = os.getenv('R2_SECRET_ACCESS_KEY')
    R2_BUCKET_NAME = os.getenv('R2_BUCKET_NAME')
    R2_REGION = os.getenv('R2_REGION')
    R2_ENDPOINT_URL = os.getenv('R2_ENDPOINT_URL')
    R2_CUSTOM_DOMAIN = os.getenv('R2_CUSTOM_DOMAIN')
