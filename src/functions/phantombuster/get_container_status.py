import os
from typing import Any

import httpx
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from restack_ai.function import NonRetryableError, function, log

load_dotenv()


class ContainerStatusInput(BaseModel):
    """Input parameters for fetching a Phantombuster container status."""

    model_config = {
        "strict": True,
        "extra": "forbid",
        "validate_assignment": True,
        "str_strip_whitespace": True,
    }

    container_id: str = Field(
        ...,
        title="Phantombuster Container ID",
        description="The container ID returned when launching a Phantom.",
        example="5058686828788156",
    )


def raise_exception(message: str) -> None:
    log.error("get_phantombuster_container_status function failed", error=message)
    raise NonRetryableError(message)


@function.defn()
async def get_phantombuster_container_status(function_input: ContainerStatusInput) -> dict[str, Any]:
    """Fetches the status of a Phantombuster container without waiting for completion.

    Returns the run status (e.g. "running", "finished") plus the end type
    ("success", "error", ...) once the run has completed.
    """
    try:
        api_key = os.environ.get("PHANTOMBUSTER_API_KEY")
        if not api_key:
            raise_exception("PHANTOMBUSTER_API_KEY is not set")

        headers = {
            "X-Phantombuster-Key-1": api_key,
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            url = f"https://api.phantombuster.com/api/v2/containers/fetch?id={function_input.container_id}"
            response = await client.get(url, headers=headers)
            response.raise_for_status()

            status_response = response.json()
            log.info(f"Phantombuster container status: {status_response}")

            status = status_response.get("status")
            end_type = status_response.get("lastEndType") or status_response.get("endType")
            is_finished = status == "finished"

            return {
                "containerId": function_input.container_id,
                "status": status,
                "endType": end_type,
                "isFinished": is_finished,
            }

    except Exception as e:
        error_message = f"get_phantombuster_container_status failed: {e}"
        raise NonRetryableError(error_message) from e
