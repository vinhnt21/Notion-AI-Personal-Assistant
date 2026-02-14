"""LangChain agent that orchestrates LLM reasoning and Notion tool usage.

Uses LangGraph's prebuilt create_react_agent (LangChain v1.2+).
"""

from typing import Optional, List, Dict, Any
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
from core.llm_factory import LLMFactory
from core.prompt_templates import CHAT_SYSTEM_PROMPT
from integrations.notion_mcp import NotionMCP
from integrations.notion_tools import NotionToolFactory


class NotionAgent:
    """LangGraph ReAct agent wired to Notion tools"""

    def __init__(
        self,
        llm_provider: str = "openai",
        llm_model: Optional[str] = None,
        temperature: float = 0.7,
        notion_api_key: Optional[str] = None,
    ):
        # LLM
        self.llm = LLMFactory.create_llm(
            provider=llm_provider,
            model=llm_model,
            temperature=temperature,
        )

        # Notion integration
        self.notion_mcp = NotionMCP(api_key=notion_api_key)

        # Tools
        tool_factory = NotionToolFactory(self.notion_mcp)
        self.tools = tool_factory.create_tools()

        # Conversation history
        self._history: List[BaseMessage] = []

        # Build LangGraph agent
        self.agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
        )

    def chat(self, user_input: str) -> str:
        """Process user input and return the agent's response"""
        try:
            # Build messages list with system prompt + history + new message
            messages: List[BaseMessage] = [
                SystemMessage(content=CHAT_SYSTEM_PROMPT),
                *self._history,
                HumanMessage(content=user_input),
            ]

            # Invoke the agent
            result = self.agent.invoke({"messages": messages})

            # Extract the final AI response
            output_messages = result.get("messages", [])
            if output_messages:
                response = output_messages[-1].content
            else:
                response = "No response generated."

            # Update history
            self._history.append(HumanMessage(content=user_input))
            self._history.append(output_messages[-1])

            # Trim history to avoid context overflow
            max_history = 40  # 20 turns
            if len(self._history) > max_history:
                self._history = self._history[-max_history:]

            return response

        except Exception as e:
            return f"❌ Error: {str(e)}"

    def clear_memory(self):
        """Reset conversation history"""
        self._history.clear()
