# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

<!-- What topic or category of knowledge does your system cover?
     Why is this knowledge valuable, and why is it hard to find through official channels?
     Example: "Student reviews of CS professors at [university] — useful because official
     course descriptions don't reflect teaching style, exam difficulty, or workload." -->
     My topic of knowledge is retail investors on Reddit discussing stocks. This knowledge is valuable and hard to find through official channels because traditional financial reports contain jargon and does not capture the behaviors of masses. Retail discussion on channels like reddit offer organic data of everyday shares showing real-time sentiment, emotional reaction, personal experience, and perspective that are absent in mainstream reporting.

---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | Reddit | Amazon is considering abandoning the USPS and establishing a competing postal service. | https://www.reddit.com/r/stocks/comments/1pe5t5i/amazon_is_considering_abandoning_the_usps_and/ |
| 2 | Reddit | Reddit stock drops 6% after Meta announces a Facebook Groups app | https://www.reddit.com/r/stocks/comments/1tl1m3q/reddit_stock_drops_6_after_meta_announces_a/ |
| 3 | Reddit | BlackBerry (BB) isn’t about Smartphones anymore. | https://www.reddit.com/r/stocks/comments/1tn0giy/blackberry_bb_isnt_about_smartphones_anymore/ |
| 4 | Reddit | Getting out of Palantir | https://www.reddit.com/r/stocks/comments/1s2t7ys/getting_out_of_palantir/ |
| 5 | Reddit | I’ve had AMD since 2023 and just sold | https://www.reddit.com/r/stocks/comments/1nzk4mm/ive_had_amd_since_2023_and_just_sold/ |
| 6 | Reddit | Microsoft freefall | https://www.reddit.com/r/stocks/comments/1s5d4l7/microsoft_freefall/ |
| 7 | Reddit | This is a disaster of epic proportion” Trump vs. Musk turns into a $150B Tesla bloodbath | https://www.reddit.com/r/stocks/comments/1l56hgo/this_is_a_disaster_of_epic_proportion_trump_vs/ |
| 8 | Reddit | Trump's Japan tariffs actually harm US auto companies, like $F and $GM. | https://www.reddit.com/r/stocks/comments/1mcbijm/trumps_japan_tariffs_actually_harm_us_auto/ |
| 9 | Reddit | GOOGL up 130% since April lows ... why do you think it’s climbing so fast? | https://www.reddit.com/r/stocks/comments/1p67m4g/googl_up_130_since_april_lows_why_do_you_think/ |
| 10 | Reddit | Okay Micron has gone crazy | https://www.reddit.com/r/stocks/comments/1tod7ce/okay_micron_has_gone_crazy/ |

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:**
Chunk size is 1000 characters.

**Overlap:**
Overlap is 150.

**Why these choices fit your documents:**
The documents I found were paragraphs with a range of 400-1200 characters. The chunk size of 1000 gave a better distance score than with the lower chunk size. It ended up being an issue when I had a smaller chunk so I revised back to the chunk size described now. 

**Final chunk count:**
20

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:**
all-MiniLM-L6-v2

**Production tradeoff reflection:**
Initially I wanted to use nomic to try out the model but using that required asymmetric sentence which was outside of the project instructions. Ended up using all-MiniLM-L6-v2 for using a symmetric sentence-similarity mode without needing to distinguish between search queries and documents. 


---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**
The system prompt establishes a strict boundary, preventing the model from utilizing its general pre-training knowledge to answer the query:
"You must answer the user's question using ONLY the information provided in the documents below."
To handle cases where the retrieved document chunks do not contain the answer, the prompt designates a specific, zero-knowledge fallback string.

**How source attribution is surfaced in the response:**
Every assertion made by the model must be tied back to a specific document and chunk. For any fact or opinion you state from the documents, you MUST cite the source document name and the chunk position.
---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What did Ross Gerber call Elon Musk's actions and TSLA's recent stock moves? | Ross Gerber called it a "disaster." Tesla's stock dropped 14% in one day, wiping out $150B in market cap. | Ross Gerber called Elon Musk's actions a "disaster" (Source:...) | Relevant | Accurate |
| 2 | What does BlackBerry do today? | They make a software called QNX, it is currently installed in 275 million vehicles. | BlackBerry has stopped making smartphones and has shifted its focus to software. | Relevant | Accurate |
| 3 | What do people really think about Meta new move with forum? | People think Facebook have been around for decades but did not affect how people used Reddit | I don't have enough information on that. | Off-target  | Inaccurate |
| 4 | Why does retail want to get out of Palantir? | People from Reddit believes Palantir is generally bad for humanity and dislikes their stock dilution practices. | I don't have enough information on that. | Off-target  | Inaccurate |
| 5 | What do people think about Trump's 15% tariffs on cars imported from Japan related to US auto companies? | It harms them because Ford and GM import critical parts and entire vehicles from their Japanese subsidiaries/joint ventures, meaning they will pay the tariffs themselves. | The author of the post thinks that Trump's 15% tariffs on cars imported from Japan will actually harm US auto companies | Relevant | Accurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:**
What do people really think about Meta new move with forum? 

**What the system returned:**
I don't have enough information on that.

**Root cause (tied to a specific pipeline stage):**
This was caused by me having context that Meta is Facebook so when I wrote the question I already thought of Meta and Facebook as the same object. In reality, that was mentioned one in the title as Meta and later referred to as Facebook. The question was too board and the chunk distance was large.

**What you would change to fix it:**
Asking "What do people really think about Facebook's new forum and Reddit?" prompted an accurate response. Facebook and Reddit were both reference in the chunk. I would have to provide the context of what Meta is when referred to as Facebook in the chunks.

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**
The diagram helped the LLM to write the later code for embed and retrieve. One of the anticipated challenges ended up being an issue for a prompt that I had. That would help to refer back to and design around it.

**One way your implementation diverged from the spec, and why:**
When designing the retrieve.py and rag_app.py I had to redefine the chunk size a few times to see what is being pulled as the chunks because I couldn't get an answer from my model.

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:*
I gave the AI my chunking strategy in planning.md.
- *What it produced:*
It produced an embed_chunks.py script that was not sufficient for the model.
- *What I changed or overrode:*
Revised the chunk size to a larger chunk in the planning.md.

**Instance 2**

- *What I gave the AI:*
I gave the AI instructions to implement nomic for rag_app.py.
- *What it produced:*
It produced a model that required assymmetric sentence.
- *What I changed or overrode:*
I revised to the suggested model to mimick what prompting should be like according to instructions.