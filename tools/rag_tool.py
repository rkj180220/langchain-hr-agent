from langchain.tools import Tool


class RAGTool:
    """Tool for searching and retrieving information from HR policy documents."""

    def __init__(self, vector_store):
        self.vector_store = vector_store

    def search_policies(self, query):
        """
        Search the HR policy documents for relevant information.

        Args:
            query: The search query

        Returns:
            String with relevant policy information
        """
        if not self.vector_store:
            return "Vector store not initialized. Please ensure HR policy documents are available."

        # Search the vector store for relevant documents
        docs = self.vector_store.similarity_search(query, k=3)

        if not docs:
            return "No relevant information found in HR policies."

        # Combine the results with proper formatting
        result = "## Relevant HR Policy Information\n\n"
        for i, doc in enumerate(docs, 1):
            result += f"### Extract {i}\n{doc.page_content}\n\n"

        return result

    def get_tool(self):
        return Tool(
            name="HR_Policy_Search",
            func=self.search_policies,
            description="Searches general HR policy documents for information on company policies, procedures, code of conduct, and performance management. For insurance or health benefits, use the 'Insurance_Query' tool."
        )