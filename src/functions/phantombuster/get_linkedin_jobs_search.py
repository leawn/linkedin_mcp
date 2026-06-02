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

    search_url: str | None = Field(
        default=None,
        title="LinkedIn Jobs Search URL",
        description=(
            "Optional LinkedIn jobs search results URL to export. When omitted, the "
            "Phantom runs with its saved default input (e.g. a Google Sheet of search URLs)."
        ),
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

        headers = {
            "X-Phantombuster-Key-1": api_key,
            "Content-Type": "application/json",
        }

        agent_id = os.environ.get("PHANTOMBUSTER_JOBS_SEARCH_AGENT_ID")
        if not agent_id:
            raise_exception("PHANTOMBUSTER_JOBS_SEARCH_AGENT_ID is not set")

        # Launch with the Phantom's saved default input (e.g. a Google Sheet of
        # search URLs). If a specific search_url is provided, override only that
        # field for this launch via bonusArgument merge semantics; everything else
        # (identity/sessionCookie, category, result counts, searchType) is inherited.
        payload: dict[str, Any] = {"id": agent_id}
        if function_input.search_url:
            payload["bonusArgument"] = {"linkedInSearchUrl": function_input.search_url}

        async with httpx.AsyncClient() as client:
            log.info(
                "Initiating LinkedIn jobs search export "
                + (f"for {function_input.search_url}" if function_input.search_url else "with saved default input")
            )
            launch_url = "https://api.phantombuster.com/api/v2/agents/launch"

            # Phantombuster rate-limits /agents/launch (429). Back off and retry
            # instead of failing the whole workflow on a transient throttle.
            max_launch_attempts = 5
            response = None
            for attempt in range(1, max_launch_attempts + 1):
                response = await client.post(launch_url, headers=headers, json=payload)
                if response.status_code != 429:
                    break

                retry_after = response.headers.get("Retry-After")
                wait_seconds = float(retry_after) if retry_after else min(60, 5 * 2 ** (attempt - 1))
                if attempt == max_launch_attempts:
                    raise_exception(
                        f"Phantombuster launch rate-limited (429) after {max_launch_attempts} attempts. "
                        "The agent may already be running or the plan launch quota is exhausted."
                    )
                log.warning(
                    f"Phantombuster launch rate-limited (429). Attempt {attempt}/{max_launch_attempts}, "
                    f"retrying in {wait_seconds}s"
                )
                await asyncio.sleep(wait_seconds)

            response.raise_for_status()

            response_json = response.json()
            log.info(f"Phantombuster launch response: {response_json}")

            container_id = response_json.get("containerId") or response_json.get("data", {}).get("containerId")
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

            # The resultObject on containers/fetch can lag behind the "finished"
            # status (returning null even though the run succeeded). Pull it from
            # the dedicated endpoint and retry briefly until it is available.
            if result_object is None:
                result_url = f"https://api.phantombuster.com/api/v2/containers/fetch-result-object?id={container_id}"
                for attempt in range(1, 6):
                    result_response = await client.get(result_url, headers=headers)
                    result_response.raise_for_status()
                    result_object = result_response.json().get("resultObject")
                    if result_object is not None:
                        break
                    log.info(f"resultObject not ready yet (attempt {attempt}/5), retrying in 3s")
                    await asyncio.sleep(3)

            log.info(f"Phantombuster job for container {container_id} finished successfully.")
            return {"status": "success", "containerId": container_id, "resultObject": result_object}

    except Exception as e:
        error_message = f"get_linkedin_jobs_search_phantombuster failed: {e}"
        raise NonRetryableError(error_message) from e
