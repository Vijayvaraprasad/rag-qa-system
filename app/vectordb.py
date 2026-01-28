import chromadb
import os

# Ensure data directory exists
os.makedirs("data/chroma_db", exist_ok=True)

# Use PersistentClient for data persistence
try:
    # Try newer ChromaDB API
    client = chromadb.PersistentClient(path="data/chroma_db")
except AttributeError:
    # Fallback for older versions
    from chromadb.config import Settings
    client = chromadb.Client(
        Settings(
            persist_directory="data/chroma_db",
            anonymized_telemetry=False,
            chroma_db_impl="duckdb+parquet"
        )
    )

collection = client.get_or_create_collection(
    name="documents",
    metadata={"hnsw:space": "cosine"}
)

def add_chunks(chunks, embeddings, source):
    ids = [f"{source}_{i}" for i in range(len(chunks))]
    metadatas = [{"source": source} for _ in chunks]

    collection.add(
        documents=chunks,
        embeddings=embeddings.tolist(),
        metadatas=metadatas,
        ids=ids
    )
    # ChromaDB v0.4+ auto-persists, so this is optional
    try:
        client.persist()
    except AttributeError:
        pass  # New ChromaDB versions auto-persist

def query_chunks(query_embedding, top_k=8):
    return collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=top_k
    )
