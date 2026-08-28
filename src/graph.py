from langgraph.graph import START,END,StateGraph
from langgraph.checkpoint.memory import MemorySaver
from typing import List, Optional, Tuple
from pydantic import BaseModel, Field
from src.schema import SOWPydanticSchema
from src.structure_the_text import extract_sow_json_from_text
from src.pricing_schema import CalculatedSOWFinancials
from src.rules_engine import calculate_sow_financials_and_roadmap
from src.ingestion import uploaded_file_aggregator
from src.prompts import SOW_GENERATION_PROMPT, NEGOTIATION_EMAIL_PROMPT
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
import logging
import json
from dotenv import load_dotenv
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer #register schema with langgraph

load_dotenv()

class SOWState(BaseModel):
    #ingested raw files (email, docx, txt etc)
    raw_files: List[Tuple[bytes, str]] = Field(default_factory=list)
    #extracted texts in aggregated form to be stored in below state variable
    raw_text: Optional[str]=None

    #structured json, the extracted details, and the calculated financials
    extracted_details: Optional[SOWPydanticSchema] = None
    calculated_financials: Optional[CalculatedSOWFinancials] = None

    #HITL variables
    human_approved: Optional[bool] = None
    human_feedback_notes: Optional[str] = None

    #OUTPUT
    final_sow_report: str = ""
    negotiation_email: str = ""
    pipeline_status: str = "INITIALIZED"


#init gemini
# Suppress warnings originating from google.genai
logging.getLogger("google_genai").setLevel(logging.ERROR)
llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")

###################
# Graph Function #
###################
def make_sow_graph():

    def extract_details_agent(state:SOWState):
        """This node/agent takes the raw files (eg., Emails, txt, docx etc) and extracts details and structures
        them in a json format"""

        #load the user input files in a variable (List[Tuple[bytes,str]])
        files = state.raw_files

        if not files:
            #Fallback if text was passed directly instead of raw_files
            raw_text = state.raw_text
        else:
            #will return aggregated texts of files
            raw_text = uploaded_file_aggregator(files)

        extracted_details:SOWPydanticSchema = extract_sow_json_from_text(raw_text)

        return {"raw_text":raw_text,
                "extracted_details":extracted_details,
                "pipeline_status":"EXTRACTED_DETAILS"}


    def calculate_rules_agent(state:SOWState):
        """This agent extracts details from the files and structures them as json format"""
        calculated_financials:CalculatedSOWFinancials = calculate_sow_financials_and_roadmap(state.extracted_details)
        return {"calculated_financials":calculated_financials,
                "pipeline_status":"AWAITING_HUMAN_APPROVAL"}


    def route_after_human_review(state: SOWState) -> str:
        """Conditional Edge: Routes flow based on HITL approval status."""
        if state.human_approved:
            return "generate_sow_agent"
        else:
            return "generate_negotiation_email_agent"


    sow_generation_chain = SOW_GENERATION_PROMPT | llm | StrOutputParser()

    def generate_sow_agent(state:SOWState):
        """This agent will make the final SOW report based on the client details and calculated financials"""

        extracted_details = state.extracted_details
        calculated_financials = state.calculated_financials

        #convert the pydantic schemas(CalculatedSOWFinancials, SOWPydanticSchema) back to human readable dicts, so that llm can read them 
        #json.dumps() -> converts entire python dictionaries into human readable format
        #then we are converting each deliverable into human readable dict by .model_dump() and indented by 2 spaces 
        deliverables_json = json.dumps(
            [d.model_dump() for d in extracted_details.deliverables], indent=2
        )
        milestones_json = json.dumps(
            [m.model_dump() for m in calculated_financials.milestone_roadmap], indent=2
        )

        # Invoke the chain using dict mapping
        response = sow_generation_chain.invoke({
        "company_name": extracted_details.client_info.company_name,
        "executive_summary": extracted_details.executive_summary,
        "total_dev_hours": calculated_financials.total_dev_hours,
        "final_total_cost": calculated_financials.final_total_cost_usd,
        "estimated_duration_weeks": calculated_financials.estimated_duration_weeks,
        "deliverables_json": deliverables_json,
        "milestones_json": milestones_json,
        })

        return{
            "final_sow_report":response,
            "pipeline_status":"SOW_GENERATED",
        }


    negotiation_email_chain = NEGOTIATION_EMAIL_PROMPT | llm | StrOutputParser()

    def generate_negotiation_email_agent(state:SOWState):
        """It will generate a negotiation email, if the user does not approve after seeing the budget etc."""

        ext = state.extracted_details
        fin = state.calculated_financials

        #fetch the details to feed the llm with context
        contact_person = ext.client_info.contact_person or "Client"
        company_name = ext.client_info.company_name
        target_budget = ext.constraints.budget_amount or 0.0
        human_feedback = state.human_feedback_notes or "None provided"

        # Invoke the prompt | llm chain with the dictionary of parameters
        response = negotiation_email_chain.invoke({
        "contact_person": contact_person,
        "company_name": company_name,
        "target_budget": target_budget,
        "calculated_cost": fin.final_total_cost_usd,
        "human_feedback": human_feedback,
        })

        return {
        "negotiation_email": response,
        "pipeline_status": "NEGOTIATION_EMAIL_DRAFTED",
        }
        
    #################
    # graph builder #
    #################
    builder = StateGraph(SOWState)

    #add node
    builder.add_node("ingestion_agent",extract_details_agent)
    builder.add_node("rules_agent",calculate_rules_agent)
    builder.add_node("generate_sow_agent",generate_sow_agent)
    builder.add_node("generate_negotiation_email_agent", generate_negotiation_email_agent)

    #add edges
    builder.add_edge(START,"ingestion_agent")
    builder.add_edge("ingestion_agent","rules_agent")

    #add HITL
    builder.add_conditional_edges(
        "rules_agent",
        route_after_human_review,
        {
            "generate_sow_agent":"generate_sow_agent",
            "generate_negotiation_email_agent":"generate_negotiation_email_agent"
        }
    )
    #both shall go to end, (only one will execute based on HITL response)
    builder.add_edge("generate_sow_agent", END)
    builder.add_edge("generate_negotiation_email_agent", END)

    #serializer to register our defined schemas with langgraph
    serializer = JsonPlusSerializer(
    allowed_msgpack_modules=[
        ("src.schema", "SOWPydanticSchema"),#Use tuples instead of lists
        ("src.pricing_schema", "CalculatedSOWFinancials"),#Use tuples instead of lists
    ]
    )

    # Memory Checkpointer for state persistence and pause/resume (HITL it is bro)
    memory = MemorySaver(serde=serializer)
    return builder.compile(
        checkpointer=memory,
        #below pauses execution right after rules calculation
        interrupt_after=[
            "rules_agent"
            ]
    )

graph = make_sow_graph()