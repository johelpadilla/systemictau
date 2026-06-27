from pydantic import BaseModel, Field
from typing import Optional

class SystemNode(BaseModel):
    tenant_id: str = Field(..., description="Unique identifier for the tenant system")
    name: Optional[str] = None

class AscentNode(BaseModel):
    t_star: int = Field(..., description="The time index where the critical mass was breached")
    tau: float = Field(..., description="The tau correlation value at the transition")
    description: str = Field(..., description="Details about the ontological transition")
    timestamp: Optional[int] = Field(None, description="Unix timestamp of the transition")
