import unittest
from unittest.mock import patch, MagicMock
from langchain.tools import Tool
from tools.mcp_tool import MCPTool

class TestMCPTool(unittest.TestCase):

    @patch.dict('os.environ', {
        "INSURANCE_DOC_KEY": "test_insurance_doc_id",
        "MASTER_HEALTH_CHECKUP_DOC_KEY": "test_health_doc_id"
    })
    @patch('tools.mcp_tool.MCPTool._get_credentials')
    def setUp(self, mock_get_credentials):
        """Set up a test instance of MCPTool before each test."""
        mock_get_credentials.return_value = "dummy_credentials"
        self.tool = MCPTool()

    def test_initialization(self):
        """Test if the tool initializes correctly."""
        self.assertEqual(self.tool.creds, "dummy_credentials")
        self.assertEqual(self.tool.topic_to_doc["insurance"], "test_insurance_doc_id")
        self.assertEqual(self.tool.topic_to_doc["master_health_checkup"], "test_health_doc_id")

    def test_determine_relevant_doc_health(self):
        """Test if the correct doc is selected for health-related queries."""
        doc_id = self.tool._determine_relevant_doc("What about my health checkup?")
        self.assertEqual(doc_id, "test_health_doc_id")

    def test_determine_relevant_doc_insurance(self):
        """Test if the correct doc is selected for general insurance queries."""
        doc_id = self.tool._determine_relevant_doc("What is the policy coverage?")
        self.assertEqual(doc_id, "test_insurance_doc_id")

    @patch('tools.mcp_tool.build')
    def test_fetch_document_content_success(self, mock_build):
        """Test successful fetching of document content."""
        mock_service = MagicMock()
        mock_documents = MagicMock()
        mock_get = MagicMock()
        mock_get.execute.return_value = {
            'body': {
                'content': [
                    {'paragraph': {'elements': [{'textRun': {'content': 'Hello '}}]}},
                    {'paragraph': {'elements': [{'textRun': {'content': 'World'}}]}}
                ]
            }
        }
        mock_documents.get.return_value = mock_get
        mock_service.documents.return_value = mock_documents
        mock_build.return_value = mock_service

        content = self.tool._fetch_document_content("any_doc_id")
        self.assertEqual(content, "Hello World")
        mock_build.assert_called_once_with('docs', 'v1', credentials=self.tool.creds)

    @patch('tools.mcp_tool.build')
    def test_fetch_document_content_error(self, mock_build):
        """Test handling of an API error during document fetching."""
        mock_build.side_effect = Exception("API Error")
        content = self.tool._fetch_document_content("any_doc_id")
        self.assertEqual(content, "Error fetching document: API Error")

    def test_fetch_document_no_creds(self):
        """Test fetch behavior when credentials are not available."""
        self.tool.creds = None
        content = self.tool._fetch_document_content("any_doc_id")
        self.assertEqual(content, "Google API credentials not configured.")

    @patch('tools.mcp_tool.MCPTool._fetch_document_content')
    def test_answer_insurance_query(self, mock_fetch):
        """Test the main query answering function."""
        mock_fetch.return_value = "This is the document content."
        query = "Tell me about my policy."
        response = self.tool.answer_insurance_query(query)

        self.assertIn("## Insurance Information", response)
        self.assertIn(f"relevant to your query about '{query}'", response)
        self.assertIn("This is the document content.", response)

    def test_get_tool(self):
        """Test the get_tool method."""
        langchain_tool = self.tool.get_tool()
        self.assertIsInstance(langchain_tool, Tool)
        self.assertEqual(langchain_tool.name, "Insurance_Query")
        self.assertEqual(langchain_tool.func, self.tool.answer_insurance_query)
        self.assertIn("Answers questions about insurance policies", langchain_tool.description)

if __name__ == '__main__':
    unittest.main()