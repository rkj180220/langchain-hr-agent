from nemoguardrails import LLMRails, RailsConfig

# Function to setup guardrails
def setup_guardrails():
    # Load rails configuration
    config = RailsConfig.from_path("./guardrails")
    rails = LLMRails(config, verbose=True)
    return rails