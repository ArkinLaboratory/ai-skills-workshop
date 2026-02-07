"""
Simplest Claude API call using anthropic SDK.

This teaches:
- How to initialize the Anthropic client
- How to make a basic API call
- How to extract the response text

Prerequisites:
    pip install anthropic
    export ANTHROPIC_API_KEY="your-key-here"

Run:
    python 01-basic-api-call.py
"""

import os
from anthropic import Anthropic

# Initialize the client (reads ANTHROPIC_API_KEY from environment)
client = Anthropic()

# Make a simple API call
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": "Tell me about bacteriophages and their role in microbiology research.",
        }
    ],
)

# Extract and print the response
print(message.content[0].text)
