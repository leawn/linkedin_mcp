import asyncio
import os
from typing import Any

import httpx
from dotenv import load_dotenv
from pydantic import BaseModel
from restack_ai.function import NonRetryableError, function, log

load_dotenv()


class LaunchCompanyDetailsInput(BaseModel):
    """Input parameters for launching a LinkedIn company details export."""

    model_config = {
        "strict": True,
        "extra": "forbid",
        "validate_assignment": True,
        "str_strip_whitespace": True,
    }


def raise_exception(message: str) -> None:
    log.error("launch_linkedin_company_details_phantombuster function failed", error=message)
    raise NonRetryableError(message)


@function.defn()
async def launch_linkedin_company_details_phantombuster(
    function_input: LaunchCompanyDetailsInput | None = None,
) -> dict[str, Any]:
    """Launches the LinkedIn company details Phantom and returns the container ID immediately.

    This does not poll for completion. Use the returned containerId with the
    status/result workflows to track progress.
    """
    try:
        api_key = os.environ.get("PHANTOMBUSTER_API_KEY")
        if not api_key:
            raise_exception("PHANTOMBUSTER_API_KEY is not set")

        headers = {
            "X-Phantombuster-Key-1": api_key,
            "Content-Type": "application/json",
        }

        agent_id = os.environ.get("PHANTOMBUSTER_COMPANY_DETAILS_AGENT_ID")
        if not agent_id:
            raise_exception("PHANTOMBUSTER_COMPANY_DETAILS_AGENT_ID is not set")

        payload: dict[str, Any] = {"id": agent_id}

        async with httpx.AsyncClient() as client:
            log.info("Launching LinkedIn company details export with saved default input")
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

            log.info(f"LinkedIn company details export launched. Container ID: {container_id}")
            return {"status": "launched", "containerId": container_id}

    except Exception as e:
        error_message = f"launch_linkedin_company_details_phantombuster failed: {e}"
        raise NonRetryableError(error_message) from e
