"""OpenTelemetry GenAI semantic-convention attribute keys.

Single source of truth for the ``gen_ai.*`` keys AgentForge uses, so the SDK,
the ingest layer, and analytics all agree on naming.

Reference: OpenTelemetry GenAI semantic conventions.
"""

# System / provider that served the request (e.g. "openai", "anthropic").
GEN_AI_SYSTEM = "gen_ai.system"

# The model requested / used.
GEN_AI_REQUEST_MODEL = "gen_ai.request.model"
GEN_AI_RESPONSE_MODEL = "gen_ai.response.model"

# Operation name: "chat", "text_completion", "execute_tool", etc.
GEN_AI_OPERATION_NAME = "gen_ai.operation.name"

# Token usage.
GEN_AI_USAGE_INPUT_TOKENS = "gen_ai.usage.input_tokens"
GEN_AI_USAGE_OUTPUT_TOKENS = "gen_ai.usage.output_tokens"

# Agent / tool identity.
GEN_AI_AGENT_NAME = "gen_ai.agent.name"
GEN_AI_TOOL_NAME = "gen_ai.tool.name"

# Prompt / completion content (stored as attributes for replay).
GEN_AI_PROMPT = "gen_ai.prompt"
GEN_AI_COMPLETION = "gen_ai.completion"

# Span "kind" values used by AgentForge.
KIND_LLM = "llm"
KIND_TOOL = "tool"
KIND_AGENT = "agent"
KIND_RETRIEVAL = "retrieval"
KIND_CHAIN = "chain"
