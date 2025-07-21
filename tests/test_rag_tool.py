import unittest
from unittest.mock import MagicMock, patch
from tools.rag_tool import CompanyKnowledgeTool
from langchain.tools import Tool

class TestCompanyKnowledgeTool(unittest.TestCase):

    def setUp(self):
        """Set up a test instance of CompanyKnowledgeTool before each test."""
        self.mock_vector_store = MagicMock()
        self.mock_web_search_tool = MagicMock()

        # Mock the get_tool method on the web_search_tool instance
        self.mock_web_search_tool.get_tool.return_value = Tool(
            name="Web_Search",
            func=MagicMock(return_value="web search results"),
            description="A tool for searching the web."
        )

        self.rag_tool = CompanyKnowledgeTool(
            vector_store=self.mock_vector_store,
            web_search_tool=self.mock_web_search_tool
        )

    def test_initialization(self):
        """Test that the CompanyKnowledgeTool initializes correctly."""
        self.assertIsInstance(self.rag_tool, CompanyKnowledgeTool)
        self.assertIsNotNone(self.rag_tool.vector_store)
        self.assertIsNotNone(self.rag_tool.web_search_tool)

    def test_general_query_uses_vector_store(self):
        """Test that a general query uses the vector store."""
        mock_doc = MagicMock()
        mock_doc.page_content = "This is a document about company policy."
        self.mock_vector_store.similarity_search.return_value = [mock_doc]

        query = "What is the company policy on remote work?"
        response = self.rag_tool.search_company_knowledge(query)

        self.mock_vector_store.similarity_search.assert_called_once_with(query, k=3)
        self.assertIn("Company Information", response)
        self.assertIn("This is a document about company policy.", response)

    def test_fallback_to_web_search(self):
        """Test that the tool falls back to web search when no internal documents are found."""
        self.mock_vector_store.similarity_search.return_value = []

        query = "What are the latest industry trends in our sector?"
        response = self.rag_tool.search_company_knowledge(query)

        self.mock_vector_store.similarity_search.assert_called_once_with(query, k=3)
        self.mock_web_search_tool.get_tool.return_value.func.assert_called_once_with(query)
        self.assertIn("External Information", response)
        self.assertIn("web search results", response)

    def test_no_results_found(self):
        """Test the response when no information is found from any source."""
        self.mock_vector_store.similarity_search.return_value = []
        self.mock_web_search_tool.get_tool.return_value.func.return_value = ""

        query = "A query with no possible answer"
        response = self.rag_tool.search_company_knowledge(query)

        self.assertEqual(response, "I couldn't find any relevant information about this topic from company resources or external sources.")

    def test_get_tool(self):
        """Test the get_tool method."""
        langchain_tool = self.rag_tool.get_tool()
        self.assertIsInstance(langchain_tool, Tool)
        self.assertEqual(langchain_tool.name, "Company_Knowledge_Search")
        self.assertTrue(callable(langchain_tool.func))
        self.assertIn("Searches company knowledge sources", langchain_tool.description)

if __name__ == '__main__':
    unittest.main()
