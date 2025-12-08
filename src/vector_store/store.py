import os
import shutil
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore
from langchain_core.retrievers import BaseRetriever
from langchain_text_splitters import RecursiveCharacterTextSplitter

def ingest_repo(repo_name: str, file_paths: list[str], repo_root: str):
    """
    Ingests a list of files into a persistent ChromaDB collection dedicated to the repo.
    """
    print(f"[{repo_name}] Starting ingestion of {len(file_paths)} files...")

    documents = []
    
    for relative_path in file_paths:
        full_path = os.path.join(repo_root, relative_path)
        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                if not content.strip():
                    continue
                
                doc = Document(
                    page_content=content,
                    metadata={"source": relative_path, "repo_name": repo_name}
                )
                documents.append(doc)
        except Exception as e:
            print(f"[{repo_name}] Failed to read {relative_path}: {e}")

    if not documents:
        print(f"[{repo_name}] No documents to ingest.")
        return

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(documents)
    print(f"[{repo_name}] Created {len(splits)} chunks.")

    persist_dir = os.path.join(os.getcwd(), "knowledge_base", repo_name)
    
    if os.path.exists(persist_dir):
        shutil.rmtree(persist_dir)

    Chroma.from_documents(
        documents=splits,
        embedding=OpenAIEmbeddings(model="text-embedding-3-small"),
        persist_directory=persist_dir
    )
    print(f"[{repo_name}] Successfully ingested into {persist_dir}")

def get_vector_store(repo_name: str) -> VectorStore:
    """
    Loads and returns the existing vector store for a given repository.
    """
    persist_dir = os.path.join(os.getcwd(), "knowledge_base", repo_name)
    if not os.path.exists(persist_dir):
        raise ValueError(f"No vector store found for {repo_name} at {persist_dir}")
        
    return Chroma(
        persist_directory=persist_dir,
        embedding_function=OpenAIEmbeddings(model="text-embedding-3-small")
    )

def get_retriever(vector_store: VectorStore) -> BaseRetriever:
    """
    Returns a retriever from the vector store.
    """
    return vector_store.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 8}
    )
