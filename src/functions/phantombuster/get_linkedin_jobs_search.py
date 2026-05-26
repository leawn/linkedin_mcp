import asyncio
import os
from typing import Any

import httpx
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from restack_ai.function import NonRetryableError, function, log

load_dotenv()


class GetJobsSearchInput(BaseModel):
    """Input parameters for exporting LinkedIn job search results."""

    model_config = {
        "strict": True,
        "extra": "forbid",
        "validate_assignment": True,
        "str_strip_whitespace": True,
    }

    search_url: str = Field(
        ...,
        title="LinkedIn Jobs Search URL",
        description="The LinkedIn jobs search results URL to export.",
        example="https://www.linkedin.com/jobs/search-results/?keywords=forward%20deployed%20engineer",
    )


def raise_exception(message: str) -> None:
    log.error("get_linkedin_jobs_search_phantombuster function failed", error=message)
    raise NonRetryableError(message)


@function.defn()
async def get_linkedin_jobs_search_phantombuster(function_input: GetJobsSearchInput) -> dict[str, Any]:
    try:
        api_key = os.environ.get("PHANTOMBUSTER_API_KEY")
        if not api_key:
            raise_exception("PHANTOMBUSTER_API_KEY is not set")

        session_cookie = os.environ.get("LINKEDIN_SESSION_COOKIE")
        if not session_cookie:
            raise_exception("LINKEDIN_SESSION_COOKIE is not set")

        headers = {
            "X-Phantombuster-Key-1": api_key,
            "Content-Type": "application/json",
        }

        agent_id = os.environ.get("PHANTOMBUSTER_JOBS_SEARCH_AGENT_ID")
        if not agent_id:
            raise_exception("PHANTOMBUSTER_JOBS_SEARCH_AGENT_ID is not set")

        argument = {
            "sessionCookie": session_cookie,
            "searches": function_input.search_url,
            "category": "jobs",
            "numberOfResultsPerLaunch": 100,
            "numberOfResultsPerSearch": 100,
        }

        async with httpx.AsyncClient() as client:
            log.info(f"Initiating LinkedIn jobs search export for {function_input.search_url}")
            launch_url = f"https://api.phantombuster.com/api/v1/agent/{agent_id}/launch"
            response = await client.post(launch_url, headers=headers, json={"argument": argument})
            response.raise_for_status()

            response_json = response.json()
            log.info(f"Phantombuster launch response: {response_json}")

            container_id = response_json.get("data", {}).get("containerId")
            if not container_id:
                raise_exception("Failed to get containerId from Phantombuster launch response.")

            log.info(f"LinkedIn jobs search export initiated. Container ID: {container_id}")

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
        error_message = f"get_linkedin_jobs_search_phantombuster failed: {e}"
        raise NonRetryableError(error_message) from e
