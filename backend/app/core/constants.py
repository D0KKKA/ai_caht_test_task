"""Fixed code-level constants — not deployment-configurable.

These are implementation details of algorithms and API contracts.
For deployment-tunable values (keys, URLs, thresholds), see app/core/config.py.
"""

# --- LLM / OpenRouter HTTP headers ---
LLM_HTTP_REFERER = "https://github.com"
LLM_APP_TITLE = "AI Chat App"

# --- SSE stream parsing ---
SSE_DATA_PREFIX = "data: "
SSE_DATA_OFFSET = 6          # len("data: ")
SSE_DONE_SENTINEL = "[DONE]"

# --- LLM sampling temperatures ---
TEMPERATURE_SUMMARIZATION = 0.3
TEMPERATURE_TITLE_GENERATION = 0.5

# --- Context / summarization ---
MAX_SUMMARY_LENGTH = 2_000
SUMMARY_CONTEXT_LABEL = "[Previous context summary]:\n"
SUMMARY_LATER_LABEL = "\n\n[Later conversation]:\n"

# --- API / Content limits ---
MAX_MESSAGE_INPUT_CHARS = 10_000
MAX_ACCUMULATED_RESPONSE_CHARS = 50_000
TITLE_MAX_LENGTH = 60

# --- Pagination defaults ---
MESSAGES_PAGE_DEFAULT_LIMIT = 100
CHATS_PAGE_DEFAULT_LIMIT = 50
