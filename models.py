from pydantic import BaseModel, ConfigDict, Field


class PaperAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    found: bool
    title: str = ""
    authors: list[str] = Field(default_factory=list)
    publication_year: int | None = None
    citation_count: int | None = None
    citation_source: str = ""
    url: str = ""
    explanation: str
