from typing import List,Optional
from pydantic import Field, BaseModel

#since project will be made in phases, so different milestones will be there
class MilestonePhase(BaseModel):
    phase_number: int
    phase_name: str
    duration_weeks: int
    deliverable_titles: List[str]
    cost_usd: float

class CalculatedSOWFinancials(BaseModel):
    total_dev_hours: int
    hourly_rate_usd: float = 175.0
    base_cost_usd: float
    risk_buffer_percentage: float
    final_total_cost_usd: float
    estimated_duration_weeks: int
    budget_alignment_status: str  # "Within Budget", "Exceeds Budget", "Underspecified Budget"
    milestone_roadmap: List[MilestonePhase]