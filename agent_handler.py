import os
import logging
from langchain.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, Tool
from langchain.agents.agent_types import AgentType
from langchain.memory import ConversationBufferMemory

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
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        self.agent = self._initialize_agent()

    def _initialize_agent(self):
        tools = [
            Tool(
                name="generate_php",
                func=self._generate_code,
                description="يولّد شيفرة PHP بناءً على الوصف"
            ),
        ]
        return initialize_agent(
            tools,
            self.llm,
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            memory=self.memory,
            verbose=True
        )

    def _generate_code(self, prompt: str) -> str:
        return self.llm.predict(prompt)

    def process_request(self, prompt: str, action: str = "generate_php") -> str:
        try:
            self.logger.info(f"تشغيل وكيل LangChain مع الإجراء: {action}")
            full_prompt = f"{self.base_prompt}\n{prompt}" if self.base_prompt else prompt
            result = self.agent.run(full_prompt)
            return result
        except Exception as e:
            self.logger.error(f"فشل وكيل LangChain: {e}")
            raise ValueError(f"خطأ في تنفيذ الوكيل: {e}")