from llama_index.core.llms import ChatMessage, TextBlock, ImageBlock
from llama_index.llms.ollama import Ollama

def basic():
    print(
        Ollama(
            model="llama3.2-vision",
            request_timeout=600.0,
        ).chat([
            ChatMessage(
                role="system",
                content="you are not human.",
            ),
            ChatMessage(
                role="user",
                blocks=[
                    TextBlock(text="what is in this image?"),
                    ImageBlock(path="C:\\Users\\lawre\\OneDrive\\Pictures\\bg.jpg"),
                ],
            ),
        ])
    )

basic()