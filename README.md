# 📄 Automated SOW & Negotiation Engine

An automated enterprise workspace tool built with **LangGraph**, **Gemini API**, **Pydantic**, and **Streamlit**. 

The engine ingests multi-format project inputs (client emails, raw briefs, proposal PDFs, text files), extracts structured scope parameters into validated data models, 
executes financial calculations against internal business rules, and routes output through a 
**Human-in-the-Loop (HITL)** manager approval gate before generating formal Statements of Work (SOW) or client negotiation drafts.


## 🏗 Workflow & Pipeline Architecture

+--------------------------------------------------------------+
|              Multi-Format Inputs                             |
|   (.eml Emails | .pdf Documents | .docx Files | .txt Briefs) |
+------------------------------+-------------------------------+
|
v
+--------------------------------------------------------------+
|             Structured Extraction Engine                     |
|        (Pydantic Schema Enforcement + Gemini API)            |
+------------------------------+-------------------------------+
|
v
+--------------------------------------------------------------+
|             Deterministic Rules & Financials                 |
|     (Scope Verification, Margin Calc, Budget Flagging)       |
+------------------------------+-------------------------------+
|
v
+--------------------------------------------------------------+
|               Human-in-the-Loop (HITL) Gate                  |
|      (Manager Review, Manual Overrides, Approval State)      |
+------------------------------+-------------------------------+
|
+---------------+---------------+
|                               |
v                               v
+------------------------------+ +-----------------------------+
|      Finalized SOW Doc       | |  Client Negotiation Draft   |
|     (Formatted Output)       | |   (Margin/Budget Adjust)    |
+------------------------------+ +-----------------------------+




## ✨ Key Features

* **Multi-Format Document Parsing:** Native ingestion and text extraction for `.eml`, `.pdf`, `.docx`, and raw `.txt` client briefs.
* **Strict Pydantic Schema Enforcement:** Guarantees LLM outputs adhere to rigid, type-safe Python data structures, eliminating missing fields or unparsed financial values.
* **Deterministic Financials & Rule Engine:** Computes project milestones, rate cards, and total costs deterministically (rather than letting LLMs perform raw arithmetic) to avoid budget hallucinations.
* **Human-in-the-Loop (HITL) Approval Gate:** Provides an interactive manager interface to review extracted terms, provide a feedback and either accept the project or reject it (will trigger negotiation email generation).
* **Dual-Output Generator:** Produces either a finalized enterprise Statement of Work (SOW) or a professionally framed negotiation email draft if client constraints conflict with internal minimum thresholds.
* **Sleek UI/UX:** Styled Streamlit glassmorphic interface.

---

## 🛠 Tech Stack

* **LLM Engine:** Google Gemini API (`gemini-3.1-flash`)
* **Data Structuring & Validation:** Pydantic v2
* **Orchestration:** LangGraph / Python Functions
* **Document Parsing:** `pypdf`, `python-docx`, `extract-msg` / native email modules
* **Frontend UI:** Streamlit (Custom Inline CSS)

Checkout the App: https://automated-sow-engine.streamlit.app/

You can use sample files to test the app in this same repository, in sample emails folder.
