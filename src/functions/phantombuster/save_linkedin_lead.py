import os
from typing import Any, Dict
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from restack_ai.function import NonRetryableError, function, log
import httpx

load_dotenv()

class SaveLeadInput(BaseModel):
    """Input parameters for saving a LinkedIn lead."""

    model_config = {
        "strict": True,
        "extra": "forbid",
        "validate_assignment": True,
        "str_strip_whitespace": True,
    }

    linkedin_profile_url: str = Field(
        ...,
        title="LinkedIn Profile URL",
        description="The URL of the LinkedIn profile to save.",
        example="https://www.linkedin.com/in/le-awn/",
    )

def raise_exception(message: str) -> None:
    log.error("save_linkedin_lead_phantombuster function failed", error=message)
    raise NonRetryableError(message)

@function.defn()
async def save_linkedin_lead_phantombuster(function_input: SaveLeadInput) -> dict[str, Any]:
    """Saves a scraped LinkedIn profile as a lead in Phantombuster's storage."""
    try:
        api_key = os.environ.get("PHANTOMBUSTER_API_KEY")
        if not api_key:
            raise_exception("PHANTOMBUSTER_API_KEY is not set")

        headers = {
            "X-Phantombuster-Key-1": api_key,
            "Content-Type": "application/json",
        }

        save_url = "https://api.phantombuster.com/api/v2/org-storage/leads/save"
        
        payload = {
            "linkedinProfileUrl": function_input.linkedin_profile_url
        }

        async with httpx.AsyncClient() as client:
            log.info(f"Saving lead {function_input.linkedin_profile_url} to Phantombuster.")
            response = await client.post(save_url, headers=headers, json=payload)
            response.raise_for_status()
            
            response_json = response.json()
            log.info(f"Phantombuster save lead response: {response_json}")
            return response_json

    except Exception as e:
        error_message = f"save_linkedin_lead_phantombuster failed: {e}"
        raise NonRetryableError(error_message) from e
