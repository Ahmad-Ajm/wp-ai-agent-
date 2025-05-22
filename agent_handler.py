import os
import logging
import redis
import json
from openai import OpenAI
from datetime import timedelta

class DirectOpenAIHandler:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.logger = logging.getLogger(__name__)
        self.cache_ttl = 3600  # 60 دقيقة
        
        # إعداد Redis
        self.redis = redis.Redis.from_url(
            os.getenv('REDIS_URL', 'redis://localhost:6379'),
            decode_responses=True,
            socket_timeout=5
        )
        
        # تحميل البرومبت
        prompt_path = os.path.join(os.path.dirname(__file__), "wp_prompt.txt")
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                self.base_prompt = f.read().strip()
        except Exception as e:
            self.logger.error(f"فشل في قراءة wp_prompt.txt: {e}")
            self.base_prompt = ""

    def _get_cache_key(self, session_id: str) -> str:
        return f"ai_agent:{session_id}:history"

    def process_request(self, prompt: str, session_id: str) -> str:
        system_prompt = f"""
{self.base_prompt}

⚠️ **توجيهات إلزامية** ⚠️:
- التزم بالبروبت.
"""
        try:
            cache_key = self._get_cache_key(session_id)
            
            # استرجاع تاريخ المحادثة
            history = []
            cached_history = self.redis.lrange(cache_key, 0, -1)
            if cached_history:
                history = [json.loads(msg) for msg in cached_history]

            # إضافة الرسالة الجديدة
            history.append({"role": "user", "content": prompt})
            
            # الحفاظ على أخر 10 رسائل
            if len(history) > 10:
                history = history[-10:]
            
            # إعداد الرسائل للذكاء الاصطناعي
            messages = [{"role": "system", "content": system_prompt}] + history[-6:]
            
            # طلب الرد من الذكاء الاصطناعي
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=0.3,
                max_tokens=1000
            )
            response_text = response.choices[0].message.content
            
            # تحديث التخزين المؤقت
            history.append({"role": "assistant", "content": response_text})
            self.redis.delete(cache_key)
            for msg in history:
                self.redis.rpush(cache_key, json.dumps(msg))
            self.redis.expire(cache_key, self.cache_ttl)
            
            return response_text
        
        except Exception as e:
            self.logger.error(f"خطأ في المعالجة: {e}", exc_info=True)
            return f"#ERROR\nفشل في المعالجة: {e}"
