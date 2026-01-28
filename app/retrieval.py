from app.embeddings import embed_texts
from app.vectordb import query_chunks

def retrieve_candidates(question, threshold=0.5):
    query_embedding = embed_texts([question])[0]
    results = query_chunks(query_embedding)

    candidates = []
    for doc, dist in zip(
        results["documents"][0],
        results["distances"][0]
    ):
        similarity = 1 - dist
        if similarity >= threshold:
            candidates.append(doc)

    return candidates
