from typing import List
from pydantic import BaseModel, Field
from openai import OpenAI
import json

class SearchQueryList(BaseModel):
    query: List[str] = Field(
        description="A list of search queries to be used for web research."
    )
    rationale: str = Field(
        description="A brief explanation of why these queries are relevant to the research topic."
    )


class Reflection(BaseModel):
    is_sufficient: bool = Field(
        description="Whether the provided summaries are sufficient to answer the user's question."
    )
    knowledge_gap: str = Field(
        description="A description of what information is missing or needs clarification."
    )
    follow_up_queries: List[str] = Field(
        description="A list of follow-up queries to address the knowledge gap."
    )


def vllm_structured_output(content: str, structure):

    client = OpenAI(base_url="http://localhost:8000/v1", api_key="-")
    model = client.models.list().data[0].id

    json_schema = structure.model_json_schema()

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": content,
            }
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": structure.__name__.lower(),
                "schema": json_schema
            },
        },
    )
    # print(structure.__name__.lower())

    usage = completion.usage
    usage_output = usage.model_dump()

    json_output = completion.choices[0].message.content
    parsed = structure.model_validate_json(json_output)

    result = {
        "parsed": parsed,
        "usage": usage_output
    }
    
    return result