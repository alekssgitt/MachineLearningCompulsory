
import argparse
import asyncio
import os
from datetime import date

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

from pydantic_ai import Agent, PromptedOutput
from pydantic_ai.usage import UsageLimits

from agent_tools import SearchSession, register_tools
from config import Settings
from models import PaperAnswer
from provider import open_model

recent_year = date.today().year - 2

INSTRUCTIONS = f"""You are a research scout for a software company. Work in ReAct steps.

Thought: Name a short topic for the request. Python reads the year and citation limits from the user's sentence.
"recent" means since {recent_year}.

Action: Call search_papers once. The only argument is topic, a few words.

Observation: Read matches and rejected. Titles, authors, years, citation counts, and links come only from this result.

Thought: If matches is not empty, the first match is the paper. If it is empty, no paper qualifies.

Answer: Copy the first match exactly and write the explanation from its abstract. Follow any length the user asked for.
If matches is empty, set found to false and explain the rejected reasons or the error.
Never invent a citation count."""


def make_agent(model) -> Agent:
    agent = Agent(
        model,
        deps_type=SearchSession,
        output_type=PromptedOutput(PaperAnswer),
        instructions=INSTRUCTIONS,
        retries=1,
        model_settings={"temperature": 0.2, "max_tokens": 700},
    )
    register_tools(agent)
    return agent


def verify(answer: PaperAnswer, session: SearchSession) -> PaperAnswer:
    if not session.matches:
        return PaperAnswer(found=False, explanation=answer.explanation or "No matching paper was found.")
    match = next(
        (paper for paper in session.matches
         if paper["url"] == answer.url or paper["title"].casefold() == (answer.title or "").casefold()),
        session.matches[0],
    )
    explanation = answer.explanation.strip()
    if not answer.found or len(explanation) < 40:
        explanation = match.get("abstract") or "This paper passed the year and citation checks."
    return PaperAnswer(
        found=True,
        title=match["title"],
        authors=list(match["authors"]),
        publication_year=match["year"],
        citation_count=match["citation_count"],
        citation_source=match["citation_source"],
        url=match["url"],
        explanation=explanation,
    )


async def run_request(request: str, settings: Settings | None = None) -> tuple[PaperAnswer, SearchSession]:
    settings = settings or Settings.load()
    session = SearchSession()
    async with open_model(settings) as model:
        result = await make_agent(model).run(
            request,
            deps=session,
            usage_limits=UsageLimits(request_limit=4, tool_calls_limit=2),
            timeout=settings.timeout,
        )
    return verify(result.output, session), session


def main():
    parser = argparse.ArgumentParser(description="Find one research paper for a request.")
    parser.add_argument("request", nargs="+", help="What paper to find")
    args = parser.parse_args()
    try:
        answer, session = asyncio.run(run_request(" ".join(args.request)))
    except ValueError as error:
        parser.exit(2, str(error) + "\n")
    print(answer.model_dump_json(indent=2))
    print(f"Tool calls: {session.calls}")


if __name__ == "__main__":
    main()
