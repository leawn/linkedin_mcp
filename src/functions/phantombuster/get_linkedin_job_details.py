import asyncio
import os
from typing import Any

import httpx
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from restack_ai.function import NonRetryableError, function, log

load_dotenv()


class GetJobDetailsInput(BaseModel):
    """Input parameters for scraping LinkedIn job post details."""

    model_config = {
        "strict": True,
        "extra": "forbid",
        "validate_assignment": True,
        "str_strip_whitespace": True,
    }

    job_url: str = Field(
        ...,
        title="LinkedIn Job URL",
        description="The LinkedIn job post URL to scrape.",
        example="https://www.linkedin.com/jobs/view/4333867793/",
    )


def raise_exception(message: str) -> None:
    log.error("get_linkedin_job_details_phantombuster function failed", error=message)
    raise NonRetryableError(message)


@function.defn()
async def get_linkedin_job_details_phantombuster(function_input: GetJobDetailsInput) -> dict[str, Any]:
    try:
        api_key = os.environ.get("PHANTOMBUSTER_API_KEY")
        if not api_key:
            raise_exception("PHANTOMBUSTER_API_KEY is not set")

        headers = {
            "X-Phantombuster-Key-1": api_key,
            "Content-Type": "application/json",
        }

        agent_id = os.environ.get("PHANTOMBUSTER_JOB_DETAILS_AGENT_ID")
        if not agent_id:
            raise_exception("PHANTOMBUSTER_JOB_DETAILS_AGENT_ID is not set")

        # Only override the job post URL for this launch; the sessionCookie,
        # userAgent and other settings come from the Phantom's saved setup via
        # bonusArgument merge. The Job Scraper accepts a single job post URL,
        # Google Sheet or CSV URL under the "spreadsheetUrl" key.
        bonus_argument = {
            "spreadsheetUrl": function_input.job_url,
        }

        async with httpx.AsyncClient() as client:
            log.info(f"Initiating LinkedIn job details scrape for {function_input.job_url}")
            launch_url = "https://api.phantombuster.com/api/v2/agents/launch"
            payload = {"id": agent_id, "bonusArgument": bonus_argument}
            response = await client.post(launch_url, headers=headers, json=payload)
            response.raise_for_status()

            response_json = response.json()
            log.info(f"Phantombuster launch response: {response_json}")

            container_id = response_json.get("containerId") or response_json.get("data", {}).get("containerId")
            if not container_id:
                raise_exception("Failed to get containerId from Phantombuster launch response.")

            log.info(f"LinkedIn job details scrape initiated. Container ID: {container_id}")

            result_object = None
            while True:
                log.info(f"Checking status for container {container_id}...")
                output_url = f"https://api.phantombuster.com/api/v2/containers/fetch?id={container_id}&withResultObject=true"
                response = await client.get(output_url, headers=headers)
                response.raise_for_status()
                status_response = response.json()
                log.info(f"Phantombuster response: {status_response}")

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
        error_message = f"get_linkedin_job_details_phantombuster failed: {e}"
        raise NonRetryableError(error_message) from e
