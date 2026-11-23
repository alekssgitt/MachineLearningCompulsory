# Research Scout

## Setup

You need Ollama to be running, with Llama 3.2 model pulled.

Run this:
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
ollama pull llama3.2
```

put those values in your .env (there is no api keys,since the model is locally hosted)
```bash
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=llama3.2
LLM_API_KEY=ollama
```
## Run
to run the agent just do:
```bash
python agent_runner.py "prompt"
```

## Evaluation

`python evaluate.py` has 10 prompts and runs them through the agent and checks each answer against the OpenAlex.

Result of the evaluation: **7/10 passed**. 

| # | Prompt | Result |
|---|---|---|
| 01 | LLM agents for software engineering, after 2022, at least 100 citations | pass |
| 02 | Retrieval-augmented generation, before 2021, more than 500 citations | fail, no paper on the first page passed |
| 03 | Recent paper on AI agents using tools | pass |
| 04 | Transformer architecture, published in 2017, at least 1000 citations | fail, no paper on the first page passed |
| 05 | SWE-bench agents, after 2023, at least 50 citations | pass |
| 06 | Word embeddings, before 2015, more than 1000 citations | fail, no paper on the first page passed |
| 07 | Denoising diffusion, about 1000 citations | pass |
| 08 | Underwater basket weaving with GPT-9, in 1990, at least 10000 citations | pass, correctly found nothing |
| 09 | A good paper on AI | pass |
| 10 | Zodiac diet of household robots, after 2024, at least 50000 citations | pass, correctly found nothing |

## Reflection

The year and citation filter worked as it was planned. Papers that missed a limit were dropped before the answer was written, and the two impossible requests correctly came back with no paper.

The unreliable part of this agent is the first page of search results. For example for older, highly cited papers, none of the first eight OpenAlex hits passed the year and citation limits so the agent just reported that no paper was found. A citation number is also ignored unless the sentence uses `at least`, `more than`, `fewer than`, `at most`, or `about`.

Each of the 10 prompts needed only one tool call. The instructions tell the model to search only once, and the run stops it from calling the tool more than twice.

In this evaluation the model did not invent a title, year, or citation count. When nothing matched in the search, it returned no paper instead of creating some .

Incorrect facts are then blocked in Python. The limits are from the sentence, OpenAlex gives the citation count, and `verify` copies the title, authors, year, count, source, and link from that tool record.

If i had to improve the agent, I would request a second page when the first page has no match maybe, accept more ways of writing a citation limit, and maybe try a larger hosted model.
