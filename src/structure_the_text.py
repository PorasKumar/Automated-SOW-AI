import logging
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from src.schema import SOWPydanticSchema
from src.prompts import STRUCTURED_OUTPUT_PROMPT

load_dotenv()

# Suppress warnings originating from google.genai
logging.getLogger("google_genai").setLevel(logging.ERROR)

llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")
llm_structured = llm.with_structured_output(SOWPydanticSchema)

def extract_sow_json_from_text(raw_context_text: str) -> SOWPydanticSchema:
    
    messages = [
        {"role": "system", "content": STRUCTURED_OUTPUT_PROMPT},
        {
            "role": "user",
            "content": (
                "Please extract the SOW schema from the following client context"
                f" documents:\n\n{raw_context_text}"
            ),
        },
    ]

    # Invokes model and automatically parses response into ExtractedSOWState Pydantic object
    extracted_data: SOWPydanticSchema = llm_structured.invoke(messages)
    return extracted_data