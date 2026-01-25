import ollama
import time

start_time = time.time()

response = ollama.chat(
    model="gemma3",
    messages=[
        {"role": "user", "content": "short (2-3 sentences) bio on JFK"}
    ],
    stream=True
)

for chunk in response:
    print(chunk["message"]["content"], end="", flush=True)

print("\n")

print("time: %s second" % (time.time() - start_time))