import os
import json
from typing import Any
from dotenv import load_dotenv
import asyncio
from pydantic import BaseModel, Field
from restack_ai.function import NonRetryableError, function, log
import httpx

load_dotenv()


class GetProfileReactionsInput(BaseModel):
    """Input parameters for getting a LinkedIn profile's reactions."""

    model_config = {
        "strict": True,
        "extra": "forbid",
        "validate_assignment": True,
        "str_strip_whitespace": True,
    }

    profile_url: str = Field(
        ...,
        title="LinkedIn Profile URL",
        description="The URL of the LinkedIn profile.",
        example="https://www.linkedin.com/in/williamhgates/",
    )


def raise_exception(message: str) -> None:
    log.error("get_linkedin_profile_reactions_phantombuster function failed", error=message)
    raise NonRetryableError(message)


@function.defn()
async def get_linkedin_profile_reactions_phantombuster(function_input: GetProfileReactionsInput) -> dict[str, Any]:
    try:
        api_key = os.environ.get("PHANTOMBUSTER_API_KEY")
        if not api_key:
            raise_exception("PHANTOMBUSTER_API_KEY is not set")

        headers = {
            "X-Phantombuster-Key-1": api_key,
            "Content-Type": "application/json",
        }

        agent_id = os.environ.get("PHANTOMBUSTER_REACTIONS_AGENT_ID")
        if not agent_id:
            raise_exception("PHANTOMBUSTER_REACTIONS_AGENT_ID is not set")

        argument = {
            "sessionCookie": os.environ.get("LINKEDIN_SESSION_COOKIE"),
            "spreadsheetUrl": function_input.profile_url,
            "homerun": True,
        }

        async with httpx.AsyncClient() as client:
            log.info(f"Initiating scrape for {function_input.profile_url}")
            launch_url = f"https://api.phantombuster.com/api/v1/agent/{agent_id}/launch"
            response = await client.post(launch_url, headers=headers, json={"argument": argument})
            response.raise_for_status()
            
            response_json = response.json()
            log.info(f"Phantombuster launch response: {response_json}")

            container_id = response_json.get("data", {}).get("containerId")
            if not container_id:
                raise_exception("Failed to get containerId from Phantombuster launch response.")

            log.info(f"Scrape initiated. Container ID: {container_id}")

            status_response = {}
            while True:
                log.info(f"Checking status for container {container_id}...")
                output_url = f"https://api.phantombuster.com/api/v2/containers/fetch?id={container_id}&withResultObject=true"
                response = await client.get(output_url, headers=headers)
                response.raise_for_status()
                log.info(f"Phantombuster response: {response.json()}")
                
                status_response = response.json()
                status = status_response.get("status")
                result_object = status_response.get("resultObject")
                log.info(f"Container status: {status}")

                if status == "finished":
                    break
                elif status == "failed":
                    raise_exception(f"Phantombuster container {container_id} failed. Details: {status_response}")
                
                await asyncio.sleep(5)
            
            log.info(f"Phantombuster job for container {container_id} finished successfully.")
            return {"status": "success", "containerId": container_id, "resultObject": result_object}

    except Exception as e:
        error_message = f"get_linkedin_profile_reactions_phantombuster failed: {e}"
        raise NonRetryableError(error_message) from e
