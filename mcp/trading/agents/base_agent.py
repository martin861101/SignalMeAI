# agents/base_agent.py

from abc import ABC, abstractmethod
from typing import Any, Dict
from langchain_core.language_models import BaseLanguageModel

class BaseAgent(ABC):
    """
    An abstract base class for all agents in the system.

    This class defines the common interface that every agent must implement,
    ensuring consistency across the agentic framework. It requires each
    subclass to have an `execute` method, which serves as the main entry
    point for the agent's logic.
    """

    def __init__(self, name: str, llm: BaseLanguageModel):
        """
        Initializes the BaseAgent.

        Args:
            name (str): The name of the agent, used for logging and identification.
            llm (BaseLanguageModel): The language model instance that the agent will use.
        """
        self.name = name
        self.llm = llm
        print(f"--- Initializing Agent: {self.name} ---")

    @abstractmethod
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        The main entry point for the agent's execution logic.

        This method must be implemented by all subclasses. It takes the current
        application state as input and should return the modified state.

        Args:
            state (Dict[str, Any]): The current state of the trading graph.

        Returns:
            Dict[str, Any]: The updated state after the agent has performed its action.
        """
        pass

# --- Example of How to Use This Base Class ---
# You would put this code in your specific agent files, like `macroagent.py`.
# This is just for demonstration purposes here.

if __name__ == '__main__':
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.language_models.fake import FakeListChatModel

    # 1. Define a specific agent that inherits from BaseAgent
    class MacroAgent(BaseAgent):
        """A concrete implementation of BaseAgent for macroeconomic analysis."""

        def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
            """
            Executes the macroeconomic analysis logic.
            This is where you would build your chain and invoke it.
            """
            print(f"\n--- Executing Agent: {self.name} ---")
            print(f"Received state: {state}")

            # Create a prompt template (could also be loaded from a file)
            prompt_template = ChatPromptTemplate.from_template(
                "Analyze the following economic data: {data}"
            )

            # Create the LangChain runnable chain
            chain = prompt_template | self.llm

            # Invoke the chain with data from the state
            agent_response = chain.invoke({"data": state.get("economic_data", "")})

            # Update the state with the agent's response
            state["macro_outlook"] = agent_response
            print(f"Updated state with macro_outlook: {agent_response}")

            return state

    # 2. Example usage
    # Create a fake LLM for testing that will always return a canned response
    fake_llm = FakeListChatModel(responses=["Outlook is bullish due to strong CPI."])

    # Initialize your agent
    macro_agent = MacroAgent(name="Macro Forecaster", llm=fake_llm)

    # Define an initial state
    initial_state = {
        "economic_data": "CPI is up, unemployment is down.",
        "messages": []
    }

    # Execute the agent
    final_state = macro_agent.execute(initial_state)

    print("\n--- Final State ---")
    print(final_state)

