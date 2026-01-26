import ollama

modelfile='''
FROM llama3.2:latest
SYSTEM You are mario from super mario bros.
'''

ollama.create(model="example", modelfile=modelfile)

response = ollama.generate(
    model="example",
    prompt="5 questions for vex robotics judge to ask about engineering notebooks"
)
print(response)