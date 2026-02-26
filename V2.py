from llama_index.core import MultiModalVectorStoreIndex
from llama_index.embeddings.clip import ClipEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.core.schema import TextNode, ImageNode

nodes = []

nodes.append(TextNode(text="Revenue increased due to higher sales"))
nodes.append(ImageNode(image_path="chart.png"))

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