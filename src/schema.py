from typing import Optional,List
from pydantic import Field, BaseModel

class ClientInformation(BaseModel):
    company_name:Optional[str] = Field(
        default="Unknown /TBD",
        description="extracted company name of the client"
    )

    contact_person:Optional[str] = Field(
        default=None, description="Name of primary contact person"
    )

    contact_email:Optional[str] = Field(
        default=None, description="email of the client/contact person"
    )

class DeliverableItem(BaseModel):
    title:str = Field(
        description="short title of the deliverable (e.g., 'Shopify ETL Data Sync')"
    )

    description: str = Field(
        description="Detailed explaination of what will be built, including technical stack."
    )

    complexity:str = Field(
        description="estimated technical complexity: 'High','Medium', or 'Low'"
    )

class RiskItem(BaseModel):
    risk_description:str = Field(
        description="Identified scope risk, tight deadline, API rate limit, or ambiguous requirement"
    )

    mitigation_strategy: str = Field(
      description="Proposed technical or operational strategy to mitigate the risk."
    )

class ProjectConstraints(BaseModel):
    taget_timeline_weeks: Optional[int] = Field(
        description="Target timeline for the project. Set to null if not specified"
    )

    budget_amount: Optional[float] = Field(
        description="Extracted budget cap or target figure. Set to null if not mentioned."
    )

    tech_stack_requirements:List[str] = Field(
        default_factory=list, #if no value then a defailt empty [] will be created
        description="List of requested frameworks, APIs, or infrastructure (e.g.,"
          "['AWS', 'React', 'Shopify REST API'])"
    )

################
#MASTER SCHEMA #
################
class SOWPydanticSchema(BaseModel):
    """Complete structured output representation extracted from raw inputs"""

    #client information
    client_info: ClientInformation

    #overall summary of the project
    executive_summary:str = Field(
        description=("High-level 2-3 sentence summary of the project goals and business pain points.")
    )

    #list of different deliverables(title, description, complexities)
    deliverables:List[DeliverableItem] = Field(
        default_factory=list,
        description=("List of core functional and technical deliverables.")
    )

    #contraints of the project
    constraints: ProjectConstraints

    #risks of the project
    identified_risks:List[RiskItem] = Field(
        default_factory=list,
      description=(
          "List of potential risks, tight deadlines, or technical hurdles with mitigations")
    )

    #some unlisted vague requirements by the client
    ambiguous_points: List[str] = Field(
      default_factory=list,
      description=(
          "List of unstated or vague requirements that need clarification before finalizing scope")
    )