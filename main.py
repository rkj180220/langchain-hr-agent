import os
import logging
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_aws.chat_models import ChatBedrock
from langchain.memory import ConversationBufferMemory
from tools.rag_tool import CompanyKnowledgeTool
from tools.web_search_tool import WebSearchTool
from utils.vector_store import setup_vector_store
from dotenv import load_dotenv
import config

load_dotenv()

# Setup logging
logging.basicConfig(level=config.LOG_LEVEL, format=config.LOG_FORMAT)

def main():
    """Main function to run the HR agent."""
    logging.info("🚀 Starting the HR AI Agent...")

    # Setup the language model
    llm = ChatBedrock(
        model_id=config.LLM_MODEL_ID,
        model_kwargs={"temperature": config.LLM_TEMPERATURE},
        region_name=os.environ.get("AWS_REGION", config.AWS_REGION)
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
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=config.AGENT_MAX_ITERATIONS,
        early_stopping_method=config.AGENT_EARLY_STOPPING_METHOD
    )

    print("🤖 HR AI Agent is ready. How can I help you today?")

    # Main interaction loop
    while True:
        try:
            query = input("> ")
            if query.lower() in ["exit", "quit"]:
                print("👋 Goodbye!")
                break
            if query.strip():
                # Manually manage history
                chat_history = memory.chat_memory.messages
                try:
                    response = agent_executor.invoke({
                        "input": query,
                        "chat_history": chat_history
                    })
                    memory.save_context({"input": query}, {"output": response["output"]})
                    print(f"\n🤖: {response['output']}\n")
                except Exception as e:
                    logging.error(f"An error occurred during agent execution: {e}")
                    print("🤖: I'm sorry, but I encountered an error. Please try again.")
            else:
                print("🤖: Please enter a query.")
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Goodbye!")
            break


if __name__ == "__main__":
    main()