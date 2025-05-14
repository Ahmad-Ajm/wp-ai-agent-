import logging
from langchain.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, Tool
from langchain.agents.agent_types import AgentType
from langchain.prompts import MessagesPlaceholder
from langchain.memory import ConversationBufferMemory

class AgentHandler:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.logger = logging.getLogger(__name__)
        self.llm = ChatOpenAI(model="gpt-4o", openai_api_key=self.api_key)
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        self.agent = self._initialize_agent()

    def _initialize_agent(self):
        tools = [
            Tool(
                name="Code Generator",
                func=self._generate_code,
                description="Use this tool to generate PHP code for WordPress tasks based on user prompt."
            )
        ]

        return initialize_agent(
            tools=tools,
            llm=self.llm,
            agent=AgentType.OPENAI_FUNCTIONS,
            memory=self.memory,
            agent_kwargs={
                "system_message": "أنت مساعد ذكي لإنشاء أكواد ووردبريس نظيفة وآمنة. لا تشرح، فقط أنشئ الكود.",
                "extra_prompt_messages": [MessagesPlaceholder(variable_name="chat_history")],
            },
            verbose=True
        )

    def _generate_code(self, prompt: str) -> str:
        return self.llm.predict(prompt)

    def process_request(self, prompt: str, action: str = "generate_php") -> str:
        try:
            self.logger.info(f"LangChain Agent executing action: {action}")
            result = self.agent.run(prompt)
            return result
        except Exception as e:
            self.logger.error(f"LangChain agent failed: {str(e)}")
            raise ValueError(f"Agent execution error: {str(e)}")
