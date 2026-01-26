import ollama
import time

start_time = time.time()

# response = ollama.chat(
#     model="gemma3",
#     messages=[
#         {"role": "user", "content": "5 questions for vex robotics judge to ask about engineering notebooks"}
#     ],
#     stream=True
# )
#
# for chunk in response:
#     print(chunk["message"]["content"], end="", flush=True)

modelfile = """
FROM gemma3
# system temperature, higher is more creative
PARAMETER temperature 1

# Set system prompt
SYSTEM You are acting as an assistant to VEX Robotics Judges. You will generate resources for them to help them in grading engineering notebooks. Write in a way such that a highschooler would understand what you are saying.
"""

ollama.create(model="gemma3_judge", modelfile=modelfile)

response = ollama.generate(
    model="gemma3_judge",
    prompt="5 questions for vex robotics judge to ask about engineering notebooks"
)

print(response["response"])

print("\n")

print("time: %s second" % (time.time() - start_time))