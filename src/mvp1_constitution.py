from pathlib import Path
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

from langchain_ollama import OllamaLLM
from langchain_classic.chains import RetrievalQA

load_dotenv()

RAW_DATA_DIR = Path("data/raw")
DB_DIR = Path("vectorstores/constitution_chroma")
PDF_PATH = RAW_DATA_DIR / "The_Constitution_of_Kenya_2010.pdf"

COLLECTION_NAME = "constitution_of_kenya_2010"

def build_or_load_vectordb(embeddings):
    # If DB already exists, load it (fast)
    if DB_DIR.exists() and any(DB_DIR.iterdir()):
        print(f"Loading existing vector store from {DB_DIR} ...")
        return Chroma(
            persist_directory=str(DB_DIR),
            embedding_function=embeddings,
            collection_name=COLLECTION_NAME,
        )

    # Else build it (first run)
    print(f"Loading PDF from {PDF_PATH}...")
    loader = PyPDFLoader(str(PDF_PATH))
    pages = loader.load()

    for p in pages:
        p.metadata["doc_title"] = COLLECTION_NAME

    print(f"Loaded {len(pages)} pages from the PDF.")

    print("Chunking the text...")
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(pages)
    print(f"Created {len(chunks)} chunks from the PDF.")

    print("Creating embeddings + vector store...")
    vectordb = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=str(DB_DIR),
    )
    print("Vector store ready ✅")
    return vectordb


def main():
    if not PDF_PATH.exists():
        raise FileNotFoundError(f"PDF file not found at {PDF_PATH}")

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    vectordb = build_or_load_vectordb(embeddings)

    print("Initializing Ollama (llama3.2)...")
    llm = OllamaLLM(model="llama3.2")

    retriever = vectordb.as_retriever(search_kwargs={"k": 5})

    qa = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
    )

    question = "What are the qualifications for a person to be elected as the president of Kenya?"
    print(f"\nAsking: {question}")

    result = qa.invoke({"query": question})

    print("\nAnswer:", result["result"])

    print("\nSource Documents:")
    for doc in result["source_documents"][:4]:
        meta = doc.metadata
        page = meta.get("page", "N/A")
        title = meta.get("doc_title", "N/A")
        if isinstance(page, int):
            page += 1
        print(f"- {title} (Page {page})")


if __name__ == "__main__":
    main()


      