import requests
import json
from datetime import datetime

start = datetime.now()

url = "http://localhost:11434/api/generate"

payload = {
    "model": "notebook-judge",
    "prompt": "write 5 questions for a vex robotics judge to ask a student about their engineering journal. print only the questions, in a numbered list.",
}

response = requests.post(url, json=payload, stream=False)

if response.status_code == 200:
    print("Generated Text:" + "\n", end=" ", flush=True)
    # Iterate over the streaming response
    for line in response.iter_lines():
        if line:
            # Decode the line and parse the JSON
            decoded_line = line.decode("utf-8")
            result = json.loads(decoded_line)
            # Get the text from the response
            generated_text = result.get("response", "")
            print(generated_text, end="", flush=True)
else:
    print("Error:", response.status_code, response.text)

print("\n" + "\n" + "Runtime:")
print(datetime.now() - start)