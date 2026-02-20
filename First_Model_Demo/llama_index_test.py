from llama_index.llms.ollama import Ollama
from llama_index.readers.schema.base import Document
from llama_index import VectorStoreIndex
from llmsherpa.readers import LayoutPDFReader

llmsherpa_api_url = "https://readers.llmsherpa.com/api/document/developer/parseDocument?renderFormat=all"
rubric_url = "./rubric/rubric.pdf" # also allowed is a file path e.g. /home/downloads/xyz.pdf
pdf_reader = LayoutPDFReader(llmsherpa_api_url)
rubric = pdf_reader.read_pdf(rubric_url)

llm = Ollama(
    model="llama3.2:3b",
    request_timeout=120.0,
    # Manually set the context window to limit memory usage
    context_window=8000,
)

# Chunk rubric PDF and allow LLM to use it in response
rubric_index = VectorStoreIndex([])
for chunk in rubric.chunks():
    rubric_index.insert(Document(text=chunk.to_context_text(), extra_info={}))
query_engine = rubric_index.as_query_engine()

# Let's run one query
response = query_engine.query("list all the tasks that work with bart")
print(response)