from pydantic import BaseModel, Field, confloat
class FAQAnswer(BaseModel):
    answer: str = Field(...)
    citations: list[str] = Field(default_factory=list)
    confidence: confloat(ge=0, le=1) = 0.0
