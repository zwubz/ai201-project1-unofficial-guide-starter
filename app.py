import os
import gradio as gr
from dotenv import load_dotenv
from rag_app import retrieve_top_chunks, generate_answer

def ask(question):
    """
    End-to-end RAG question answering: retrieves top chunks and queries Groq.
    """
    base_dir = os.path.dirname(__file__)
    dotenv_path = os.path.join(base_dir, '.env')
    load_dotenv(dotenv_path)
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return {
            "answer": "Error: GROQ_API_KEY is not set. Please set it in your .env file.",
            "sources": []
        }
        
    try:
        context, raw_chunks = retrieve_top_chunks(question, k=3)
        answer = generate_answer(question, context, api_key)
        
        # Extract sources cleanly
        sources = []
        for c in raw_chunks:
            sources.append(f"{c['source_doc']} (Chunk {c['chunk_position']})")
            
        return {
            "answer": answer,
            "sources": sources
        }
    except Exception as e:
        return {
            "answer": f"An error occurred during query execution: {e}",
            "sources": []
        }

def handle_query(question):
    if not question or not question.strip():
        return "Please enter a question.", "No sources retrieved."
    
    result = ask(question)
    if not result["sources"]:
        sources_str = "No sources cited."
    else:
        sources_str = "\n".join(f"• {s}" for s in result["sources"])
        
    return result["answer"], sources_str

# High-fidelity custom styling for a premium dark mode dashboard experience
custom_css = """
body {
    background-color: #0b0f19 !important;
    background-image: radial-gradient(circle at top right, rgba(99, 102, 241, 0.08), transparent 400px), 
                      radial-gradient(circle at bottom left, rgba(168, 85, 247, 0.08), transparent 400px) !important;
    font-family: 'Outfit', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
}
.gradio-container {
    max-width: 1050px !important;
    margin: 40px auto !important;
    background: rgba(17, 24, 39, 0.7) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border: 1px solid rgba(255, 255, 255, 0.06) !important;
    border-radius: 24px !important;
    padding: 36px !important;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7) !important;
}
.header-section {
    text-align: center;
    margin-bottom: 36px;
}
.header-section h1 {
    font-size: 2.4rem;
    font-weight: 800;
    letter-spacing: -0.025em;
    background: linear-gradient(135deg, #a5b4fc 0%, #c084fc 50%, #e879f9 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 10px;
}
.header-section p {
    color: #9ca3af;
    font-size: 1.1rem;
    font-weight: 400;
}
.ask-btn {
    background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%) !important;
    color: white !important;
    font-weight: 600 !important;
    border: none !important;
    border-radius: 12px !important;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.35) !important;
}
.ask-btn:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 20px rgba(99, 102, 241, 0.5) !important;
}
.ask-btn:active {
    transform: translateY(0) !important;
}
.gr-textbox, .gr-textarea {
    border-radius: 12px !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    background-color: rgba(31, 41, 55, 0.4) !important;
    color: #f3f4f6 !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
}
.gr-textbox:focus-within, .gr-textarea:focus-within {
    border-color: #818cf8 !important;
    box-shadow: 0 0 0 3px rgba(129, 140, 248, 0.15) !important;
}
.gr-form {
    border: none !important;
    background: transparent !important;
}
.gr-example-btn {
    background: rgba(31, 41, 55, 0.5) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 10px !important;
    color: #d1d5db !important;
    font-size: 0.9rem !important;
    transition: all 0.2s ease !important;
}
.gr-example-btn:hover {
    background: rgba(55, 65, 81, 0.8) !important;
    border-color: rgba(129, 140, 248, 0.3) !important;
    color: #ffffff !important;
    transform: translateX(2px) !important;
}
"""

theme = gr.themes.Soft(
    primary_hue="indigo",
    secondary_hue="purple",
    neutral_hue="slate",
    font=[gr.themes.GoogleFont("Outfit"), "sans-serif"]
).set(
    body_background_fill="#0b0f19",
    block_background_fill="rgba(17, 24, 39, 0.6)",
    block_border_color="rgba(255, 255, 255, 0.08)",
    input_background_fill="rgba(31, 41, 55, 0.4)",
    input_border_color="rgba(255, 255, 255, 0.1)"
)

with gr.Blocks(title="Retail Stocks RAG Dashboard") as demo:
    gr.HTML(
        '<div class="header-section">'
        '<h1>📈 Retail Stocks RAG Assistant</h1>'
        '<p>Ask questions about retail investor sentiments, stock updates, and discussion summaries derived from processed documents.</p>'
        '</div>'
    )

    with gr.Row(equal_height=True):
        with gr.Column(scale=5):
            gr.Markdown("### 🔍 Query Engine")
            inp = gr.Textbox(
                label="Your Question", 
                placeholder="e.g., What does BlackBerry do today?", 
                lines=2,
                elem_id="query-input"
            )
            btn = gr.Button("Ask Assistant", elem_classes="ask-btn")
            
            gr.Markdown("### 💡 Quick-Access Examples")
            gr.Examples(
                examples=[
                    "What does BlackBerry do today?",
                    "Why did Tesla stock decline recently?",
                    "What does retail think about Palantir?",
                    "Why did they sell AMD?"
                ],
                inputs=inp,
                label=None,
                examples_per_page=4
            )
            
        with gr.Column(scale=5):
            gr.Markdown("### 🤖 Assistant Response")
            answer = gr.Textbox(
                label="Answer", 
                lines=10, 
                placeholder="The assistant answer will appear here..."
            )
            sources = gr.Textbox(
                label="Retrieved from Documents", 
                lines=3,
                placeholder="Sources cited will appear here..."
            )

    btn.click(handle_query, inputs=inp, outputs=[answer, sources])
    inp.submit(handle_query, inputs=inp, outputs=[answer, sources])

if __name__ == "__main__":
    demo.launch(
        theme=theme,
        css=custom_css,
        server_name="127.0.0.1",
        server_port=7860,
        share=False
    )
