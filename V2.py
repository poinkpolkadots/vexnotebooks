from llama_index.core import MultiModalVectorStoreIndex
from llama_index.embeddings.clip import ClipEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.core.schema import TextNode, ImageNode
from util import *

nodes = []

def add_data_from_pdf(path):
    nodes.append(TextNode(text=pdf_to_text(path=path)))
    #nodes.append(ImageNode(image_path=""))

index = MultiModalVectorStoreIndex(
    nodes,
    embed_model=ClipEmbedding(),
)

query_engine = index.as_query_engine(Ollama(
    model="llama3.2-vision",
    request_timeout=600.0,
))

response = query_engine.query("What does the chart show?")
print(response)