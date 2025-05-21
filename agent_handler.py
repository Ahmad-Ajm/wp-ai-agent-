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
        self.cache_ttl = 3600
        self.operation_log = []
        
        self.redis = redis.Redis.from_url(
            os.getenv('REDIS_URL'),
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
            self._add_log(f"خطأ في تحميل البرومبت: {str(e)}")

    def _get_cache_key(self, session_id: str) -> str:
        return f"ai_agent:{session_id}:history"

    def _add_log(self, log_entry: str):
        self.operation_log.append(f"{len(self.operation_log)+1}. {log_entry}")

    def process_request(self, prompt: str, session_id: str) -> dict:
        self.operation_log = []
        self._add_log("بدء معالجة الطلب")
        
        try:
            system_prompt = f"{self.base_prompt}\n\n⚠️ **توجيهات إلزامية** ⚠️:\n- التزم بالبروبت."
            cache_key = self._get_cache_key(session_id)
            self._add_log("إنشاء مفتاح التخزين المؤقت")
            
            history = []
            cached_history = self.redis.lrange(cache_key, 0, -1)
            if cached_history:
                history = [json.loads(msg) for msg in cached_history]
                self._add_log(f"تم استرداد {len(history)} رسالة من السجل")

            history.append({"role": "user", "content": prompt})
            self._add_log("تمت إضافة رسالة المستخدم إلى السجل")
            
            if len(history) > 10:
                history = history[-10:]
                self._add_log("تم تقليم السجل إلى آخر 10 رسائل")
            
            messages = [{"role": "system", "content": system_prompt}] + history[-6:]
            self._add_log("تم تجهيز الرسائل للنموذج")
            
            self._add_log("بدء الاتصال بخدمة الذكاء الاصطناعي")
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=0.3,
                max_tokens=1000
            )
            response_text = response.choices[0].message.content
            self._add_log("تم استلام الرد بنجاح")
            
            history.append({"role": "assistant", "content": response_text})
            self.redis.delete(cache_key)
            for msg in history:
                self.redis.rpush(cache_key, json.dumps(msg))
            self.redis.expire(cache_key, self.cache_ttl)
            self._add_log("تم تحديث التخزين المؤقت")
            
            return {
                "response": response_text,
                "log": "#Start-log\n" + "\n".join(self.operation_log) + "\n#End-log"
            }
        
        except Exception as e:
            self.logger.error(f"خطأ في المعالجة: {e}", exc_info=True)
            self._add_log(f"خطأ حرج: {str(e)}")
            return {
                "response": "#ERROR\nفشل في المعالجة",
                "log": "#Start-log\n" + "\n".join(self.operation_log) + "\n#End-log"
            }