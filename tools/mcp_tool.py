import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from langchain.tools import Tool

# If modifying these scopes, delete the token.pickle file.
SCOPES = ['https://www.googleapis.com/auth/documents.readonly']


class MCPTool:
    """Tool for connecting to Google Docs to answer insurance-related queries."""

    def __init__(self):
        self.creds = self._get_credentials()
        # Dictionary mapping insurance topics to document IDs
        self.topic_to_doc = {
            "insurance": os.environ.get("INSURANCE_DOC_KEY", "..."),
            "master_health_checkup": os.environ.get("MASTER_HEALTH_CHECKUP_DOC_KEY", "..."),
        }

    def _get_credentials(self):
        """Get valid user credentials from storage or user authentication."""
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'credentials.json', SCOPES)
                    creds = flow.run_local_server(port=0)
                    with open('token.pickle', 'wb') as token:
                        pickle.dump(creds, token)
                except Exception as e:
                    print(f"Error setting up Google credentials: {e}")
                    print("Please make sure 'credentials.json' is available.")
                    return None
        return creds

    def _fetch_document_content(self, doc_id):
        """
        Fetch content from a Google Doc.
        """
        if not self.creds:
            return "Google API credentials not configured."
        try:
            service = build('docs', 'v1', credentials=self.creds)
            document = service.documents().get(documentId=doc_id).execute()
            doc_content = ""
            for content in document.get('body').get('content'):
                if 'paragraph' in content:
                    for element in content.get('paragraph').get('elements'):
                        if 'textRun' in element:
                            doc_content += element.get('textRun').get('content')
            return doc_content
        except Exception as e:
            return f"Error fetching document: {e}"

    def _determine_relevant_doc(self, query):
        """Determine which document is most relevant to the query."""
        query = query.lower()
        if "health" in query or "checkup" in query or "medical" in query:
            return self.topic_to_doc["master_health_checkup"]
        else:
            return self.topic_to_doc["insurance"]

    def answer_insurance_query(self, query):
        """
        Answer insurance-related queries using Google Docs.
        """
        if not self.creds:
            return "Google Docs integration not configured. Please follow the setup instructions for the MCP Tool."
        doc_id = self._determine_relevant_doc(query)
        doc_content = self._fetch_document_content(doc_id)
        if "Error" in doc_content:
            return doc_content
        response = "## Insurance Information\n\n"
        response += f"Based on our insurance documentation, here's information relevant to your query about '{query}':\n\n"
        response += doc_content[:1500]
        if len(doc_content) > 1500:
            response += "\n...(content truncated)..."
        return response

    def get_tool(self):
        return Tool(
            name="Insurance_Query",
            func=self.answer_insurance_query,
            description="Answers questions about insurance policies, coverage, claims, health checkups, and other medical benefits by accessing specific documents. Use this for any insurance-related query."
        )