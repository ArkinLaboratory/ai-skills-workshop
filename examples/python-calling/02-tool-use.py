"""
Claude with tool_use: define a reverse_complement tool and handle the tool_use loop.

This teaches:
- How to define tools that Claude can call
- How to check stop_reason == "tool_use"
- How to extract tool_use blocks from the response
- How to execute the tool and send results back
- How to maintain conversation context

Prerequisites:
    pip install anthropic
    export ANTHROPIC_API_KEY="your-key-here"

Run:
    python 02-tool-use.py
"""

import os
import json
from anthropic import Anthropic

# Initialize the client
client = Anthropic()

# Define our tool
tools = [
    {
        "name": "reverse_complement",
        "description": "Returns the reverse complement of a DNA sequence",
        "input_schema": {
            "type": "object",
            "properties": {
                "sequence": {
                    "type": "string",
                    "description": "DNA sequence (ATCG)",
                }
            },
            "required": ["sequence"],
        },
    }
]


def reverse_complement(sequence: str) -> str:
    """Reverse complement a DNA sequence."""
    complement = {"A": "T", "T": "A", "C": "G", "G": "C"}
    return "".join(complement.get(base, "N") for base in reversed(sequence))


def process_tool_call(tool_name: str, tool_input: dict) -> str:
    """Execute a tool and return the result."""
    if tool_name == "reverse_complement":
        sequence = tool_input["sequence"]
        result = reverse_complement(sequence)
        return result
    else:
        return f"Unknown tool: {tool_name}"


# Maintain conversation history
messages = [
    {
        "role": "user",
        "content": "What is the reverse complement of ATCGATCG? Explain what you're doing.",
    }
]

print("User: What is the reverse complement of ATCGATCG? Explain what you're doing.")
print()

# Agentic loop: keep asking Claude until it stops using tools
while True:
    # Call Claude with tools enabled
    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        tools=tools,
        messages=messages,
    )

    # Check if Claude wants to use a tool
    if response.stop_reason == "tool_use":
        # Find the tool_use block in the response
        tool_use_block = None
        for block in response.content:
            if block.type == "tool_use":
                tool_use_block = block
                break

        if tool_use_block:
            tool_name = tool_use_block.name
            tool_input = tool_use_block.input

            print(f"Claude is using tool: {tool_name}")
            print(f"Input: {json.dumps(tool_input, indent=2)}")
            print()

            # Execute the tool
            tool_result = process_tool_call(tool_name, tool_input)
            print(f"Tool result: {tool_result}")
            print()

            # Add Claude's response (with tool_use) to messages
            messages.append({"role": "assistant", "content": response.content})

            # Add the tool result back to messages
            messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use_block.id,
                            "content": tool_result,
                        }
                    ],
                }
            )

            # Continue the loop—Claude will now respond based on the tool result
    else:
        # Claude is done with tool_use, extract and print the final response
        final_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                final_text += block.text

        print("Claude's final response:")
        print(final_text)
        break
