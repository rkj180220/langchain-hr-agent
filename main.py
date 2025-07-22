import os
import logging
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_aws.chat_models import ChatBedrock
from langchain.memory import ConversationBufferMemory
from langfuse.callback import CallbackHandler

from nemoguardrails import RailsConfig
from nemoguardrails.integrations.langchain.runnable_rails import RunnableRails

from tools.rag_tool import CompanyKnowledgeTool
from tools.web_search_tool import WebSearchTool
from utils.vector_store import setup_vector_store
from dotenv import load_dotenv
import config

load_dotenv()

# Setup logging
logging.basicConfig(level=config.LOG_LEVEL, format=config.LOG_FORMAT)

def get_guardrails_config():
    """Setup and return guardrails configuration."""
    try:
        config_guard = RailsConfig.from_path("guardrails")
        return config_guard
    except Exception as e:
        logging.warning(f"Failed to load guardrails config: {e}")
        return None

def apply_input_guardrails(user_input, guardrails_config):
    """Apply input guardrails to user input."""
    if not guardrails_config:
        return True, user_input

    try:
        guardrails_runnable = RunnableRails(guardrails_config)
        # Check input moderation
        result = guardrails_runnable.invoke({"input": user_input})
        if isinstance(result, dict) and result.get("status") == "blocked":
            return False, "Input blocked by guardrails"
        return True, user_input
    except Exception as e:
        logging.warning(f"Input guardrails check failed: {e}")
        return True, user_input

def apply_output_guardrails(output, guardrails_config):
    """Apply output guardrails to agent response."""
    if not guardrails_config:
        return True, output

    try:
        guardrails_runnable = RunnableRails(guardrails_config)
        # Check output moderation
        result = guardrails_runnable.invoke({"input": output})
        if isinstance(result, dict) and result.get("status") == "blocked":
            return False, "Output blocked by guardrails"
        return True, output
    except Exception as e:
        logging.warning(f"Output guardrails check failed: {e}")
        return True, output

def main():
    """Main function to run the HR agent."""
    logging.info("🚀 Starting the HR AI Agent...")

    # Setup Langfuse handler
    handler = CallbackHandler(
        public_key=config.LANGFUSE_PUBLIC_KEY,
        secret_key=config.LANGFUSE_SECRET_KEY,
        host=config.LANGFUSE_HOST
    )

    # Setup NeMo Guardrails
    logging.info("🛡️ Setting up NeMo Guardrails...")
    guardrails_config = get_guardrails_config()

    # Setup the language model
    llm = ChatBedrock(
        model_id=config.LLM_MODEL_ID,
        model_kwargs={"temperature": config.LLM_TEMPERATURE},
        region_name=os.environ.get("AWS_REGION", config.AWS_REGION),
        callbacks=[handler],
    )

    # Setup tools
    logging.info("🛠️ Initializing tools...")
    vector_store = setup_vector_store(config.VECTOR_STORE_PATH)
    web_search_tool_instance = WebSearchTool()
    rag_tool = CompanyKnowledgeTool(vector_store, web_search_tool=web_search_tool_instance).get_tool()
    web_search_tool = web_search_tool_instance.get_tool()
    tools = [rag_tool, web_search_tool]
    logging.info("✅ Tools initialized.")

    # Create the agent prompt
    prompt_template = """
    You are Presidio's Internal Research Agent. Your goal is to provide accurate and helpful information to employees.
    Use the available tools to answer questions. Be conversational and remember the previous parts of the conversation.

    TOOLS:
    ------
    You have access to the following tools:
    {tools}

    To use a tool, please use the following format:
    ```
    Thought: Do I need to use a tool? Yes
    Action: The action to take. Should be one of [{tool_names}]
    Action Input: The input to the action
    Observation: The result of the action
    ```

    When you have a response to say to the Human, or if you do not need to use a tool, you MUST use the format:
    ```
    Thought: Do I need to use a tool? No
    Final Answer: [your response here]
    ```

    Begin!

    Previous conversation history:
    {chat_history}

    New input: {input}
    Thought: {agent_scratchpad}
    """
    prompt = PromptTemplate.from_template(prompt_template)

    # Setup memory
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    # Create the agent
    agent = create_react_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=True,
        max_iterations=config.AGENT_MAX_ITERATIONS,
        early_stopping_method=config.AGENT_EARLY_STOPPING_METHOD,
        handle_parsing_errors=True,
        callbacks=[handler]
    )

    logging.info("🤖 HR AI Agent is ready to chat!")

    # Start conversation loop
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ["exit", "quit"]:
            logging.info("👋 Exiting the HR AI Agent.")
            break

        try:
            # Apply input guardrails
            input_allowed, processed_input = apply_input_guardrails(user_input, guardrails_config)
            if not input_allowed:
                print("🛡️ Input blocked by guardrails.")
                continue

            response = agent_executor.invoke({"input": processed_input})
            output = response['output']

            # Apply output guardrails
            output_allowed, processed_output = apply_output_guardrails(output, guardrails_config)
            if not output_allowed:
                print("🛡️ Output blocked by guardrails.")
                continue

            print(f"\n🤖 **HR AI Agent:**\n{processed_output}\n")

        except Exception as e:
            error_message = str(e)
            if "Could not parse LLM output" in error_message or "Invalid Format" in error_message:
                print("\n🛡️ I cannot provide that information due to security constraints.")
            else:
                print(f"\n🛡️ Error: {error_message}")

def get_agent_executor():
    """Returns a ready-to-use agent_executor for programmatic use (e.g., evaluation)."""
    # Setup Langfuse handler
    handler = CallbackHandler(
        public_key=config.LANGFUSE_PUBLIC_KEY,
        secret_key=config.LANGFUSE_SECRET_KEY,
        host=config.LANGFUSE_HOST
    )

    # Setup the language model
    llm = ChatBedrock(
        model_id=config.LLM_MODEL_ID,
        model_kwargs={"temperature": config.LLM_TEMPERATURE},
        region_name=os.environ.get("AWS_REGION", config.AWS_REGION),
        callbacks=[handler],
    )

    # Setup tools
    vector_store = setup_vector_store(config.VECTOR_STORE_PATH)
    web_search_tool_instance = WebSearchTool()
    rag_tool = CompanyKnowledgeTool(vector_store, web_search_tool=web_search_tool_instance).get_tool()
    web_search_tool = web_search_tool_instance.get_tool()
    tools = [rag_tool, web_search_tool]

    # Create the agent prompt
    prompt_template = """
    You are Presidio's Internal Research Agent. Your goal is to provide accurate and helpful information to employees.
    Use the available tools to answer questions. Be conversational and remember the previous parts of the conversation.

    TOOLS:
    ------
    You have access to the following tools:
    {tools}

    To use a tool, please use the following format:
    ```
    Thought: Do I need to use a tool? Yes
    Action: The action to take. Should be one of [{tool_names}]
    Action Input: The input to the action
    Observation: The result of the action
    ```

    When you have a response to say to the Human, or if you do not need to use a tool, you MUST use the format:
    ```
    Thought: Do I need to use a tool? No
    Final Answer: [your response here]
    ```

    Begin!

    Previous conversation history:
    {chat_history}

    New input: {input}
    Thought: {agent_scratchpad}
    """
    prompt = PromptTemplate.from_template(prompt_template)
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    # Create agent with standard LLM (guardrails applied at input/output level)
    agent = create_react_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=True,
        max_iterations=config.AGENT_MAX_ITERATIONS,
        early_stopping_method=config.AGENT_EARLY_STOPPING_METHOD,
        handle_parsing_errors=True,
        callbacks=[handler]
    )

    return agent_executor

if __name__ == "__main__":
    main()