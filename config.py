import os

# config.py

# LLM Configuration
LLM_MODEL_ID = "anthropic.claude-3-5-sonnet-20240620-v1:0"
LLM_TEMPERATURE = 0.1
AWS_REGION = "us-west-2"

# Agent Configuration
AGENT_MAX_ITERATIONS = 5
AGENT_EARLY_STOPPING_METHOD = "force"

# Vector Store Configuration
VECTOR_STORE_PATH = "hr_docs"
VECTOR_STORE_K = 3

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'

# Langfuse Configuration
LANGFUSE_PUBLIC_KEY = os.environ.get("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = os.environ.get("LANGFUSE_SECRET_KEY")
LANGFUSE_HOST = os.environ.get("LANGFUSE_HOST", "http://localhost:3000")
