import os
import sys
from dotenv import load_dotenv

# Force UTF-8 output on Windows consoles to prevent UnicodeEncodeError
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Ensure we use absolute imports or relative imports depending on running directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

def test_api():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        print("❌ API Key is missing or default in .env")
        return False

    if api_key.startswith("sk-or-"):
        return test_openrouter(api_key)
    else:
        return test_gemini(api_key)

def test_gemini(api_key):
    print("Testing direct Gemini API connectivity...")
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content("Напиши одне слово: Тест")
        print(f"✅ Direct Gemini API is working! Response: {response.text.strip()}")
        return True
    except Exception as e:
        print(f"❌ Direct Gemini API test failed: {e}")
        return False

def test_openrouter(api_key):
    print("Testing OpenRouter API connectivity...")
    try:
        import requests
        import json
        
        # Check model name from env
        model = os.getenv("GEMINI_MODEL", "google/gemini-2.5-pro")
        if not "/" in model:
            model = "google/gemini-2.5-pro" # fallback to default OpenRouter model path
            
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": [{"role": "user", "content": "Напиши одне слово: Тест"}],
            "max_tokens": 100
        }
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            data=json.dumps(data),
            timeout=10
        )
        
        if response.status_code == 200:
            res_json = response.json()
            text = res_json['choices'][0]['message']['content'].strip()
            print(f"✅ OpenRouter API is working! Model: {model}. Response: {text}")
            return True
        else:
            print(f"❌ OpenRouter API test failed with code {response.status_code}: {response.text}")
            print("⚠️ Перевірте, чи ви поповнили баланс на сайті OpenRouter (вкладка Credits)!")
            return False
    except Exception as e:
        print(f"❌ OpenRouter API test failed: {e}")
        return False

def test_telegram():
    print("Testing Telegram Bot connectivity...")
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token or token == "your_telegram_bot_token_here":
        print("❌ Telegram Bot Token is missing or default in .env")
        return False
        
    try:
        import telebot
        bot = telebot.TeleBot(token)
        me = bot.get_me()
        print(f"✅ Telegram Bot connection successful! Bot name: @{me.username}")
        
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if not chat_id or chat_id == "your_telegram_chat_id_here":
            print("⚠️ TELEGRAM_CHAT_ID is missing. This is okay for now.")
            print("   Please start the main application, send /start to your bot,")
            print("   and follow the instructions to get your Chat ID.")
        else:
            try:
                bot.send_message(chat_id, "🔧 Діагностичний тест пройдено! Бот успішно підключений.")
                print(f"✅ Test message sent successfully to Chat ID: {chat_id}")
            except Exception as e:
                print(f"⚠️ Could not send test message to Chat ID {chat_id}: {e}")
                print("   Make sure you have started a chat with the bot in Telegram by sending `/start`.")
        return True
    except Exception as e:
        print(f"❌ Telegram Bot test failed: {e}")
        return False

def main():
    print("="*60)
    print("Screen Solver Bot Setup Diagnostic")
    print("="*60)
    
    if not os.path.exists(".env"):
        print("❌ `.env` file does not exist!")
        sys.exit(1)

    api_ok = test_api()
    print("-" * 40)
    telegram_ok = test_telegram()
    print("="*60)
    
    if api_ok and telegram_ok:
        print("🎉 All systems ready! You can now run `python main.py` to start the bot.")
    else:
        print("⚠️ Some checks failed. Please inspect the output above and edit your `.env` file accordingly.")
        
if __name__ == "__main__":
    main()
