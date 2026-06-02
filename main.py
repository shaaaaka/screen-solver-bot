import os
import shutil
import threading
import sys
from PIL import ImageGrab
from pynput import keyboard

# Force UTF-8 output on Windows consoles to prevent UnicodeEncodeError
# Redirect stdout/stderr to devnull if running under pythonw.exe (where they are None)
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import config
from solver import GeminiSolver
from bot import ScreenSolverBot

# Global variables
is_paused = False
solver = None
bot = None
hotkey_listener = None
overlay_win = None

def copy_env_if_missing():
    """Copies .env.example to .env if .env doesn't exist."""
    env_path = ".env"
    example_path = ".env.example"
    if not os.path.exists(env_path) and os.path.exists(example_path):
        shutil.copy(example_path, env_path)
        print("Created `.env` file from `.env.example`. Please configure your keys inside `.env`.")

def beep_confirm():
    """Silent fallback, no sound on capture."""
    pass

def process_screenshot_worker():
    """Worker thread function to process screenshots without blocking the UI/hotkey listener."""
    import uuid
    temp_path = f"temp_screenshot_{uuid.uuid4().hex}.png"
    status_msg = None
    
    try:
        # Show analysis status on the overlay if running
        if overlay_win:
            overlay_win.show_answer("⏳ Аналізую екран...")
            
        # Take screenshot of primary screen
        screenshot = ImageGrab.grab()
        screenshot.save(temp_path)
        print("Screenshot captured successfully.")
        
        if not bot or not bot.chat_id:
            print("Telegram chat ID is not configured yet. Run /start in your Telegram bot first.")
            if overlay_win:
                overlay_win.show_answer("❌ Telegram chat ID is not configured yet.\nRun /start in your Telegram bot first.")
            return

        # Send initial status message to Telegram
        status_msg = bot.bot.send_message(bot.chat_id, "🔍 Отримано запит. Аналізую ваш екран за допомогою Gemini...")
        
        # Send to Gemini
        explanation, chat_session = solver.solve_image(temp_path)
        
        # Update overlay with the answer
        if overlay_win:
            overlay_win.show_answer(explanation)
            
        # Send results to Telegram
        bot.send_screenshot_result(temp_path, explanation, chat_session)
        
        # Clean up status message
        bot.bot.delete_message(bot.chat_id, status_msg.message_id)
        print("Explanation and image sent to Telegram.")
        
    except Exception as e:
        print(f"Error in screenshot worker: {e}")
        if overlay_win:
            overlay_win.show_answer(f"❌ Виникла помилка під час обробки:\n{str(e)}")
        if bot and bot.chat_id:
            error_text = f"❌ Виникла помилка під час обробки знімку екрану:\n`{str(e)}`"
            if status_msg:
                bot.bot.edit_message_text(error_text, bot.chat_id, status_msg.message_id, parse_mode='Markdown')
            else:
                bot.send_text_safe(bot.chat_id, error_text)
    finally:
        # Clean up screenshot file
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                print(f"Could not remove temp file: {e}")

def on_hotkey_triggered():
    """Triggered when global hotkey is pressed."""
    global is_paused
    if is_paused:
        print("Hotkey pressed, but application is currently PAUSED.")
        return

    print("Hotkey triggered! Starting screenshot processing...")
    beep_confirm()
    
    # Run the processing in a separate thread so we don't block the hotkey listener
    threading.Thread(target=process_screenshot_worker, daemon=True).start()

def on_toggle_paused(paused_state):
    """Callback when user pauses/resumes from system tray."""
    global is_paused
    is_paused = paused_state
    print(f"Application paused state changed to: {is_paused}")

def on_toggle_click_through():
    """Toggles click-through mode for the overlay window."""
    global overlay_win
    if overlay_win:
        overlay_win.toggle_click_through()
        print("Toggled click-through mode.")

def on_exit_app():
    """Callback when user exits the application from system tray."""
    print("Exiting application...")
    if hotkey_listener:
        hotkey_listener.stop()
    # Force exit to ensure background threads terminate
    os._exit(0)

def main():
    global solver, bot, hotkey_listener, overlay_win
    
    # Change CWD to the script directory to ensure path references work correctly
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    copy_env_if_missing()
    
    # Verify environment variables
    if not config.check_config():
        print("Application cannot start without proper configuration.")
        print("Please check `.env` and fill in: TELEGRAM_BOT_TOKEN and GEMINI_API_KEY.")
        sys.exit(1)
        
    # Initialize Core Modules
    solver = GeminiSolver(config.GEMINI_API_KEY)
    bot = ScreenSolverBot(solver)
    
    # Start Telegram Bot Polling Thread
    bot.start_polling()
    
    # Setup Hotkey Listener
    hotkey_str = config.HOTKEY
    print(f"Registering global hotkey: {hotkey_str}")
    
    # We parse and run hotkeys using pynput
    try:
        hotkey_listener = keyboard.GlobalHotKeys({
            hotkey_str: on_hotkey_triggered,
            "<ctrl>+<f2>": on_toggle_click_through
        })
        hotkey_listener.start()
        print("Global hotkey listener started. Click-through toggle: Ctrl+F2")
    except Exception as e:
        print(f"Failed to start hotkey listener: {e}")
        print("Check if the HOTKEY value in your .env file is correct (e.g., '<ctrl>+<shift>+s')")
        sys.exit(1)

    # Initialize Overlay Window
    try:
        from overlay import OverlayWindow
        overlay_win = OverlayWindow()
        print("Overlay window initialized.")
    except Exception as e:
        print(f"Failed to initialize overlay window: {e}")

    print("\n" + "="*50)
    print("Screen Solver Bot is RUNNING in STEALTH MODE.")
    print("Press your hotkey to capture and solve the screen!")
    print("="*50 + "\n")

    # Start Overlay event loop (blocks main thread)
    if overlay_win:
        try:
            overlay_win.start()
        except KeyboardInterrupt:
            pass
    else:
        # Fallback: keep the main thread alive silently if overlay is disabled/failed
        try:
            hotkey_listener.join()
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    main()
