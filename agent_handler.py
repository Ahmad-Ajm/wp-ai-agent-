import os
import logging
import redis
import json
import requests
from openai import OpenAI

class AIHandler:
    def __init__(self, provider, api_key):
        self.provider = provider.lower().strip()
        self.api_key = api_key
        self.logger = logging.getLogger(__name__)
        self.cache_ttl = 3600

        self.redis = redis.Redis.from_url(
            os.getenv('REDIS_URL', 'redis://localhost:6379'),
            decode_responses=True,
            socket_timeout=5
        )

        prompt_path = os.path.join(os.path.dirname(__file__), "wp_prompt.txt")
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                self.base_prompt = f.read().strip()
        except Exception as e:
            self.logger.error(f"فشل في قراءة wp_prompt.txt: {e}")
            self.base_prompt = ""

        self.openai_client = None

    def _get_cache_key(self, session_id):
        return f"ai_agent:{session_id}:history"

    def process_request(self, prompt, session_id):
        try:
            if self.provider == 'gpt':
                return self._process_gpt(prompt, session_id)
            elif self.provider == 'deepseek':
                return self._process_deepseek(prompt)
            else:
                return f"#ERROR\nمزود الذكاء غير مدعوم: {self.provider}"
        except Exception as e:
            self.logger.error(f"Error in provider '{self.provider}': {e}", exc_info=True)
            return f"#ERROR\nفشل في المعالجة مع {self.provider}: {e}"

    def _process_gpt(self, prompt, session_id):
        if not self.openai_client:
            self.openai_client = OpenAI(api_key=self.api_key)

        cache_key = self._get_cache_key(session_id)
        history = []
        cached_history = self.redis.lrange(cache_key, 0, -1)
        if cached_history:
            history = [json.loads(msg) for msg in cached_history]

        history.append({"role": "user", "content": prompt})
        if len(history) > 10:
            history = history[-10:]

        system_prompt = f"{self.base_prompt}\n\n⚠️ **توجيهات إلزامية** ⚠️:\n- التزم بالبروبت."
        messages = [{"role": "system", "content": system_prompt}] + history[-6:]

        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.3,
            max_tokens=1000
        )

        if hasattr(response, 'choices') and len(response.choices) > 0 and hasattr(response.choices[0], 'message'):
            response_text = response.choices[0].message.content
        else:
            raise Exception(f"استجابة غير متوقعة من OpenAI: {response}")

        history.append({"role": "assistant", "content": response_text})
        self.redis.delete(cache_key)
        for msg in history:
            self.redis.rpush(cache_key, json.dumps(msg))
        self.redis.expire(cache_key, self.cache_ttl)

        return response_text


def _process_deepseek(self, prompt):
    headers = {'Authorization': f'Bearer {self.api_key}'}
    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post(
        'https://api.deepseek.com/v1/chat/completions',
        headers=headers,
        json=data
    )
    resp_json = response.json()

    if isinstance(resp_json, dict) and 'error' in resp_json:
        msg = resp_json['error'].get('message', 'Unknown DeepSeek Error')
        raise Exception(f"DeepSeek Error: {msg}")

    choices = resp_json.get('choices')
    if not isinstance(choices, list) or len(choices) == 0:
        raise Exception("رد غير متوقع من DeepSeek: لا توجد خيارات متاحة")

    choice = choices[0]
    message = choice.get('message')
    if not isinstance(message, dict) or 'content' not in message:
        raise Exception("الرد غير مكتمل من DeepSeek")

    return message['content']