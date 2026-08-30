from langchain_core.prompts import ChatPromptTemplate

#fetch details from documents prompt
STRUCTURED_OUTPUT_PROMPT = """You are an expert Solutions Architect and Agency Proposal Director.
Your task is to analyze raw client discovery documents (emails, RFPs, transcripts, briefs) and extract a precise, structured Scope of Work (SOW) specification.

Guidelines:
1. Extract facts accurately without hallucinating unmentioned numbers or constraints.
2. If budget or timeline is ambiguous or unspecified, leave them as null/None and flag the ambiguity in 'ambiguous_points'.
3. Identify technical risks (e.g., tight deadlines, third-party API rate limits, compliance mandates) and suggest realistic mitigation strategies.
4. Categorize deliverable complexity accurately based on technical scope.
"""

#final sow report prompt
SOW_GENERATION_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        (
            "You are an expert technical solutions architect. Your task is to draft a comprehensive, "
            "formal Statement of Work (SOW) in clear Markdown based strictly on the provided JSON context. "
            "Use clear headers, tables for financial breakdowns, and professional business tone."
        ),
    ),
    (
        "human",
        """
Write a formal Statement of Work (SOW) in clear Markdown based on this scope:

Client: {company_name}
Summary: {executive_summary}
Total Dev Hours: {total_dev_hours} hrs
Total Cost: ${final_total_cost:,.2f}
Timeline: {estimated_duration_weeks} Weeks

Deliverables:
{deliverables_json}

Milestones:
{milestones_json}
""",
    ),
])


#negotiation email
NEGOTIATION_EMAIL_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        (
            "You are a professional sales engineering director. Your goal is to write "
            "courteous, persuasive sales emails when a client's budget target does not "
            "match estimated development costs. Maintain a collaborative, solutions-oriented tone."
            "Read the feedback below and keep the theme of negotiation around it, since it is the feedback of our comapny's manager."
            "If the data is too vague according to the feedback, then ask to clear the misunderstanding by sending the project documents again."
        ),
    ),
    (
        "human",
        """
Write a courteous sales negotiation email addressing a project budget mismatch based on the following context:

Client Contact: {contact_person}
Client Company: {company_name}
Client Target Budget: ${target_budget:,.2f}
Calculated Total Cost: ${calculated_cost:,.2f}
Human Review Notes / Feedback / Our Company Manager's feedback on client's budget etc.,: {human_feedback}

Explain why the full scope exceeds their budget (due to technical complexity and risk buffers).
Propose two concrete solutions:
1. Scope reduction (MVP approach) to hit target budget.
2. Phased implementation across multiple budget cycles.
""",
    ),
])