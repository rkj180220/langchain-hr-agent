import unittest
from unittest.mock import patch, MagicMock
from langchain.tools import Tool
from tools.web_search_tool import WebSearchTool

# class TestWebSearchTool(unittest.TestCase):
#
#     @patch('tools.web_search_tool.DuckDuckGoSearchRun')
#     def setUp(self, mock_ddg_search_class):
#         """Set up a test instance of WebSearchTool before each test."""
#         self.mock_search_instance = MagicMock()
#         mock_ddg_search_class.return_value = self.mock_search_instance
#         self.web_search_tool = WebSearchTool()
#
#     def test_initialization(self):
#         """Test if the tool initializes correctly."""
#         self.assertIsInstance(self.web_search_tool, WebSearchTool)
#         self.assertIsNotNone(self.web_search_tool.tool)
#
#     def test_search_the_web_success(self):
#         """Test a successful web search."""
#         self.mock_search_instance.run.return_value = "GitHub was acquired by Microsoft in 2018."
#
#         langchain_tool = self.web_search_tool.get_tool()
#         result = langchain_tool.func("When was GitHub acquired?")
#
#         self.assertEqual(result, "GitHub was acquired by Microsoft in 2018.")
#         self.mock_search_instance.run.assert_called_once_with("When was GitHub acquired?")
#
#     def test_search_the_web_failure(self):
#         """Test web search when an exception occurs."""
#         self.mock_search_instance.run.side_effect = Exception("API Error")
#
#         langchain_tool = self.web_search_tool.get_tool()
#         with self.assertRaises(Exception) as context:
#             langchain_tool.func("query")
#
#         self.assertIn("API Error", str(context.exception))
#
#     def test_get_tool(self):
#         """Test the get_tool method."""
#         langchain_tool = self.web_search_tool.get_tool()
#         self.assertIsInstance(langchain_tool, Tool)
#         self.assertEqual(langchain_tool.name, "Web_Search")
#         self.assertEqual(langchain_tool.func, self.mock_search_instance.run)
#         self.assertIn("Use this tool for general web searches", langchain_tool.description)
#
# if __name__ == '__main__':
#     unittest.main()