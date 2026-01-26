import ollama
import time

start_time = time.time()

response = ollama.chat(
    model="llama3.2:latest",
    messages=[
        {"role": "user", "content": "5 questions for vex robotics judge to ask about engineering notebooks"}
    ],
    stream=True
)

for chunk in response:
    print(chunk["message"]["content"], end="", flush=True)

print("\n")

print("time: %s second" % (time.time() - start_time))