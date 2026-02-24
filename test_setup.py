import os
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

# Test GROQ connection
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {"role": "user", "content": "Say 'NBA Agent is ready!' and nothing else"}
    ]
)

print("✅ Setup successful!")
print(f"Response: {response.choices[0].message.content}")