"""
Same as 01-basic-api-call.py but using CBORG (openai SDK).

CBORG (Community Biomedical Research GPU) provides free on-premises LLMs.
This example shows how to:
- Use the openai SDK with a different base_url
- Call free models like lbl/llama
- Optionally swap to commercial anthropic/claude-sonnet for better results

Prerequisites:
    pip install openai anthropic

Run:
    python 03-cborg-api-call.py

Note: CBORG models are free and on-premises (lower quality), while
Claude models are commercial but higher quality. The difference is just
the base_url and model name.
"""

import os
from openai import OpenAI

# Initialize the CBORG client (using openai SDK with different base_url)
client = OpenAI(
    api_key="dummy",  # CBORG doesn't require API keys
    base_url="https://api.cborg.lbl.gov",
)

print("Using CBORG free model (llama)...")
print()

# Make an API call with CBORG
message = client.chat.completions.create(
    model="lbl/llama",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": "Tell me about bacteriophages and their role in microbiology research.",
        }
    ],
)

# Extract and print the response
print(message.choices[0].message.content)
print()
print("---")
print()

# To use Claude Sonnet (commercial) instead, you would do:
# (requires ANTHROPIC_API_KEY in environment)
print("Switching to Claude Sonnet (commercial) model...")
print()

from anthropic import Anthropic

# Use anthropic client (doesn't need openai SDK)
claude_client = Anthropic()

message = claude_client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": "Tell me about bacteriophages and their role in microbiology research.",
        }
    ],
)

print(message.content[0].text)
