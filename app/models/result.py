from pydantic import BaseModel, Field


class AgentResult(BaseModel):
    agent: str = Field(min_length=1)
    success: bool
    output: str
    artifacts: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class ReviewResult(BaseModel):
    approved: bool
    summary: str = Field(min_length=1)
    blocking_issues: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
