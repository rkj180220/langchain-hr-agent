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
INSURANCE_DOC_KEY=doc_key_for_health_insurance_doc
MASTER_HEALTH_CHECKUP_DOC_KEY=doc_key_for_master_health_checkup_doc
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

### 4. Prepare Company Internal Documents

1. Create text files (.txt) or PDF files (.pdf) containing your company internal documents
2. Place them in the `data/hr_policies/` directory

### 5. Update Document IDs

In `tools/mcp_tool.py`, update the dictionary `self.topic_to_doc` with actual Google Document IDs:

```python
self.topic_to_doc = {
    "insurance": "your_health_insurance_doc_id",
    "master_health_checkup": "your_master_health_doc_id",
}
```

## Running the Agent

```bash
python main.py
```

## Test Prompts

Use these example queries to test different capabilities of the research agent.

### Insurance-Related Queries (MCP Tool)

- "What coverage does our health insurance policy provide for dental procedures?"
- "What is the process for scheduling a master health checkup through our company plan?"
- "How do I file an insurance claim for medical expenses incurred outside our network?"
- "Does our health insurance cover mental health counseling services?"

### HR Policy Queries (RAG Tool)

- "What is Presidio's policy on remote work arrangements?"
- "How many paid vacation days are employees entitled to per year?"
- "What is the company's maternity and paternity leave policy?"
- "What are the guidelines for requesting educational assistance or tuition reimbursement?"
- "What is our policy on performance reviews and promotions?"

### Industry Information Queries (Web Search Tool)

- "What are the current industry benchmarks for employee retention rates in IT consulting?"
- "What are the latest regulations on data protection that might affect our AI initiatives?"
- "How have IT consulting firms adapted their hiring strategies post-pandemic?"
- "What are the emerging cybersecurity compliance requirements for companies handling sensitive data?"

### Complex Multi-Tool Queries

- "How does our parental leave policy compare with the industry standard, and what legal changes might affect it in the coming year?"
- "What cybersecurity certifications should our IT team prioritize based on current market demands and our internal security policies?"
- "Based on our current remote work policy and industry trends, what adjustments should we consider to remain competitive in talent acquisition?"
- "Compare our Q2 2025 diversity hiring metrics with industry standards and recommend strategies to improve our recruiting pipeline for underrepresented groups."
- "Analyze the correlation between our cybersecurity hiring trends and the performance of our 'AI Governance Framework' marketing campaign."
- "What healthcare benefits are available to our remote employees across different states, and how does our remote work policy compare to industry benchmarks in the tech sector?"
- "Create a comprehensive onboarding plan for new cloud architects that incorporates our certification requirements, training programs, and insurance benefits."
- "How have our employee retention rates for military veterans compared to overall company retention since 2024?"
- "Evaluate the ROI of our professional development investments compared to industry benchmarks and recommend adjustments to our certification reimbursement policies."
- "What compliance considerations should we address when implementing AI-powered recruiting tools, based on our existing AI governance framework and current regulations?"

## Troubleshooting

- **Vector Store Errors**: Ensure you have .txt files in the data/hr_policies directory
- **Google Docs API Errors**: Check if credentials.json is properly set up
- **API Rate Limits**: If you encounter rate limits, reduce the frequency of queries
```