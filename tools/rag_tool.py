from langchain.tools import Tool


class CompanyKnowledgeTool:
    """Tool for searching and retrieving information from multiple company knowledge sources."""

    def __init__(self, vector_store, mcp_tool=None, web_search_tool=None):
        self.vector_store = vector_store
        self.mcp_tool = mcp_tool
        self.web_search_tool = web_search_tool

    def _is_insurance_query(self, query):
        """Determine if a query is related to insurance."""
        insurance_keywords = [
            "insurance", "benefit", "coverage", "health", "medical",
            "dental", "vision", "claim", "policy", "deductible",
            "premium", "copay", "checkup"
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in insurance_keywords)

    def search_company_knowledge(self, query):
        """
        Search company knowledge sources using a priority-based approach:
        1. For insurance queries, use MCP Tool (Google Docs)
        2. For general company queries, use RAG with vector store
        3. If no relevant info found, fall back to web search

        Args:
            query: The search query

        Returns:
            String with relevant information from appropriate sources
        """
        results = []

        # For insurance queries, prioritize the MCP Tool
        if self._is_insurance_query(query) and self.mcp_tool:
            try:
                insurance_info = self.mcp_tool.answer_insurance_query(query)
                if "Error" not in insurance_info and "not configured" not in insurance_info:
                    results.append(insurance_info)
            except Exception as e:
                print(f"Error fetching insurance information: {e}")

        # For all queries, try searching internal documents with RAG
        # (This will be the primary source for non-insurance queries)
        if self.vector_store:
            try:
                docs = self.vector_store.similarity_search(query, k=3)
                if docs:
                    internal_info = "## Company Information\n\n"
                    for i, doc in enumerate(docs, 1):
                        internal_info += f"### Extract {i}\n{doc.page_content}\n\n"
                    results.append(internal_info)
            except Exception as e:
                print(f"Error searching vector store: {e}")

        # If no results from internal sources, try web search as fallback
        if not results and self.web_search_tool:
            try:
                web_search_func = self.web_search_tool.get_tool().func
                web_results = web_search_func(query)
                if web_results:
                    results.append(
                        f"## External Information\n\nNo internal company information found. Here's relevant information from external sources:\n\n{web_results[:1500]}")
            except Exception as e:
                print(f"Error performing web search: {e}")

        # If we still have no results, return a message
        if not results:
            return "I couldn't find any relevant information about this topic from company resources or external sources."

        # Combine results from different sources
        combined_result = "# Search Results\n\n"
        combined_result += "\n\n".join(results)

        return combined_result

    def get_tool(self):
        return Tool(
            name="Company_Knowledge_Search",
            func=self.search_company_knowledge,
            description="Searches company knowledge sources for information including HR policies, procedures, insurance details, and benefits. Uses appropriate sources based on query type and combines information when needed."
        )