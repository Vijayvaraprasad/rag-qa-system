import nltk
from PyPDF2 import PdfReader
from nltk.tokenize import sent_tokenize
from app.embeddings import embed_texts
from app.vectordb import add_chunks

# Download NLTK punkt tokenizer
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')

def semantic_chunk(text, max_tokens=500):
    sentences = sent_tokenize(text)
    chunks, current = [], ""

    for sent in sentences:
        if len((current + sent).split()) > max_tokens:
            chunks.append(current.strip())
            current = sent
        else:
            current += " " + sent

    if current:
        chunks.append(current.strip())

    return chunks

def process_document(file_path: str):
    if file_path.endswith(".pdf"):
        reader = PdfReader(file_path)
        text = " ".join(p.extract_text() for p in reader.pages)
    else:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

    chunks = semantic_chunk(text)
    embeddings = embed_texts(chunks)

    add_chunks(
        chunks=chunks,
        embeddings=embeddings,
        source=file_path
    )
