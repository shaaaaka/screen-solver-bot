import os
import base64
import requests
import json
from PIL import Image
import config

class GeminiSolver:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.is_openrouter = api_key.startswith("sk-or-")
        # Direct Mistral API is activated if key is not OpenRouter and model contains 'mistral' or 'pixtral'
        self.is_mistral = not self.is_openrouter and ("mistral" in config.AI_MODEL.lower() or "pixtral" in config.AI_MODEL.lower())
        self.sessions = {}
        
        if self.is_openrouter:
            print("OpenRouter mode activated.")
            self.model_name = config.AI_MODEL
            # If the user has a standard model name from Gemini (e.g. gemini-2.5-flash)
            # map it to OpenRouter naming convention
            if not "/" in self.model_name:
                if "flash" in self.model_name:
                    self.model_name = "google/gemini-2.5-flash"
                elif "pro" in self.model_name:
                    self.model_name = "google/gemini-2.5-pro"
                else:
                    self.model_name = "google/gemini-2.5-pro"
            print(f"Using OpenRouter Model: {self.model_name}")
        elif self.is_mistral:
            print("Direct Mistral API mode activated.")
            self.model_name = config.AI_MODEL
            print(f"Using Mistral Model: {self.model_name}")
        else:
            print("Direct Gemini API mode activated.")
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            model_name = config.AI_MODEL
            if model_name.startswith("google/"):
                model_name = model_name.replace("google/", "", 1)
            self.model_name = model_name
            print(f"Using Gemini Model: {self.model_name}")

    def encode_image(self, image_path: str):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def solve_image(self, image_path: str):
        if self.is_openrouter:
            return self._solve_image_openrouter(image_path)
        elif self.is_mistral:
            return self._solve_image_mistral(image_path)
        else:
            return self._solve_image_gemini(image_path)

    def ask_follow_up(self, chat, question_text: str):
        if self.is_openrouter:
            return self._ask_follow_up_openrouter(chat, question_text)
        elif self.is_mistral:
            return self._ask_follow_up_mistral(chat, question_text)
        else:
            return self._ask_follow_up_gemini(chat, question_text)

    # --- Direct Gemini API Implementation ---
    def _solve_image_gemini(self, image_path: str):
        import google.generativeai as genai
        try:
            img = Image.open(image_path)
            model = genai.GenerativeModel(self.model_name)
            chat = model.start_chat(history=[])
            
            prompt = (
                "Ти — інтелектуальний помічник. Перед тобою скріншот мого екрану. "
                "Будь ласка, проаналізуй його вміст:\n"
                "1. Якщо на скріншоті зображено тестове запитання (тест з варіантами відповідей), надавай ВИКЛЮЧНО літеру (або літери) та текст правильних відповідей.\n"
                "КРИТИЧНО ВАЖЛИВО: Якщо правильних відповідей кілька, записуй КОЖНУ правильну відповідь СУВОРО З НОВОГО РЯДКА.\n"
                "НЕ з'єднуй їх в один рядок жодними сполучниками (такими як 'та', 'і', 'або', 'також' тощо).\n"
                "Приклад правильного формату для кількох відповідей:\n"
                "a) Konfiguračný súbor logrotate obsahuje syntaktickú chybu.\n"
                "d) Cron úloha pre logrotate nie je spustená alebo je nesprávne nakonfigurovaná.\n\n"
                "НЕ пиши жодних розборів, вступів, пояснень чи обґрунтувань. Тільки правильні літери та текст варіантів, кожен варіант з нового рядка. Уважно перевір форму вибору: якщо там квадратні чекбокси, правильних варіантів може бути кілька — знайди та вкажи їх УСІ.\n"
                "2. Якщо там складне завдання без варіантів відповідей, розв'яжи його покроково.\n"
                "3. Якщо там код або технічна помилка, поясни її причину та надай виправлене рішення.\n"
                "4. Якщо це просто веб-сторінка чи зображення, коротко поясни, що на ньому зображено.\n\n"
                "Будь ласка, пиши відповідь українською мовою."
            )
            
            response = chat.send_message([prompt, img])
            return response.text, chat
        except Exception as e:
            print(f"Error calling direct Gemini API: {e}")
            raise e

    def _ask_follow_up_gemini(self, chat, question_text: str):
        try:
            prompt = (
                f"Дай відповідь на наступне запитання користувача щодо попереднього скріншоту:\n\n"
                f"{question_text}\n\n"
                f"Відповідай українською мовою, використовуючи Markdown."
            )
            response = chat.send_message(prompt)
            return response.text
        except Exception as e:
            print(f"Error in direct Gemini follow-up: {e}")
            raise e

    # --- OpenRouter API Implementation ---
    def _solve_image_openrouter(self, image_path: str):
        try:
            base64_image = self.encode_image(image_path)
            
            prompt = (
                "Ти — інтелектуальний помічник. Перед тобою скріншот мого екрану. "
                "Будь ласка, проаналізуй його вміст:\n"
                "1. Якщо на скріншоті зображено тестове запитання (тест з варіантами відповідей), надавай ВИКЛЮЧНО літеру (або літери) та текст правильних відповідей.\n"
                "КРИТИЧНО ВАЖЛИВО: Якщо правильних відповідей кілька, записуй КОЖНУ правильну відповідь СУВОРО З НОВОГО РЯДКА.\n"
                "НЕ з'єднуй їх в один рядок жодними сполучниками (такими як 'та', 'і', 'або', 'також' тощо).\n"
                "Приклад правильного формату для кількох відповідей:\n"
                "a) Konfiguračný súbor logrotate obsahuje syntaktickú chybu.\n"
                "d) Cron úloha pre logrotate nie je spustená alebo je nesprávne nakonfigurovaná.\n\n"
                "НЕ пиши жодних розборів, вступів, пояснень чи обґрунтувань. Тільки правильні літери та текст варіантів, кожен варіант з нового рядка. Уважно перевір форму вибору: якщо там квадратні чекбокси, правильних варіантів може бути кілька — знайди та вкажи їх УСІ.\n"
                "2. Якщо там складне завдання без варіантів відповідей, розв'яжи його покроково.\n"
                "3. Якщо там код або технічна помилка, поясни її причину та надай виправлене рішення.\n"
                "4. Якщо це просто веб-сторінка чи зображення, коротко поясни, що на ньому зображено.\n\n"
                "Будь ласка, пиши відповідь українською мовою."
            )
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model_name,
                "messages": messages,
                "max_tokens": 2048
            }
            
            # Inject reasoning effort if configured (OpenRouter standard)
            effort = config.REASONING_EFFORT
            if effort and effort.lower() != "none":
                data["reasoning"] = {
                    "effort": effort.lower(),
                    "exclude": False
                }
            
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                data=json.dumps(data)
            )
            
            if response.status_code != 200:
                raise Exception(f"OpenRouter API error: {response.status_code} {response.text}")
                
            res_json = response.json()
            choice = res_json['choices'][0]['message']
            answer_text = choice['content']
            
            # Maintain manual conversation history for follow-ups
            history = list(messages)
            history.append({
                "role": "assistant",
                "content": answer_text
            })
            
            return answer_text, history
        except Exception as e:
            print(f"Error calling OpenRouter API: {e}")
            raise e

    def _ask_follow_up_openrouter(self, history, question_text: str):
        try:
            prompt = (
                f"Дай відповідь на наступне запитання користувача щодо попереднього скріншоту:\n\n"
                f"{question_text}\n\n"
                f"Відповідай українською мовою, використовуючи Markdown."
            )
            history.append({
                "role": "user",
                "content": prompt
            })
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model_name,
                "messages": history,
                "max_tokens": 2048
            }
            
            # Inject reasoning effort if configured (OpenRouter standard)
            effort = config.REASONING_EFFORT
            if effort and effort.lower() != "none":
                data["reasoning"] = {
                    "effort": effort.lower(),
                    "exclude": False
                }
            
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                data=json.dumps(data)
            )
            
            if response.status_code != 200:
                raise Exception(f"OpenRouter API error: {response.status_code} {response.text}")
                
            res_json = response.json()
            choice = res_json['choices'][0]['message']
            answer_text = choice['content']
            
            history.append({
                "role": "assistant",
                "content": answer_text
            })
            
            return answer_text
        except Exception as e:
            print(f"Error in OpenRouter follow-up: {e}")
            raise e

    # --- Direct Mistral API Implementation ---
    def _solve_image_mistral(self, image_path: str):
        try:
            base64_image = self.encode_image(image_path)
            
            prompt = (
                "Ти — інтелектуальний помічник. Перед тобою скріншот мого екрану. "
                "Будь ласка, проаналізуй його вміст:\n"
                "1. Якщо на скріншоті зображено тестове запитання (тест з варіантами відповідей), надавай ВИКЛЮЧНО літеру (або літери) та текст правильних відповідей.\n"
                "КРИТИЧНО ВАЖЛИВО: Якщо правильних відповідей кілька, записуй КОЖНУ правильну відповідь СУВОРО З НОВОГО РЯДКА.\n"
                "НЕ з'єднуй їх в один рядок жодними сполучниками (такими як 'та', 'і', 'або', 'також' тощо).\n"
                "Приклад правильного формату для кількох відповідей:\n"
                "a) Konfiguračný súbor logrotate obsahuje syntaktickú chyбу.\n"
                "d) Cron úloha pre logrotate nie je spustená alebo je nesprávne nakonfigurovaná.\n\n"
                "НЕ пиши жодних розборів, вступів, пояснень чи обґрунтувань. Тільки правильні літери та текст варіантів, кожен варіант з нового рядка. Уважно перевір форму вибору: якщо там квадратні чекбокси, правильних варіантів може бути кілька — знайди та вкажи їх УСІ.\n"
                "2. Якщо там складне завдання без варіантів відповідей, розв'яжи його покроково.\n"
                "3. Якщо там код або технічна помилка, поясни її причину та надай виправлене рішення.\n"
                "4. Якщо це просто веб-сторінка чи зображення, коротко поясни, що на ньому зображено.\n\n"
                "Будь ласка, пиши відповідь українською мовою."
            )
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model_name,
                "messages": messages,
                "max_tokens": 2048
            }
            
            response = requests.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers=headers,
                data=json.dumps(data)
            )
            
            if response.status_code != 200:
                raise Exception(f"Mistral API error: {response.status_code} {response.text}")
                
            res_json = response.json()
            choice = res_json['choices'][0]['message']
            answer_text = choice['content']
            
            history = list(messages)
            history.append({
                "role": "assistant",
                "content": answer_text
            })
            
            return answer_text, history
        except Exception as e:
            print(f"Error calling Mistral API: {e}")
            raise e

    def _ask_follow_up_mistral(self, history, question_text: str):
        try:
            prompt = (
                f"Дай відповідь на наступне запитання користувача щодо попереднього скріншоту:\n\n"
                f"{question_text}\n\n"
                f"Відповідай українською мовою, використовуючи Markdown."
            )
            history.append({
                "role": "user",
                "content": prompt
            })
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model_name,
                "messages": history,
                "max_tokens": 2048
            }
            
            response = requests.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers=headers,
                data=json.dumps(data)
            )
            
            if response.status_code != 200:
                raise Exception(f"Mistral API error: {response.status_code} {response.text}")
                
            res_json = response.json()
            choice = res_json['choices'][0]['message']
            answer_text = choice['content']
            
            history.append({
                "role": "assistant",
                "content": answer_text
            })
            
            return answer_text
        except Exception as e:
            print(f"Error in Mistral follow-up: {e}")
            raise e

    # --- Session Management ---
    def register_session(self, message_id: int, chat_session):
        self.sessions[message_id] = chat_session

    def get_session(self, reply_to_message_id: int):
        return self.sessions.get(reply_to_message_id)
