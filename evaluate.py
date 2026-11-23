import asyncio

from agent_runner import run_request
from paper_search import rejection_reason

cases = [
    {
        "name": "broad, after, at least 100",
        "prompt": "Find a research paper about LLM agents for software engineering that was published after 2022 and has at least 100 citations. Explain why the paper is relevant and provide the source of the citation count.",
        "expect_found": True,
        "year_relation": "after",
        "year": 2022,
        "citation_relation": "at_least",
        "citation_count": 100,
    },
    {
        "name": "narrow, before, more than 500",
        "prompt": "Find a paper about retrieval-augmented generation published before 2021 with more than 500 citations. Summarize its contribution in 5-7 sentences.",
        "expect_found": True,
        "year_relation": "before",
        "year": 2021,
        "citation_relation": "more_than",
        "citation_count": 500,
    },
    {
        "name": "recent, no citation limit",
        "prompt": "Find a recent paper about AI agents using tools and explain whether it would be useful for someone building autonomous software agents.",
        "expect_found": True,
        "year_relation": "since",
        "year": 2024,
        "citation_relation": "any",
        "citation_count": None,
    },
    {
        "name": "exact year, at least 1000",
        "prompt": "Find a paper about the transformer neural network architecture published in 2017 with at least 1000 citations.",
        "expect_found": True,
        "year_relation": "in",
        "year": 2017,
        "citation_relation": "at_least",
        "citation_count": 1000,
    },
    {
        "name": "narrow, after, at least 50",
        "prompt": "Find a paper about SWE-bench or software engineering agents that fix GitHub issues, published after 2023, with at least 50 citations.",
        "expect_found": True,
        "year_relation": "after",
        "year": 2023,
        "citation_relation": "at_least",
        "citation_count": 50,
    },
    {
        "name": "broad, before, more than 1000",
        "prompt": "Find a paper about word embeddings for natural language processing published before 2015 with more than 1000 citations.",
        "expect_found": True,
        "year_relation": "before",
        "year": 2015,
        "citation_relation": "more_than",
        "citation_count": 1000,
    },
    {
        "name": "about 1000 citations",
        "prompt": "Find a paper about denoising diffusion probabilistic models with about 1000 citations.",
        "expect_found": None,
        "year_relation": "any",
        "year": None,
        "citation_relation": "about",
        "citation_count": 1000,
    },
    {
        "name": "no paper",
        "prompt": "Find a paper about underwater basket weaving with GPT-9 published in 1990 with at least 10000 citations.",
        "expect_found": False,
        "year_relation": "in",
        "year": 1990,
        "citation_relation": "at_least",
        "citation_count": 10000,
    },
    {
        "name": "ambiguous",
        "prompt": "Find me a good paper on AI.",
        "expect_found": None,
        "year_relation": "any",
        "year": None,
        "citation_relation": "any",
        "citation_count": None,
    },
    {
        "name": "no paper, after, at least 50000",
        "prompt": "Find a paper about the zodiac diet of household robots published after 2024 with at least 50000 citations.",
        "expect_found": False,
        "year_relation": "after",
        "year": 2024,
        "citation_relation": "at_least",
        "citation_count": 50000,
    },
]


def check(case, answer, session):
    problems = []
    if session.calls < 1:
        problems.append("tool was not called")
    if case["expect_found"] is not None and answer.found != case["expect_found"]:
        problems.append(f"found={answer.found}, expected {case['expect_found']}")
    if not answer.found:
        return problems
    match = next((paper for paper in session.matches if paper["url"] == answer.url), None)
    if match is None:
        problems.append("paper was not in the tool results")
        return problems
    reason = rejection_reason(
        match, case["year_relation"], case["year"], case["citation_relation"], case["citation_count"]
    )
    if reason:
        problems.append(reason)
    if answer.citation_count != match["citation_count"] or answer.publication_year != match["year"]:
        problems.append("facts differ from the tool record")
    if not answer.url or not answer.citation_source:
        problems.append("missing link or citation source")
    if len(answer.explanation.strip()) < 40:
        problems.append("explanation too short")
    return problems


async def main():
    passed = 0
    for number, case in enumerate(cases, start=1):
        try:
            answer, session = await run_request(case["prompt"])
            problems = check(case, answer, session)
            title = answer.title or "no paper"
        except Exception as error:
            problems = [str(error)]
            title = "error"
        if not problems:
            passed += 1
        print(f"{number:02} {'pass' if not problems else 'fail'}  {case['name']}  {title}")
        for problem in problems:
            print(f"    {problem}")
    print(f"\n{passed}/{len(cases)} passed")


if __name__ == "__main__":
    asyncio.run(main())
