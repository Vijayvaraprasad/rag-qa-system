from sentence_transformers import SentenceTransformer

# Try CUDA, fallback to CPU
try:
    model = SentenceTransformer(
        "sentence-transformers/all-MiniLM-L6-v2",
        device="cuda"
    )
except Exception:
    model = SentenceTransformer(
        "sentence-transformers/all-MiniLM-L6-v2",
        device="cpu"
    )

def embed_texts(texts: list[str]):
    return model.encode(
        texts,
        batch_size=32,
        convert_to_numpy=True,
        normalize_embeddings=True
    )
