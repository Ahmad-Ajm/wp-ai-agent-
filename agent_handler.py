import os
import logging
from langchain.chat_models import ChatOpenAI

class AgentHandler:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.logger = logging.getLogger(__name__)

        prompt_path = os.path.join(os.path.dirname(__file__), "wp_prompt.txt")
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                self.base_prompt = f.read().strip()
        except Exception as e:
            self.logger.error(f"فشل في قراءة wp_prompt.txt: {e}")
            self.base_prompt = ""

        self.llm = ChatOpenAI(model_name="gpt-4o", openai_api_key=self.api_key)

    def process_request(self, prompt: str, action: str = "generate_php") -> str:
        try:
            self.logger.info(f"تنفيذ عبر predict() | الإجراء: {action}")
            full_prompt = f"{self.base_prompt}\n\nطلب المستخدم:\n{prompt}"
            result = self.llm.predict(full_prompt)
            return result
        except Exception as e:
            self.logger.error(f"فشل في تنفيذ النموذج: {e}")
            raise ValueError(f"خطأ في تنفيذ النموذج: {e}")