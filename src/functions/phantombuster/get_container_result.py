import os
from typing import Any

import httpx
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from restack_ai.function import NonRetryableError, function, log

load_dotenv()


class ContainerResultInput(BaseModel):
    """Input parameters for fetching a Phantombuster container result object."""

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
    log.error("get_phantombuster_container_result function failed", error=message)
    raise NonRetryableError(message)


@function.defn()
async def get_phantombuster_container_result(function_input: ContainerResultInput) -> dict[str, Any]:
    """Fetches the result object of a finished Phantombuster container.

    Call this after the status workflow reports the container as finished. The
    resultObject is the JSON payload produced by the Phantom run (e.g. the list
    of scraped jobs).
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
            url = f"https://api.phantombuster.com/api/v2/containers/fetch-result-object?id={function_input.container_id}"
            response = await client.get(url, headers=headers)
            response.raise_for_status()

            result_response = response.json()
            result_object = result_response.get("resultObject")
            log.info(f"Phantombuster container {function_input.container_id} result fetched.")

            return {
                "containerId": function_input.container_id,
                "resultObject": result_object,
            }

    except Exception as e:
        error_message = f"get_phantombuster_container_result failed: {e}"
        raise NonRetryableError(error_message) from e
