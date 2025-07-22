import os
import logging
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_aws.chat_models import ChatBedrock
from langchain.memory import ConversationBufferMemory
from langfuse.callback import CallbackHandler

from guardrails.nemo_guardrails import setup_guardrails
import nemoguardrails
from nemoguardrails.integrations.langchain.runnable_rails import RunnableRails


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

    # Setup Langfuse handler
    handler = CallbackHandler(
        public_key=config.LANGFUSE_PUBLIC_KEY,
        secret_key=config.LANGFUSE_SECRET_KEY,
        host=config.LANGFUSE_HOST
    )

    # Setup NeMo Guardrails
    logging.info("🛡️ Setting up NeMo Guardrails...")
    guardrails = setup_guardrails()

    # Setup the language model
    llm = ChatBedrock(
        model_id=config.LLM_MODEL_ID,
        model_kwargs={"temperature": config.LLM_TEMPERATURE},
        region_name=os.environ.get("AWS_REGION", config.AWS_REGION),
        callbacks=[handler],
    )

    # Wrap the LLM with guardrails
    guardrails_runnable = RunnableRails(guardrails.config)
    print("guardrails details")
    print("Input flows:", guardrails.config.rails.input)
    print("Output flows:", guardrails.config.rails.output)
    print("Retrieval flows:", guardrails.config.rails.retrieval)
    # llm = guardrails_runnable | base_llm

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
            # Input guardrails
            print("DEBUG input repr:", repr(user_input))  # Add this line
            result = guardrails_runnable.invoke(input={"input": user_input}, flow="input_moderation")
            print("Guardrails result:", result)
            input_blocked = False
            for flow_type in ["input_moderation", "jailbreak_detection"]:
                result = guardrails_runnable.invoke(input={"input": user_input}, flow=flow_type)
                print("Guardrails result:", result)
                if isinstance(result, dict) and result.get("status") == "blocked":
                    print("🛡️ Input blocked by guardrails.")
                    input_blocked = True
                    break
            if input_blocked:
                continue

            response = agent_executor.invoke({"input": user_input}, {"callbacks": [handler]})
            output = response['output']

            # Output guardrails
            output_blocked = False
            for flow_type in ["fact_checking", "llm_moderation", "pii_detection"]:
                result = guardrails_runnable.invoke(input={"input": output}, flow=flow_type)
                print(f"Guardrails result for {flow_type}:", result)  # Debugging: see guardrails output
                if isinstance(result, dict) and result.get("status") == "blocked":
                    print("🛡️ Output blocked by guardrails.")
                    output_blocked = True
                    break
            if not output_blocked:
                print(f"\n🤖 **HR AI Agent:**\n{output}\n")
        except Exception as e:
            error_message = str(e)
            if "Could not parse LLM output" in error_message or "Invalid Format" in error_message:
                print("\n🛡️ I cannot provide that information due to security constraints.")
            else:
                print(f"\n🛡️ Error: {error_message}")

if __name__ == "__main__":
    main()