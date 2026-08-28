import math
from typing import List
from src.pricing_schema import MilestonePhase, CalculatedSOWFinancials
from src.schema import SOWPydanticSchema

#our agency's baseline config
HOURLY_RATE_USD = 175.0
HOURS_PER_DEV_WEEK = 30  #work throughput hours per week

#dictionary of complexity hours (how many hours based on complexity)
COMPLEXITY_HOURS_MAP = {
    "low": 30,  # e.g., Basic UI, simple CRUD, standard integrations
    "medium": 60,  # e.g., Custom dashboard, RBAC, third-party API sync
    "high": 120,  # e.g., ETL pipeline(data ingest, cleanup, store, manage), FHIR API, complex state engines
}

def calculate_sow_financials_and_roadmap(clientschema:SOWPydanticSchema)->CalculatedSOWFinancials:
    """Pure Python rules engine: Calculates dev hours, costs, risk buffers, 
    and timeline milestones(phases) deterministically without LLM math hallucinations."""
    try:
        #calculate hours of work
        base_hours = 0
        for item in clientschema.deliverables:
            hours = COMPLEXITY_HOURS_MAP.get(
                item.complexity.lower(), 60 #default to medium if complexity not specified in ClientSchema json
            )
            base_hours = base_hours + hours

        #calculating risk buffer in percentage based on number of identified risks
        #base risk buffer we keep at 10%, Adding 5% for each risk, ceiling for max risk 30%
        number_of_risks = len(clientschema.identified_risks)
        risk_buffer_percentage = min(0.10 + (number_of_risks * 0.05), 0.30)

        #risk buffered hours --> with every risk time increases --> therefore if risk 0.2 then we multiply by 1 + 0.2 - 1.2
        risk_buffered_hours = int(base_hours * (1 + risk_buffer_percentage))
        base_cost = base_hours * HOURLY_RATE_USD
        final_cost = risk_buffered_hours * HOURLY_RATE_USD

        #calculating project duration in weeks
        #weeks = (buffered_hours/ weekly throughput) + 2 weeks for Quality Assurance and UserAcceptanceTesting(UAT)
        estimated_weeks = math.ceil(risk_buffered_hours/HOURS_PER_DEV_WEEK) + 2 #QA/UAT

        #checking budget alignment
        client_budget = clientschema.constraints.budget_amount
        if client_budget is None:
            budget_status = "Unspecified Budget (client did not provide the budget)"
        elif final_cost <= client_budget:
            budget_status = f"Within Budget (${final_cost:,.2f} vs. ${client_budget:,.2f} budget)"
        else:
            overage = final_cost - client_budget
            budget_status = f"Exceeds Budget by ${overage:,.2f}\n (${final_cost:,.2f} vs. ${client_budget:,.2f} budget)"


        #building milestone roadmap & payment schedule
        deliverables = clientschema.deliverables
        midpoint = len(deliverables)//2 or 1  #// is floor division, e.g.->15/4 = 3  ||  or 1 because if only 1 deliverable then 1

        #splitting tasks into phases, using the midpoint of deliverables above
        phase1_items = [d.title for d in deliverables[:midpoint]]
        phase2_items = [d.title for d in deliverables[midpoint:]]

        phase1_weeks = math.ceil(estimated_weeks * 0.4) #40% time(weeks) for phase 1
        phase2_weeks = math.ceil(estimated_weeks * 0.4) #40% time(weeks) for phase 2
        phase3_weeks = max(1, estimated_weeks - phase1_weeks - phase2_weeks) #remaining time for QA/UAT, min 1 week

        #building the roadmap now, in phases
        #it'll be a list of MilestonePhase schemas
        roadmap = [
            MilestonePhase(
                phase_number=1,
                phase_name="Discovery and Core Architecture Setup",
                duration_weeks=phase1_weeks,
                deliverable_titles=phase1_items,
                cost_usd= round(final_cost * 0.4, 2) #40% of final cost  #",2" rounds to 2 decimal place 
            ),
            MilestonePhase(
                phase_number=2,
                phase_name="Primary Feature Development & Integration",
                duration_weeks=phase2_weeks,
                deliverable_titles=phase2_items,
                cost_usd= round(final_cost * 0.4, 2)
            ),
            MilestonePhase(
                phase_number=3,
                phase_name="Quality Assessment, User Acceptance Testing and Deployment",
                duration_weeks=phase3_weeks,
                deliverable_titles=["End-to-End Testing", "Production Deployment"],
                cost_usd=round(final_cost * 0.2, 2)
            )
        ]

        #returning the project pricing schema
        return CalculatedSOWFinancials(
            total_dev_hours=risk_buffered_hours,
            hourly_rate_usd=HOURLY_RATE_USD,
            base_cost_usd=base_cost,
            risk_buffer_percentage=round(risk_buffer_percentage * 100, 1), #",1" will give 1 number after decimal 
            final_total_cost_usd=final_cost,
            estimated_duration_weeks=estimated_weeks,
            budget_alignment_status=budget_status,
            milestone_roadmap=roadmap,
        )

    except Exception as e:
        print(f"Error in rules_engine.py: \n{e}")
        raise RuntimeError(f"Error in rules_engine.py: \n{e}")