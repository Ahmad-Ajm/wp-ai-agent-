import os
import logging
from openai import OpenAI

class DirectOpenAIHandler:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.logger = logging.getLogger(__name__)
        
        prompt_path = os.path.join(os.path.dirname(__file__), "wp_prompt.txt")
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                self.base_prompt = f.read().strip()
        except Exception as e:
            self.logger.error(f"فشل في قراءة wp_prompt.txt: {e}")
            self.base_prompt = ""

    def process_request(self, prompt: str) -> str:
        system_prompt = f"""
{self.base_prompt}

⚠️ **توجيهات إلزامية** ⚠️:
- الرد يجب أن يحتوي على واحد فقط من هذه الهياكل:
    #QUESTION
    ...
    --- أو ---
    #CONFIRM
    ...
    #CODE
    ...
- أي نص خارج الهيكل المحدد سيتسبب في فشل التنفيذ.
"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"خطأ في OpenAI API: {e}", exc_info=True)
            return "#ERROR\nفشل في المعالجة"
