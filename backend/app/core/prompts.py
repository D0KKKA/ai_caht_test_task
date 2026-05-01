"""System prompts used by LLM service calls.

All prompt text lives here — one place to read, review, and edit.
"""

# Main assistant persona — sent as the system message in every chat completion.
SYSTEM_PROMPT = (
    "You are a helpful AI assistant. "
    "Provide clear, concise, and accurate answers. "
    "Use markdown formatting when appropriate."
)

# Instruction prompt for the summarization task (user turn).
SUMMARIZATION_PROMPT = (
    "Summarize the following conversation segment concisely, "
    "preserving key facts and context. Keep it under 150 words."
)

# System role for the summarizer LLM call.
SUMMARIZER_ROLE_PROMPT = (
    "You are a conversation summarizer. "
    "Create a concise summary preserving key facts and context."
)

# Instruction prompt for chat title generation (system turn).
TITLE_GENERATION_PROMPT = (
    "Generate a concise 3-5 word title for a conversation based on the first message. "
    "Reply with ONLY the title, no quotes, no punctuation."
)
