# CBORG AI Portal

CBORG is Berkeley Lab's multi-model AI platform. Free for all @lbl.gov, @es.net, @nersc.gov users. Costs for commercial models are paid by the IT Division.

## Access

| What | URL |
|------|-----|
| Chat interface | [chat.cborg.lbl.gov](https://chat.cborg.lbl.gov/) |
| Get API key | [CBorg Key Manager](https://cborg.lbl.gov/) |
| API examples | [cborg.lbl.gov/api_examples](https://cborg.lbl.gov/api_examples/) |
| Models list | [cborg.lbl.gov/models](https://cborg.lbl.gov/models/) |

## API Endpoint

```
https://api.cborg.lbl.gov          # Public (routed through Cloudflare)
https://api-local.cborg.lbl.gov    # Direct (LBL VPN/WiFi/Ethernet only, avoids Cloudflare rate limits)
```

The API is **OpenAI-compatible** — any code using the OpenAI Python SDK works by changing the base URL.

## Available Models

### Lab-Hosted (free, data stays within LBL network)

| Model ID | Description |
|----------|-------------|
| `lbl/cborg-chat:latest` | Llama with custom system prompt |
| `lbl/cborg-coder:latest` | Llama coding variant |
| `lbl/cborg-vision:latest` | Llama vision variant |
| `lbl/llama` | Base chat model |
| `lbl/qwen-coder` | Coding model |
| `lbl/qwen-vision` | Vision model |
| `lbl/nomic-embed-text` | Embedding model (for RAG) |

### Cloud-Hosted (commercial, IT Division pays)

| Model ID | Provider |
|----------|----------|
| `openai/gpt-4o`, `openai/gpt-4o-mini`, `openai/gpt-4.1` | OpenAI |
| `openai/o1`, `openai/o1-mini`, `openai/o3-mini` | OpenAI (reasoning) |
| `anthropic/claude-haiku`, `anthropic/claude-sonnet`, `anthropic/claude-opus` | Anthropic |
| `google/gemini-pro`, `google/gemini-flash`, `google/gemini-flash-lite` | Google |
| `xai/grok`, `xai/grok-mini` | xAI |
| `aws/llama-3.1-405b`, `aws/llama-3.1-70b`, `aws/llama-3.1-8b` | AWS Bedrock |
| `aws/command-r-plus-v1`, `aws/command-r-v1` | AWS Bedrock (Cohere) |

## Quick Start

```bash
pip install openai
export CBORG_API_KEY=your-key-here
```

```python
import openai
import os

client = openai.OpenAI(
    api_key=os.environ.get("CBORG_API_KEY"),
    base_url="https://api.cborg.lbl.gov",
)

response = client.chat.completions.create(
    model="lbl/llama",  # free, on-prem
    messages=[{"role": "user", "content": "What is CRISPR?"}],
)
print(response.choices[0].message.content)
```

To use a commercial model, just change the model string:

```python
response = client.chat.completions.create(
    model="anthropic/claude-sonnet",  # commercial, IT pays
    messages=[{"role": "user", "content": "What is CRISPR?"}],
)
```

## Embeddings (for RAG)

```python
response = client.embeddings.create(
    model="lbl/nomic-embed-text",
    input=["document text here", "another document"],  # must be a list
)
vectors = [d.embedding for d in response.data]
```

For queries, pass a string (not a list):
```python
response = client.embeddings.create(
    model="lbl/nomic-embed-text",
    input="query text here",  # string, not list
)
```

## Prompt Caching

OpenAI models support automatic (implicit) caching. Anthropic models require explicit `cache_control`:

```python
response = client.chat.completions.create(
    model="anthropic/claude-sonnet",
    messages=[
        {
            "role": "system",
            "content": "Your long system prompt here...",
            "cache_control": {"type": "ephemeral"},  # required for Anthropic
        },
        {"role": "user", "content": "Your question"},
    ],
)
```

## Restrictions

- **Not for public deployment**: Do not connect to any publicly accessible chatbot or interactive UI. Static/offline generated content is fine.
- **Rate limiting**: Production apps need rate limiting (`pip install ratelimit`) to avoid request rejection.
- **Data privacy**: Lab-hosted models keep data within LBL network. Commercial models send data externally but it is not saved or used for training.
- See [LBNL Guidance on Generative AI Tools](https://it.lbl.gov/ai/) for policy.
