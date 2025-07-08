import unittest
from unittest.mock import MagicMock, patch
from langchain.tools import Tool
from tools.rag_tool import RAGTool

# class TestRAGTool(unittest.TestCase):
#
#     @patch('langchain.chains.create_retrieval_chain')
#     @patch('langchain.chains.combine_documents.create_stuff_documents_chain')
#     @patch('tools.rag_tool.ChatBedrock')
#     @patch('tools.rag_tool.ChatPromptTemplate')
#     def setUp(self, mock_prompt_template, mock_chat_bedrock, mock_create_stuff_chain, mock_create_retrieval_chain):
#         """Set up a test instance of RAGTool before each test."""
#         self.mock_vector_store = MagicMock()
#         self.mock_retriever = MagicMock()
#         self.mock_vector_store.as_retriever.return_value = self.mock_retriever
#
#         self.mock_chain = MagicMock()
#         mock_create_retrieval_chain.return_value = self.mock_chain
#
#         self.rag_tool = RAGTool(self.mock_vector_store)
#
#     def test_initialization(self):
#         """Test that the RAGTool initializes correctly."""
#         self.assertIsInstance(self.rag_tool, RAGTool)
#         self.assertIsNotNone(self.rag_tool.chain)
#
#     def test_tool_invocation_with_documents(self):
#         """Test the tool's function when documents are found."""
#         self.mock_chain.invoke.return_value = {"answer": "This is the policy."}
#
#         langchain_tool = self.rag_tool.get_tool()
#         query = "What is the leave policy?"
#         response = langchain_tool.func(query)
#
#         self.assertEqual(response, "This is the policy.")
#         self.mock_chain.invoke.assert_called_once_with({"input": query})
#
#     def test_tool_invocation_no_documents(self):
#         """Test the tool's function when no documents are found."""
#         self.mock_chain.invoke.return_value = {"answer": "No relevant documents found."}
#
#         langchain_tool = self.rag_tool.get_tool()
#         query = "non-existent query"
#         response = langchain_tool.func(query)
#
#         self.assertEqual(response, "No relevant documents found.")
#         self.mock_chain.invoke.assert_called_once_with({"input": query})
#
#     def test_get_tool(self):
#         """Test the get_tool method."""
#         langchain_tool = self.rag_tool.get_tool()
#         self.assertIsInstance(langchain_tool, Tool)
#         self.assertEqual(langchain_tool.name, "HR_Policy_Search")
#         self.assertTrue(callable(langchain_tool.func))
#         self.assertIn("Use this tool to answer questions about HR policies", langchain_tool.description)
#
# if __name__ == '__main__':
#     unittest.main()