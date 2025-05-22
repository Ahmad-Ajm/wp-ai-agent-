# ✅ الاستيرادات الأساسية
import os
import logging
import redis
import json
import requests
from openai import OpenAI
from datetime import timedelta

# ✅ كلاس موحد لمعالجة الطلبات حسب المزود
class AIHandler:
    def __init__(self, provider, api_key):
        self.provider = provider
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

        if self.provider == 'gpt':
            self.client = OpenAI(api_key=self.api_key)
        elif self.provider == 'mistral':
            self.client = OpenAI(base_url="https://api.mistral.ai/v1", api_key=self.api_key)

    def _get_cache_key(self, session_id):
        return f"ai_agent:{session_id}:history"

    def process_request(self, prompt, session_id):
        if self.provider == 'gpt' or self.provider == 'mistral':
            return self._process_openai_compatible(prompt, session_id)
        elif self.provider == 'deepseek':
            return self._process_deepseek(prompt)
        elif self.provider == 'claude':
            return self._process_claude(prompt)
        elif self.provider == 'gemini':
            return self._process_gemini(prompt)
        else:
            return f"#ERROR\nمزود غير مدعوم: {self.provider}"

    def _process_openai_compatible(self, prompt, session_id):
        try:
            cache_key = self._get_cache_key(session_id)
            history = []
            cached_history = self.redis.lrange(cache_key, 0, -1)
            if cached_history:
                history = [json.loads(msg) for msg in cached_history]
            history.append({"role": "user", "content": prompt})
            if len(history) > 10:
                history = history[-10:]
            messages = [{"role": "system", "content": self.base_prompt}] + history[-6:]

            response = self.client.chat.completions.create(
                model="gpt-4" if self.provider == 'gpt' else "mistral-medium",
                messages=messages,
                temperature=0.3,
                max_tokens=1000
            )
            response_text = response.choices[0].message.content
            history.append({"role": "assistant", "content": response_text})
            self.redis.delete(cache_key)
            for msg in history:
                self.redis.rpush(cache_key, json.dumps(msg))
            self.redis.expire(cache_key, self.cache_ttl)
            return response_text
        except Exception as e:
            self.logger.error(f"خطأ في المعالجة: {e}", exc_info=True)
            return f"#ERROR\nفشل في المعالجة: {e}"

    def _process_deepseek(self, prompt):
        headers = {'Authorization': f'Bearer {self.api_key}'}
        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}]
        }
        response = requests.post('https://api.deepseek.com/v1/chat/completions', headers=headers, json=data)
        return response.json()['choices'][0]['message']['content']

    def _process_claude(self, prompt):
        headers = {
            'x-api-key': self.api_key,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json'
        }
        data = {
            "model": "claude-3-opus-20240229",
            "max_tokens": 1000,
            "messages": [{"role": "user", "content": prompt}]
        }
        response = requests.post('https://api.anthropic.com/v1/messages', headers=headers, json=data)
        return response.json()['content'][0]['text']

    def _process_gemini(self, prompt):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={self.api_key}"
        headers = {'Content-Type': 'application/json'}
        data = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        response = requests.post(url, headers=headers, json=data)
        return response.json()['candidates'][0]['content']['parts'][0]['text']
