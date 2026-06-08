import os
import json
import chromadb
from sentence_transformers import SentenceTransformer
from chromadb.api.types import Documents, Embeddings, EmbeddingFunction

class SentenceTransformersEmbeddingFunction(EmbeddingFunction):
    """
    Embedding function for ChromaDB that loads the local all-MiniLM-L6-v2 model
    through sentence-transformers and performs local embedding without prefixes.
    """
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def __call__(self, input: Documents) -> Embeddings:
        texts = list(input)
        print(f"Encoding {len(texts)} query chunks using {self.model_name}...")
        vectors = self.model.encode(
            texts,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        return [vector.tolist() for vector in vectors]

def retrieve_top_chunks(query_string, k=5, db_path=None):
    """
    Accepts a query string and returns the top-k most relevant chunks 
    along with their metadata and source information.
    """
    if db_path is None:
        base_dir = os.path.dirname(__file__)
        db_path = os.path.join(base_dir, 'clean', 'chroma_db')

    if not os.path.exists(db_path):
        raise FileNotFoundError(f"ChromaDB database not initialized at: {db_path}. Run embed_chunks.py first.")
        
    client = chromadb.PersistentClient(path=db_path)
    embedding_fn = SentenceTransformersEmbeddingFunction()
    
    collection = client.get_collection(
        name="stocks_company_discussions",
        embedding_function=embedding_fn
    )
    
    # Cosine distance search
    results = collection.query(
        query_texts=[query_string],
        n_results=k
    )
    
    retrieved_chunks = []
    if results and 'documents' in results and results['documents']:
        ids = results['ids'][0]
        docs = results['documents'][0]
        metas = results['metadatas'][0]
        distances = results['distances'][0]
        
        for idx in range(len(docs)):
            meta = metas[idx] if isinstance(metas[idx], dict) else {}
            chunk_info = {
                'rank': idx + 1,
                'chunk_id': ids[idx],
                'text': docs[idx],
                'cosine_distance': distances[idx],
                'source': {
                    'source_doc': meta.get('source_doc', ids[idx]),
                    'chunk_position': int(meta.get('chunk_position', 0))
                }
            }
            retrieved_chunks.append(chunk_info)
            
    return retrieved_chunks

if __name__ == '__main__':
    # Test execution
    test_queries = [
        "What does BlackBerry do today?",
        "Why did Tesla stock decline recently?"
    ]
    
    query_results = {}
    base_dir = os.path.dirname(__file__)
    output_path = os.path.join(base_dir, 'clean', 'chunk_score.json')
    
    for query in test_queries:
        print("\n" + "="*80)
        print(f"QUERY: '{query}'")
        print("="*80)
        try:
            chunks = retrieve_top_chunks(query, k=5)
            query_results[query] = chunks
            for c in chunks:
                print(f"\n[Rank {c['rank']}] Distance (Cosine): {c['cosine_distance']:.4f}")
                print(f"Source Document: {c['source']['source_doc']}")
                print(f"Chunk Position: {c['source']['chunk_position']}")
                print(f"Full Text Content:\n{c['text']}")
                print("-"*40)
        except Exception as e:
            print(f"Error during query execution: {e}")
            query_results[query] = []
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as out_file:
        json.dump(query_results, out_file, indent=2, ensure_ascii=False)
    print(f"\nSaved retrieved chunk scores to: {output_path}")
