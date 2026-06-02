import telebot
from solver import GeminiSolver
import config

class ScreenSolverBot:
    def __init__(self, solver: GeminiSolver):
        self.solver = solver
        self.bot = None
        self.chat_id = config.TELEGRAM_CHAT_ID
        
        if config.TELEGRAM_BOT_TOKEN:
            self.bot = telebot.TeleBot(config.TELEGRAM_BOT_TOKEN)
            self._setup_handlers()

    def _setup_handlers(self):
        """Set up commands and message handlers for the bot."""
        
        @self.bot.message_handler(commands=['start', 'help'])
        def send_welcome(message):
            chat_id = str(message.chat.id)
            welcome_text = (
                "👋 Привіт! Я твій особистий Screen Solver Bot.\n\n"
                f"Твій Telegram Chat ID: `{chat_id}`\n\n"
                "Щоб я міг надсилати тобі скріншоти:\n"
                "1. Скопіюй цей Chat ID.\n"
                "2. Встав його в файл `.env` у рядок `TELEGRAM_CHAT_ID=...`.\n"
                "3. Перезапусти програму.\n\n"
                "Коли все буде налаштовано, просто натискай гарячі клавіші на ноутбуці, "
                "і я автоматично пришлю знімок екрану з вирішенням!"
            )
            self.bot.reply_to(message, welcome_text, parse_mode='Markdown')

        @self.bot.message_handler(func=lambda message: True)
        def handle_all_messages(message):
            # Security check: only respond to the configured user
            if self.chat_id and str(message.chat.id) != str(self.chat_id):
                self.bot.reply_to(message, "🔒 Доступ обмежено. Цей бот налаштований лише для одного користувача.")
                return

            # Check if this message is a reply to a previous bot message
            if message.reply_to_message:
                parent_msg_id = message.reply_to_message.message_id
                chat_session = self.solver.get_session(parent_msg_id)
                
                if chat_session:
                    # User is asking a follow-up question
                    status_msg = self.bot.reply_to(message, "🧠 Запит до Gemini... Будь ласка, зачекайте.")
                    
                    try:
                        response_text = self.solver.ask_follow_up(chat_session, message.text)
                        
                        # Delete the status message
                        self.bot.delete_message(message.chat.id, status_msg.message_id)
                        
                        # Send the actual response
                        sent_msgs = self.send_text_safe(message.chat.id, response_text, reply_to_message_id=message.message_id)
                        
                        # Register the new message IDs in the solver session so follow-ups can continue
                        for msg in sent_msgs:
                            self.solver.register_session(msg.message_id, chat_session)
                        
                    except Exception as e:
                        self.bot.edit_message_text(f"❌ Помилка: {e}", message.chat.id, status_msg.message_id)
                else:
                    self.bot.reply_to(message, "⚠️ Не вдалося знайти контекст для цього повідомлення. Спробуй зробити новий скріншот.")
            else:
                self.bot.reply_to(message, "ℹ️ Надішли мені відповідь (reply) на скріншот або його опис, щоб задати додаткове питання.")

    def send_text_safe(self, chat_id, text: str, reply_to_message_id=None) -> list:
        """
        Sends markdown message, splits into 4000 char chunks to avoid message length limits, 
        and falls back to plain text if formatting fails. Returns a list of sent message objects.
        """
        # Split message into chunks of 4000 characters
        chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
        sent_messages = []
        last_msg = None
        
        for i, chunk in enumerate(chunks):
            # First chunk is replied to original message, subsequent chunks are replied to the previous chunk to form a thread
            rep_id = reply_to_message_id if i == 0 else (last_msg.message_id if last_msg else None)
            try:
                msg = self.bot.send_message(chat_id, chunk, parse_mode='Markdown', reply_to_message_id=rep_id)
            except Exception as e:
                print(f"Markdown parsing failed for chunk {i}, sending as plain text. Error: {e}")
                try:
                    msg = self.bot.send_message(chat_id, chunk, reply_to_message_id=rep_id)
                except Exception as ex:
                    print(f"Failed to send chunk {i} as plain text. Error: {ex}")
                    if i == 0:
                        raise ex
                    continue
            last_msg = msg
            sent_messages.append(msg)
        return sent_messages

    def send_screenshot_result(self, image_path: str, explanation: str, chat_session):
        """
        Sends the screenshot photo and then the explanation text to the configured chat.
        Maps the message IDs to the Gemini Chat session.
        """
        if not self.chat_id:
            print("TELEGRAM_CHAT_ID is not configured. Cannot send screenshot.")
            return False

        try:
            # 1. Send the photo
            with open(image_path, 'rb') as photo:
                photo_msg = self.bot.send_photo(self.chat_id, photo, caption="📸 Знімок екрану")
            
            # 2. Send the solution text (could be multiple chunks)
            sent_msgs = self.send_text_safe(self.chat_id, explanation, reply_to_message_id=photo_msg.message_id)
            
            # 3. Associate all message IDs with the Gemini session
            self.solver.register_session(photo_msg.message_id, chat_session)
            for msg in sent_msgs:
                self.solver.register_session(msg.message_id, chat_session)
            return True
            
        except Exception as e:
            print(f"Error sending screenshot results to Telegram: {e}")
            return False

    def start_polling(self):
        """Starts polling for telegram messages in a non-blocking way."""
        if not self.bot:
            print("Bot not initialized. Check your token.")
            return
            
        import threading
        # Run polling in a separate daemon thread so it doesn't block the main program/hotkey listener
        polling_thread = threading.Thread(target=self.bot.infinity_polling, kwargs={"skip_pending": True}, daemon=True)
        polling_thread.start()
        print("Telegram bot polling started in background.")
