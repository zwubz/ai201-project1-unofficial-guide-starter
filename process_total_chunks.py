import os
import re
import json

def load_documents(directory):
    """
    Traverses the directory, loads all Markdown files (excluding summary files),
    and separates metadata from content.
    """
    documents = []
    
    if not os.path.exists(directory):
        print(f"Error: Directory {directory} does not exist.")
        return documents

    for filename in os.listdir(directory):
        if filename.endswith('.md'):
            filepath = os.path.join(directory, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    raw_text = f.read()
                
                # Separate metadata block from body content
                parts = raw_text.split('---', 1)
                metadata_block = parts[0]
                content_body = parts[1] if len(parts) > 1 else ""
                
                # Extract specific metadata fields using regex
                title_match = re.search(r'^# (.*)', metadata_block, re.MULTILINE)
                author_match = re.search(r'- \*\*Author\*\*: u/(.*)', metadata_block)
                date_match = re.search(r'- \*\*Date\*\*: (.*)', metadata_block)
                url_match = re.search(r'- \*\*Source URL\*\*: (.*)', metadata_block)
                
                meta = {
                    'title': title_match.group(1).strip() if title_match else filename.replace('.md', ''),
                    'author': author_match.group(1).strip() if author_match else 'Unknown',
                    'date': date_match.group(1).strip() if date_match else 'Unknown',
                    'url': url_match.group(1).strip() if url_match else 'Unknown',
                    'filename': filename
                }
                
                documents.append({
                    'metadata': meta,
                    'raw_body': content_body
                })
            except Exception as e:
                print(f"Failed to read {filename}: {e}")
                
    return documents

def clean_content(raw_text):
    """
    Cleans the document text for indexing.
    - Standardizes spaces and newlines.
    - Strips leading/trailing spaces from lines.
    - Retains Markdown links and structure but removes noise.
    """
    # Replace multiple spaces/tabs with a single space
    text = re.sub(r'[ \t]+', ' ', raw_text)
    
    # Replace three or more newlines with exactly two newlines (to keep paragraph breaks clean)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Strip spaces from the beginning and end of each line
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)
    
    # Remove leading/trailing spaces of the whole block
    return text.strip()

def chunk_document(doc, chunk_size=1000, overlap=150):
    """
    Splits cleaned content into chunks with sliding-window overlap.
    Prepends metadata to each chunk to prevent entity context loss.
    """
    metadata = doc['metadata']
    content = clean_content(doc['raw_body'])
    
    # Define injected header for context resolution
    header = f"[Title: {metadata['title']} | Author: u/{metadata['author']} | URL: {metadata['url']}]\nContext Content:\n"
    header_len = len(header)
    
    # We want the total chunk length (header + text) to fit inside chunk_size.
    # Therefore, the available size for the text content is:
    available_size = chunk_size - header_len
    if available_size <= 200:
        # Fallback if header is unusually long
        available_size = chunk_size // 2
        
    chunks = []
    content_len = len(content)
    
    start = 0
    while start < content_len:
        end = start + available_size
        
        # If we are not at the end of the text, try to align split on a space or newline boundary
        if end < content_len:
            # Look back up to 100 characters for a whitespace/newline
            boundary = -1
            for offset in range(100):
                char = content[end - offset]
                if char in (' ', '\n'):
                    boundary = end - offset
                    break
            if boundary != -1:
                end = boundary
        
        chunk_text = content[start:end].strip()
        full_chunk = header + chunk_text
        
        chunks.append({
            'chunk_id': f"{metadata['filename']}_chunk_{len(chunks)}",
            'text': full_chunk,
            'metadata': metadata
        })
        
        # Slide start index back by the overlap size
        start = end - overlap
        if start >= content_len - overlap:
            break
            
    return chunks

def main():
    base_dir = os.path.dirname(__file__)
    directory = os.path.join(base_dir, 'clean')
    print(f"Loading documents from: {directory}")
    
    docs = load_documents(directory)
    print(f"Loaded {len(docs)} documents.")
    
    all_chunks = []
    for doc in docs:
        cleaned_len = len(clean_content(doc['raw_body']))
        chunks = chunk_document(doc, chunk_size=1000, overlap=150)
        all_chunks.extend(chunks)
        print(f" - Document '{doc['metadata']['title']}' (Length: {cleaned_len} chars) split into {len(chunks)} chunks.")
        
    print(f"\nTotal generated chunks: {len(all_chunks)}")
    
    # Save a preview of the first 3 chunks to console
    print("\n--- Previewing First 3 Chunks ---")
    for i, c in enumerate(all_chunks[:3], 1):
        print(f"\n[Chunk #{i} | ID: {c['chunk_id']}]")
        print(c['text'])
        print("-" * 50)
        
    # Write all chunks to a JSON file named total_chunks.json
    out_file = os.path.join(directory, 'total_chunks.json')
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, indent=4, ensure_ascii=False)
    print(f"\nSuccessfully wrote all chunks as JSON to: {out_file}")

if __name__ == '__main__':
    main()
