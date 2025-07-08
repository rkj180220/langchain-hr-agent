# Presidio Internal Research Agent

An intelligent research agent built with LangChain to help Presidio employees access information from multiple sources:

- **HR Policy Documents**: Using RAG (Retrieval-Augmented Generation) with AWS Bedrock
- **Google Docs**: For insurance-related queries via MCP Tool
- **Web Search**: For industry benchmarks, trends, and regulatory updates

## Features

- **Multi-source information retrieval**: Get answers from internal documents and external sources
- **Natural language queries**: Ask questions in plain English
- **Contextual answers**: Receive relevant information that addresses specific needs

## Prerequisites

- Python 3.8+
- AWS Credentials configured for use with Boto3
- Google Cloud project (for Google Docs API)

## Setup Instructions

### 1. Environment Setup with UV

```bash
# Install UV if not already installed
pip install uv

# Clone the repository and change to the project directory
git clone <repository-url>
cd research-agent

# Create a virtual environment with UV
uv venv

# Activate the virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file in the project root:

```
AWS_ACCESS_KEY_ID="your_aws_access_key_id"
AWS_SECRET_ACCESS_KEY="your_aws_secret_access_key"
AWS_REGION="your_aws_region" # e.g., us-east-1
```

### 3. Google Docs API Setup (for MCP Tool)

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the Google Docs API
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Application type: Desktop application
   - Download the JSON file and save it as `credentials.json` in the project root

### 4. Prepare HR Policy Documents

1. Create text files (.txt) containing your HR policies
2. Place them in the `data/hr_policies/` directory

### 5. Update Document IDs

In `tools/mcp_tool.py`, update the dictionary `self.topic_to_doc` with actual Google Document IDs:

```python
self.topic_to_doc = {
    "health": "your_health_insurance_doc_id",
    "liability": "your_liability_insurance_doc_id",
    "property": "your_property_insurance_doc_id",
    "general": "your_general_insurance_doc_id"
}
```

## Running the Agent

```bash
python main.py
```

## Example Queries

- "Summarize all customer feedback related to our Q1 marketing campaigns."
- "Compare our current hiring trend with industry benchmarks."
- "Find relevant compliance policies related to AI data handling."
- "What is our health insurance policy on dental coverage?"
- "Are there any HR policies regarding remote work?"

## Troubleshooting

- **Vector Store Errors**: Ensure you have .txt files in the data/hr_policies directory
- **Google Docs API Errors**: Check if credentials.json is properly set up
- **API Rate Limits**: If you encounter rate limits, reduce the frequency of queries
```