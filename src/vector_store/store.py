import os
import shutil
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore
from langchain_core.retrievers import BaseRetriever
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language

# Maps file extensions to LangChain Language enum for code-aware splitting.
# Files not in this map use the generic RecursiveCharacterTextSplitter.
_LANG_MAP: dict[str, Language] = {
    ".py":   Language.PYTHON,
    ".js":   Language.JS,
    ".jsx":  Language.JS,
    ".ts":   Language.JS,
    ".tsx":  Language.JS,
    ".java": Language.JAVA,
    ".go":   Language.GO,
    ".cs":   Language.CSHARP,
    ".cpp":  Language.CPP,
    ".c":    Language.C,
    ".rs":   Language.RUST,
    ".rb":   Language.RUBY,
}

_FALLBACK_SPLITTER = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)

def _get_splitter(file_path: str) -> RecursiveCharacterTextSplitter:
    """Returns a language-aware splitter for code files, generic splitter otherwise."""
    ext = os.path.splitext(file_path)[1].lower()
    lang = _LANG_MAP.get(ext)
    if lang:
        return RecursiveCharacterTextSplitter.from_language(
            language=lang, chunk_size=800, chunk_overlap=100
        )
    return _FALLBACK_SPLITTER

def ingest_repo(repo_name: str, file_paths: list[str], repo_root: str):
    """
    Ingests a list of files into a persistent ChromaDB collection dedicated to the repo.
    Each file is split with a language-aware splitter based on its extension.
    """
    print(f"[{repo_name}] Starting ingestion of {len(file_paths)} files...")

    # Extensions we are willing to read as text
    READABLE_EXTENSIONS = {
        ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".kt", ".go",
        ".cs", ".cpp", ".c", ".rs", ".rb", ".swift", ".scala",
        ".md", ".txt", ".rst", ".toml", ".yaml", ".yml", ".json",
        ".cfg", ".ini", ".env", ".gradle", ".xml", ".sh", ".bat",
        ".kts", ".pro",
    }

    def collect_paths(base_root: str, rel_path: str) -> list[str]:
        """Returns readable file paths under rel_path (handles both files and dirs)."""
        full = os.path.join(base_root, rel_path)
        if os.path.isfile(full):
            ext = os.path.splitext(full)[1].lower()
            if ext in READABLE_EXTENSIONS or ext == "":
                return [rel_path]
            return []
        if os.path.isdir(full):
            found = []
            for root, _, files in os.walk(full):
                for fname in files:
                    ext = os.path.splitext(fname)[1].lower()
                    if ext in READABLE_EXTENSIONS:
                        abs_f = os.path.join(root, fname)
                        found.append(os.path.relpath(abs_f, base_root))
            return found
        return []

    splits = []

    for relative_path in file_paths:
        for resolved_path in collect_paths(repo_root, relative_path):
            full_path = os.path.join(repo_root, resolved_path)
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    if not content.strip():
                        continue
                    doc = Document(
                        page_content=content,
                        metadata={"source": resolved_path, "repo_name": repo_name}
                    )
                    splitter = _get_splitter(resolved_path)
                    splits.extend(splitter.split_documents([doc]))
            except Exception as e:
                print(f"[{repo_name}] Failed to read {resolved_path}: {e}")

    if not splits:
        print(f"[{repo_name}] No documents to ingest.")
        return

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
        search_kwargs={"k": 8, "fetch_k": 20, "lambda_mult": 0.5}
    )
