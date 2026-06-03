import os
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
AI_API_KEY = os.getenv("AI_API_KEY")
HOTKEY = os.getenv("HOTKEY", "<ctrl>+<shift>+<f12>")
AI_MODEL = os.getenv("AI_MODEL", "gemini-2.5-flash")
REASONING_EFFORT = os.getenv("REASONING_EFFORT", "none")

def check_config():
    """Verify that all required environment variables are set."""
    missing = []
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "your_telegram_bot_token_here":
        missing.append("TELEGRAM_BOT_TOKEN")
    if not AI_API_KEY or AI_API_KEY == "your_ai_api_key_here":
        missing.append("AI_API_KEY")
        
    # Note: TELEGRAM_CHAT_ID can be optional initially because the bot can auto-detect it on /start
    chat_id_missing = not TELEGRAM_CHAT_ID or TELEGRAM_CHAT_ID == "your_telegram_chat_id_here"
    
    if missing:
        print("\n" + "="*50)
        print("WARNING: Missing required configuration in .env file:")
        for item in missing:
            print(f" - {item}")
        print("Please edit the .env file in the project folder and supply your keys.")
        print("="*50 + "\n")
        return False
        
    if chat_id_missing:
        print("\n" + "="*50)
        print("NOTE: TELEGRAM_CHAT_ID is not configured in .env.")
        print("Please send a message (like /start) to your bot in Telegram,")
        print("and the bot will output your chat ID so you can save it in .env.")
        print("="*50 + "\n")
        
    return True
