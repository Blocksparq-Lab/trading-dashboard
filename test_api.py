import os
from anthropic import Anthropic

# Load API key
api_key = open(os.path.expanduser('~/.config/trading-ai/.env')).read().split('=')[1].strip()

# Initialize client
client = Anthropic(api_key=api_key)

# Test call
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=300,
    messages=[{
        "role": "user",
        "content": "You are a trading assistant. Summarize this: The S&P 500 showed strength Friday, closing above 5800. Tech led gains with NVDA up 4%."
    }]
)

print("API TEST SUCCESSFUL")
print("Response:", response.content[0].text[:200])
