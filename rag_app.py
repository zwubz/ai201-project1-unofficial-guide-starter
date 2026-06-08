import os
import json
import requests
import chromadb
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from chromadb.api.types import Documents, Embeddings, EmbeddingFunction

class SentenceTransformersEmbeddingFunction(EmbeddingFunction):
    """
    Embedding function that loads the local all-MiniLM-L6-v2 model
    via sentence-transformers and performs local embedding.
    """
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = SentenceTransformer(self.model_name)

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

def retrieve_top_chunks(query_string, k=5, db_path=None):
    """
    Retrieves the top-k document chunks and formats them as a context block.
    """
    if db_path is None:
        base_dir = os.path.dirname(__file__)
        db_path = os.path.join(base_dir, 'clean', 'chroma_db')

    if not os.path.exists(db_path):
        raise FileNotFoundError(f"ChromaDB database not initialized at: {db_path}.")
        
    client = chromadb.PersistentClient(path=db_path)
    embedding_fn = SentenceTransformersEmbeddingFunction()
    
    collection = client.get_collection(
        name="stocks_company_discussions",
        embedding_function=embedding_fn
    )
    
    results = collection.query(
        query_texts=[query_string],
        n_results=k
    )
    
    formatted_context = []
    raw_chunks = []
    
    if results and 'documents' in results and results['documents']:
        docs = results['documents'][0]
        metas = results['metadatas'][0]
        distances = results['distances'][0]
        
        for idx in range(len(docs)):
            source_doc = metas[idx].get('source_doc', 'Unknown')
            pos = metas[idx].get('chunk_position', 0)
            
            # Formulate the context block for the LLM with required source citation format
            formatted_context.append(
                f"--- (Source: {source_doc}, Chunk {pos}) ---\n"
                f"{docs[idx]}\n"
            )
            
            raw_chunks.append({
                'source_doc': source_doc,
                'chunk_position': pos,
                'distance': distances[idx],
                'text': docs[idx]
            })
            
    return "\n".join(formatted_context), raw_chunks

def generate_answer(query, context, api_key):
    """
    Calls the Groq API using requests to generate an answer constrained by the context.
    """
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    system_prompt = (
        "You are a helpful assistant. You must answer the user's question using ONLY "
        "the information provided in the documents below.\n\n"
        "If the documents do not contain enough information to answer, you must reply with exactly: "
        "\"I don't have enough information on that.\"\n\n"
        "For any fact you state from the documents, you MUST cite the source document name and the "
        "chunk position in parentheses, e.g., (Source: BlackBerry_(BB)_isn’t_about_Smartphones_anymore..md, Chunk 0). "
        "Do not make up any citations. Only cite documents that are explicitly provided in the context below. "
        "If the context is insufficient, do not attempt to answer and do not fabricate citations."
    )
    
    prompt = f"Context:\n{context}\n\nQuestion: {query}"
    
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        if response.status_code != 200:
            return f"Error communicating with Groq API: {response.status_code} - {response.text}"
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"Error communicating with Groq API: {e}"

def main():
    base_dir = os.path.dirname(__file__)
    dotenv_path = os.path.join(base_dir, '.env')
    load_dotenv(dotenv_path)
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY must be set in the environment or in the .env file.")
    
    print("="*80)
    print(" RAG Chat Application - Retail Investor Stocks Discussion")
    print("="*80)
    print("Database: ChromaDB (clean/chroma_db)")
    print("Embedding model: all-MiniLM-L6-v2")
    print("Generation model: Llama-3.1-8b-instant via Groq API")
    print("Type 'exit' or 'quit' to close the application.\n")

    while True:
        try:
            try:
                query = input("\nEnter your stock query: ").strip()
            except EOFError:
                print("\nReceived EOF. Exiting RAG application. Goodbye!")
                break
            if not query:
                continue
            if query.lower() in ('exit', 'quit'):
                print("Exiting RAG application. Goodbye!")
                break
                
            print("\n[Retrieving matching documents...]")
            context, chunks = retrieve_top_chunks(query, k=3)
            
            print(f"Found {len(chunks)} relevant chunks. Top source files:")
            for c in chunks:
                print(f" - (Source: {c['source_doc']}, Chunk {c['chunk_position']}) [Distance: {c['distance']:.4f}]")
            
            print("\n[Querying Groq LLM with constrained context...]")
            answer = generate_answer(query, context, api_key)
            
            print("\n" + "-"*80)
            print("ANSWER:")
            print("-"*80)
            print(answer)
            print("-"*80)
            
        except KeyboardInterrupt:
            print("\nExiting RAG application. Goodbye!")
            break
        except Exception as e:
            print(f"\nAn error occurred: {e}")

if __name__ == '__main__':
    main()
