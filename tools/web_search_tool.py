from langchain.tools import Tool
from langchain_community.tools import DuckDuckGoSearchRun

class WebSearchTool:
    """
    A tool for performing web searches using DuckDuckGo.
    """
    def get_tool(self) -> Tool:
        """
        Returns the web search tool.
        This tool is useful for finding current information or topics outside
        of the company's internal knowledge base.
        """
        return Tool(
            name="Web_Search",
            func=DuckDuckGoSearchRun().run,
            description="A useful tool for searching the internet to find information on various topics, including current events, general knowledge, and external data."
        )