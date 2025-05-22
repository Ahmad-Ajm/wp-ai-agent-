import os
import logging
import redis
import json
import requests
from openai import OpenAI
from datetime import timedelta

class AIHandler:
    def __init__(self, provider, api_key):
        self.provider = provider.lower().strip()
        self.api_key = api_key
        self.logger = logging.getLogger(__name__)
        self.cache_ttl = 3600  # 60 دقيقة

        # الاتصال بقاعدة Redis
        self.redis = redis.Redis.from_url(
            os.getenv('REDIS_URL', 'redis://localhost:6379'),
            decode_responses=True,
            socket_timeout=5
        )

        # تحميل البرومبت الأساسي (تعليمات الذكاء)
        prompt_path = os.path.join(os.path.dirname(__file__), "wp_prompt.txt")
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                self.base_prompt = f.read().strip()
        except Exception as e:
            self.logger.error(f"فشل في قراءة wp_prompt.txt: {e}")
            self.base_prompt = ""

        # تهيئة OpenAI فقط عند الطلب (لتوفير الموارد)
        self.openai_client = None

    def _get_cache_key(self, session_id):
        return f"ai_agent:{session_id}:history"

    def process_request(self, prompt, session_id):
        """
        توجيه الطلب إلى المزود المناسب والتعامل مع الأخطاء بدقة
        """
        try:
            if self.provider == 'gpt':
                return self._process_gpt(prompt, session_id)
            elif self.provider == 'deepseek':
                return self._process_deepseek(prompt)
            elif self.provider == 'claude':
                return self._process_claude(prompt)
            elif self.provider == 'gemini':
                return self._process_gemini(prompt)
            elif self.provider == 'mistral':
                return self._process_mistral(prompt)
            else:
                return f"#ERROR\nمزود الذكاء غير مدعوم: {self.provider}"
        except Exception as e:
            self.logger.error(f"Error in provider '{self.provider}': {e}", exc_info=True)
            return f"#ERROR\nفشل في المعالجة مع {self.provider}: {e}"

    def _process_gpt(self, prompt, session_id):
        """
        استخدام OpenAI Chat (gpt-4)
        """
        # إنشاء العميل فقط عند الحاجة (توفير للموارد)
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

        # ✅ تحقق من وجود 'choices' و'message'
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
        """
        DeepSeek API
        """
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
        # تحقق من وجود القيم المتوقعة
        if isinstance(resp_json, dict) and 'choices' in resp_json and resp_json['choices']:
            choice = resp_json['choices'][0]
            # أمان أكثر في جلب النتائج
            message = choice.get('message', {})
            content = message.get('content', None)
            if content:
                return content
            else:
                raise Exception(f"الرد غير مكتمل من deepseek: {message}")
        elif 'error' in resp_json:
            raise Exception(f"DeepSeek Error: {resp_json['error'].get('message', str(resp_json['error']))}")
        else:
            raise Exception(f"رد غير متوقع من deepseek: {resp_json}")

    def _process_claude(self, prompt):
        """
        Claude (Anthropic) API
        """
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
        response = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers=headers,
            json=data
        )
        resp_json = response.json()
        # فحص استجابة Claude الجديدة
        # https://docs.anthropic.com/claude/reference/messages_post
        if isinstance(resp_json, dict):
            # Claude 3 يعيد الرد في resp_json['content'][0]['text']
            if 'content' in resp_json and isinstance(resp_json['content'], list) and resp_json['content']:
                return resp_json['content'][0].get('text', '')
            elif 'error' in resp_json:
                raise Exception(f"Claude Error: {resp_json['error'].get('message', str(resp_json['error']))}")
            else:
                raise Exception(f"رد غير متوقع من Claude: {resp_json}")
        else:
            raise Exception(f"استجابة غير متوقعة من Claude: {resp_json}")

    def _process_gemini(self, prompt):
        """
        Google Gemini API
        """
        url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={self.api_key}'
        headers = {'Content-Type': 'application/json'}
        data = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        response = requests.post(url, headers=headers, json=data)
        resp_json = response.json()
        # Gemini يعيد النصوص في resp_json['candidates'][0]['content']['parts'][0]['text']
        if isinstance(resp_json, dict) and 'candidates' in resp_json and resp_json['candidates']:
            parts = resp_json['candidates'][0].get('content', {}).get('parts', [])
            if parts and 'text' in parts[0]:
                return parts[0]['text']
            else:
                raise Exception(f"رد غير مكتمل من Gemini: {parts}")
        elif 'error' in resp_json:
            raise Exception(f"Gemini Error: {resp_json['error'].get('message', str(resp_json['error']))}")
        else:
            raise Exception(f"رد غير متوقع من Gemini: {resp_json}")

    def _process_mistral(self, prompt):
        """
        Mistral API
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        data = {
            "model": "mistral-medium",
            "messages": [{"role": "user", "content": prompt}]
        }
        response = requests.post(
            'https://api.mistral.ai/v1/chat/completions',
            headers=headers,
            json=data
        )
        resp_json = response.json()
        # Mistral يعيد النتيجة مثل OpenAI
        if isinstance(resp_json, dict) and 'choices' in resp_json and resp_json['choices']:
            choice = resp_json['choices'][0]
            message = choice.get('message', {})
            content = message.get('content', None)
            if content:
                return content
            else:
                raise Exception(f"الرد غير مكتمل من Mistral: {message}")
        elif 'error' in resp_json:
            raise Exception(f"Mistral Error: {resp_json['error'].get('message', str(resp_json['error']))}")
        else:
            raise Exception(f"رد غير متوقع من Mistral: {resp_json}")
