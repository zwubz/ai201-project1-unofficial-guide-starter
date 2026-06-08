import os
import json
import chromadb
from sentence_transformers import SentenceTransformer
from chromadb.api.types import Documents, Embeddings, EmbeddingFunction

class SentenceTransformersEmbeddingFunction(EmbeddingFunction):
    """
    Embedding function for ChromaDB that loads the local all-MiniLM-L6-v2 model
    through sentence-transformers and performs local embedding.
    """
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def __call__(self, input: Documents) -> Embeddings:
        texts = list(input)
        print(f"Encoding {len(texts)} chunks using {self.model_name}...")
        vectors = self.model.encode(
            texts,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        return [vector.tolist() for vector in vectors]

def main():
    base_dir = os.path.dirname(__file__)
    chunks_path = os.path.join(base_dir, 'clean', 'total_chunks.json')
    db_path = os.path.join(base_dir, 'clean', 'chroma_db')
    
    print(f"Loading chunks from: {chunks_path}")
    if not os.path.exists(chunks_path):
        print(f"Error: Chunks file not found at {chunks_path}")
        return

    with open(chunks_path, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
        
    print(f"Loaded {len(chunks)} chunks from JSON.")

    # Initialize ChromaDB persistent client
    os.makedirs(db_path, exist_ok=True)
    print(f"Connecting to ChromaDB at: {db_path}")
    client = chromadb.PersistentClient(path=db_path)
    
    # Local sentence-transformers embedding function
    embedding_fn = SentenceTransformersEmbeddingFunction()
    
    collection_name = "stocks_company_discussions"
    
    # Check if collection already exists, and delete it to reload cleanly
    try:
        client.delete_collection(collection_name)
        print(f"Deleted existing collection '{collection_name}' for clean reload.")
    except Exception:
        pass

    print(f"Creating new collection: '{collection_name}' (Space: Cosine)")
    collection = client.create_collection(
        name=collection_name,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"}
    )
    
    ids = []
    documents = []
    metadatas = []
    
    for c in chunks:
        ids.append(c['chunk_id'])

        source_doc = None
        chunk_position = 0
        metadata = c.get('metadata') if isinstance(c, dict) else None
        if isinstance(metadata, dict):
            source_doc = metadata.get('source_doc') or metadata.get('filename')
            try:
                chunk_position = int(metadata.get('chunk_position', 0))
            except (TypeError, ValueError):
                chunk_position = 0

        if not source_doc:
            chunk_id = c.get('chunk_id', '')
            if '_chunk_' in chunk_id:
                source_doc, chunk_position_str = chunk_id.rsplit('_chunk_', 1)
                try:
                    chunk_position = int(chunk_position_str)
                except ValueError:
                    chunk_position = 0
            else:
                source_doc = chunk_id

        documents.append(c['text'])

        metadatas.append({
            'source_doc': source_doc or 'Unknown',
            'chunk_position': chunk_position
        })
        
    print(f"Embedding and loading {len(chunks)} chunks into ChromaDB via all-MiniLM-L6-v2...")
    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )
    
    print(f"Successfully loaded database! Total records stored: {collection.count()}")

if __name__ == '__main__':
    main()
