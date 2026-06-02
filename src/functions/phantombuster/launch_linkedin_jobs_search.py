import asyncio
import os
from typing import Any

import httpx
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from restack_ai.function import NonRetryableError, function, log

load_dotenv()


class LaunchJobsSearchInput(BaseModel):
    """Input parameters for launching a LinkedIn jobs search export."""

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
    log.error("launch_linkedin_jobs_search_phantombuster function failed", error=message)
    raise NonRetryableError(message)


@function.defn()
async def launch_linkedin_jobs_search_phantombuster(function_input: LaunchJobsSearchInput) -> dict[str, Any]:
    """Launches the LinkedIn jobs search Phantom and returns the container ID immediately.

    Unlike get_linkedin_jobs_search_phantombuster, this does not poll for completion.
    Use the returned containerId with the status/result workflows to track progress.
    """
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
        # field for this launch via bonusArgument merge semantics.
        payload: dict[str, Any] = {"id": agent_id}
        if function_input.search_url:
            payload["bonusArgument"] = {"linkedInSearchUrl": function_input.search_url}

        async with httpx.AsyncClient() as client:
            log.info(
                "Launching LinkedIn jobs search export "
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

            log.info(f"LinkedIn jobs search export launched. Container ID: {container_id}")
            return {"status": "launched", "containerId": container_id}

    except Exception as e:
        error_message = f"launch_linkedin_jobs_search_phantombuster failed: {e}"
        raise NonRetryableError(error_message) from e
