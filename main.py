import os
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_aws.chat_models import ChatBedrock
from langchain.memory import ConversationBufferMemory
from tools.rag_tool import CompanyKnowledgeTool
from tools.web_search_tool import WebSearchTool
from tools.mcp_tool import MCPTool
from utils.vector_store import setup_vector_store
from dotenv import load_dotenv

load_dotenv()

def main():
    """Main function to run the HR agent."""
    print("🚀 Starting the HR AI Agent...")

    # Setup the language model
    llm = ChatBedrock(
        model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
        model_kwargs={"temperature": 0.1},
        region_name=os.environ.get("AWS_REGION", "us-west-2")
    )
    # Setup tools
    print("🛠️ Initializing tools...")
    vector_store = setup_vector_store("hr_docs")
    rag_tool = CompanyKnowledgeTool(vector_store).get_tool()
    web_search_tool = WebSearchTool().get_tool()
    mcp_tool = MCPTool().get_tool()
    tools = [rag_tool, web_search_tool, mcp_tool]
    print("✅ Tools initialized.")

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
        handle_parsing_errors=True
    )

    print("🤖 HR AI Agent is ready. How can I help you today?")

    # Main interaction loop
    while True:
        try:
            query = input("> ")
            if query.lower() in ["exit", "quit"]:
                print("👋 Goodbye!")
                break
            if query:
                # Manually manage history
                chat_history = memory.chat_memory.messages
                response = agent_executor.invoke({
                    "input": query,
                    "chat_history": chat_history
                })
                memory.save_context({"input": query}, {"output": response["output"]})
                print(f"\n🤖: {response['output']}\n")
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Goodbye!")
            break


if __name__ == "__main__":
    main()