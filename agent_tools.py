from dataclasses import dataclass, field
from pydantic_ai import Agent, RunContext

from paper_search import fetch_papers, read_constraints, select_papers


@dataclass
class SearchSession:
    calls: int = 0
    matches: list[dict] = field(default_factory=list)


def register_tools(agent: Agent):
    @agent.tool(sequential=True, retries=0)
    def search_papers(ctx: RunContext[SearchSession], topic: str) -> dict:
        ctx.deps.calls += 1
        request = ctx.prompt if isinstance(ctx.prompt, str) else topic
        year_relation, year, citation_relation, citation_count = read_constraints(request)
        try:
            found = fetch_papers(topic)
        except Exception as error:
            return {"matches": [], "rejected": [], "error": f"Search failed: {error}"}
        matches, rejected = select_papers(
            found, year_relation, year, citation_relation, citation_count
        )
        ctx.deps.matches.extend(matches)
        return {"matches": matches, "rejected": rejected[:5]}
