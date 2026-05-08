from typing import List
from pydantic import BaseModel

class PipelineRunRequest(BaseModel):
    city: str
    sources: List[str]  # ["osm", "google"]

class PipelineRunResponse(BaseModel):
    run_id: str
    status: str