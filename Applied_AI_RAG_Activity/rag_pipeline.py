from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain.chains import RetrievalQA

# 1. Load and Split
print("1. Loading PDF and splitting into chunks...")
loader = PyPDFLoader("./data/document.pdf")
chunks = RecursiveCharacterTextSplitter(chunk_size=1000, 
chunk_overlap=100).split_documents(loader.load())
print(f"   -> Created {len(chunks)} chunks from the document.\n")

# 2. Vector Store
print("2. Generating embeddings using llama3 (This may take a few minutes if running on CPU!)...")
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=OllamaEmbeddings(model="llama3"),
    persist_directory="./chroma_db"
)
print("   -> Vector database created and saved to './chroma_db'.\n")

# 3. RAG Chain
print("3. Querying the llama3 model to summarize the document...")
llm = OllamaLLM(model="llama3")
rag_chain = RetrievalQA.from_chain_type(llm, retriever=vectorstore.as_retriever())
response = rag_chain.invoke("Summarize this document. What is the main topic of this file?")
print("\n--- FINAL SUMMARY ---")
print(response)
