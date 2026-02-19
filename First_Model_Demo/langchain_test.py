# Test of using embeddings to work with Ollama through LangChain
import os
import getpass
from langchain_ollama import OllamaEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore

os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_API_KEY"] = getpass.getpass("Enter your LangSmith API key: ")

embeddings = OllamaEmbeddings(
    model="llama3.2:3b",
)

# Create a vector store with a sample text
text = "LangChain is the framework for building context-aware reasoning applications"

vectorstore = InMemoryVectorStore.from_texts(
    [text],
    embedding=embeddings,
)

# Use the vectorstore as a retriever
retriever = vectorstore.as_retriever()

# Retrieve the most similar text
retrieved_documents = retriever.invoke("What is LangChain?")

# Show the retrieved document's content
print(retrieved_documents[0].page_content)


# Test of general Ollama prompting with LangChain
from langchain_ollama import OllamaLLM

LLM_URL="http://localhost:11434/api/generate"
LLM_MODEL="llama3.2:3b"

chat_model = OllamaLLM(model=LLM_MODEL,
                       base_url=LLM_URL)

PdfPrompt = "write 5 questions for a vex robotics judge to \
            ask a student about their engineering journal. \
            print only the questions, in a numbered list."
SystemMessage = "You are acting as an assistant to VEX Robotics Judges. \
                You will generate resources for them to help them in grading \
                engineering notebooks. Write in a way such that a highschooler \
                would understand what you are saying. Do not grade or rank the \
                notebooks, act only as an assistant, generating questions to help \
                the actual judges with evaluating and grading notebooks."

messages = [PdfPrompt, SystemMessage,]
print(chat_model.invoke(messages))


# Test of PDF loading with LangChain document loaders
from langchain_community.document_loaders import PDFMinerLoader

file_path = "./rubric/rubric.pdf"
loader = PDFMinerLoader(file_path,
                        mode="single",
                        )
docs = loader.load()

file_path = "./rubric/rubric.pdf"
loader = PDFMinerLoader(file_path,
                        mode="single",
                        )
docs = loader.load()