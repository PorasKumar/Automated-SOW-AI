import streamlit as st
from src.graph import graph
import uuid
from src.graph import SOWState
import time

#Page Configuration
st.set_page_config(
    page_title="Automated SOW Engine", page_icon="📄", layout="centered"
)


################
#Session State #
################
if "execution_stage" not in st.session_state:
    st.session_state.execution_stage = "upload" #dashboard logic
if "sessionid" not in st.session_state:
    st.session_state.sessionid = str(f"session_id_{uuid.uuid4().hex[:8]}")


#Config Initialization
config = {"configurable": {"thread_id": st.session_state.sessionid}}


#####################
#Inline CSS Styling #
#####################

#Helper to load external CSS
def load_css(file_path: str):
    with open(file_path, "r") as f:
        #open the css file and add it to st.markdown()
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Load styles from external file
style_css = load_css("src/style.css")


##########
#Sidebar #
##########
with st.sidebar:
    st.markdown("### 👤 User Session")
    st.markdown(
        f"Thread ID: <span class='session-badge'>{config['configurable']['thread_id']}</span>",
        unsafe_allow_html=True,
    )
    st.divider()

    #button to clear session data, with some status and spinner
    if st.button("🧹 Clear Session", use_container_width=True):
        with st.status("⚡ Purging Session Data...", expanded=True) as status:
            st.write("🗑️ Flushed active file payloads & RAM...")
            time.sleep(0.5)

            st.write("🔄 Resetting LangGraph state & thread history...")
            time.sleep(0.5)

            with st.spinner("🧹 Cleaning temporary UI state..."):
                time.sleep(0.5)

            status.update(
                label="✨ Session Cleared Successfully!",
                state="complete",
                expanded=False,
            )

            time.sleep(0.3)
            st.session_state.clear()
            st.rerun()

################################
# STAGE 1: INGESTION DASHBOARD #
################################
if st.session_state.execution_stage == "upload":
    st.markdown('<div class="main-title">Automated SOW Engine</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-subtitle">Upload client briefs to calculate financials and generate SOW document</div>', unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "Upload project briefs",
        type=["txt", "pdf", "docx", "eml"],
        accept_multiple_files=True,
    )

    st.write("")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        process_clicked = st.button("🚀 Process Files & Extract Scope", use_container_width=True)

    if process_clicked:
        if not uploaded_files:
            st.warning("Please upload at least one file before processing.")
        else:
            file_payloads = []
            for file in uploaded_files:
                file.seek(0)
                content = file.read()
                file_payloads.append((content, file.name))

            st.session_state.file_payloads = file_payloads
            st.session_state.execution_stage = "processing"
            st.rerun()


#######################################
# STAGE 2: INITIAL GRAPH PIPELINE RUN #
#######################################
elif st.session_state.execution_stage == "processing":

    st.markdown('<div class="main-title">⚙️ SOW Execution Pipeline</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-subtitle">Review calculated metrics and approve or reject scope...</div>', unsafe_allow_html=True)

    with st.status("🚀 Running LangGraph Pipeline...", expanded=True) as status:
        st.write("📥 Processing uploaded file payloads...")
        initial_state = {"raw_files": st.session_state.file_payloads}

        for _ in graph.stream(initial_state, config, stream_mode="values"):
            pass

        status.update(label="✨ Extraction & Financial Calculation complete!", state="complete", expanded=False)
    
    st.session_state.execution_stage = "review"
    st.rerun()


#########################################
# STAGE 3: HITL REVIEW & DECISION GATE  #
#########################################
elif st.session_state.execution_stage == "review":
    st.markdown('<div class="main-title">⚙️ SOW Execution Pipeline</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-subtitle">Review calculated metrics and approve or reject scope...</div>', unsafe_allow_html=True)

    snapshot = graph.get_state(config)

    if snapshot.values and "extracted_details" in snapshot.values and snapshot.values["extracted_details"]:
        state_data: SOWState = snapshot.values
        extracted_details = state_data.get("extracted_details")
        financials = state_data.get("calculated_financials")

        st.markdown("---")
        st.subheader("🛡️ Human-in-the-Loop Verification Gate")

        col1, col2 = st.columns(2)
        col1.metric("Client Name", extracted_details.client_info.company_name)
        col2.metric("Calculated Total Cost", f"${financials.final_total_cost_usd:,.2f}")
        col3, col4 = st.columns(2)
        col3.metric("Target Client Budget", f"${extracted_details.constraints.budget_amount or 0:,.2f}")
        col4.metric("Estimated Timeline", f"{financials.estimated_duration_weeks} Weeks")

        if "Exceeds Budget" in financials.budget_alignment_status:
            st.error(f"⚠️ **Budget Alert:** {financials.budget_alignment_status}")
        elif "Unspecified Budget" in financials.budget_alignment_status:
            st.warning(f"Unspecified Budget! Client did not provide any budget.")
        else:
            st.success(f"✅ **Budget Status:** {financials.budget_alignment_status}")

        st.write("**Extracted Executive Summary:**", extracted_details.executive_summary)

        with st.expander("🔍 View Extracted Deliverables & Complexity Tiers", expanded=True):
            for d in extracted_details.deliverables:
                st.markdown(f"- **{d.title}** (`{d.complexity} Complexity`): {d.description}")

        with st.expander("⚠️ View Risk Factors & Applied Buffers"):
            st.write(f"**Applied Risk Buffer Markup:** {financials.risk_buffer_percentage}%")
            for r in extracted_details.identified_risks:
                st.markdown(f"- **Risk:** {r.risk_description} | **Mitigation:** {r.mitigation_strategy}")

        st.markdown("### Decision Gate")
        feedback = st.text_area(
            "Optional Notes / Instructions for downstream LLM generation:",
            placeholder="e.g. Rejecting budget overage, suggest MVP scope reduction.",
            height=120,
        )

        col_approve, col_reject = st.columns(2)

        if col_approve.button("✅ Approve Budget & Generate SOW"):
            with st.spinner("Resuming Graph -> Generating Full SOW Document"):
                graph.update_state(
                    config,
                    {
                        "human_approved": True,
                        "human_feedback_notes": (feedback or "Approved budget and calculated scope."),
                    },
                )
                for _ in graph.stream(None, config, stream_mode="values"):
                    pass

            st.session_state.execution_stage = "completed"
            st.rerun()

        if col_reject.button("❌ Reject Budget & Draft Negotiation Email"):
            with st.spinner("Resuming Graph -> Drafting Budget Negotiation Email..."):
                graph.update_state(
                    config,
                    {
                        "human_approved": False,
                        "human_feedback_notes": (feedback or "Rejected overage. Requesting negotiation email."),
                    }
                )
                for _ in graph.stream(None, config, stream_mode="values"):
                    pass

            st.session_state.execution_stage = "completed"
            st.rerun()


##################################
# STAGE 4: DISPLAY FINAL OUTPUT  #
##################################
elif st.session_state.execution_stage == "completed":
    snapshot = graph.get_state(config)

    if snapshot.values and "pipeline_status" in snapshot.values:
        final_data: SOWState = snapshot.values if snapshot else {}
        status = final_data.get("pipeline_status", "")
        extracted_details = final_data.get("extracted_details")

        client_name = "Client"
        if extracted_details and hasattr(extracted_details, "client_info") and extracted_details.client_info:
            client_name = getattr(extracted_details.client_info, "company_name", "Client")

        if status == "SOW_GENERATED" or final_data.get("human_approved") is True:
            st.markdown("---")
            st.subheader("📄 Final Statement of Work (SOW)")
            sow_text = final_data.get("final_sow_report")
            st.markdown(sow_text)

            st.download_button(
                label="Download SOW (.md)",
                data=sow_text,
                file_name=f"SOW_{client_name}.md",
                mime="text/markdown",
            )

        elif status == "NEGOTIATION_EMAIL_DRAFTED" or final_data.get("human_approved") is False:
            st.markdown("---")
            st.subheader("✉️ Generated Budget Negotiation Email")
            email_text = final_data.get("negotiation_email")
            st.markdown(email_text)

        st.write("")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔄 Start New Session", use_container_width=True):
                if "file_payloads" in st.session_state:
                    del st.session_state["file_payloads"]
                st.session_state.clear()
                st.rerun()