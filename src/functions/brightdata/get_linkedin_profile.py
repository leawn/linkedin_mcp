import os
from typing import Any
from dotenv import load_dotenv
import asyncio
from pydantic import BaseModel, Field
from restack_ai.function import NonRetryableError, function, log
from brightdata import bdclient

# Changes to this file should also be reflected in the Phantombuster version


class GetProfileInput(BaseModel):
    """Input parameters for getting a LinkedIn profile."""

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
    log.error("get_linkedin_profile_brightdata function failed", error=message)
    raise NonRetryableError(message)


@function.defn()
async def get_linkedin_profile_brightdata(function_input: GetProfileInput) -> dict[str, Any]:
    try:
        api_token = os.environ.get("BRIGHT_DATA_API_TOKEN")
        if not api_token:
            raise_exception("BRIGHT_DATA_API_TOKEN is not set")

        bd = bdclient(api_token)
        log.info(f"Initiating scrape for {function_input.profile_url}")

        initial_response = bd.scrape_linkedin.profiles(function_input.profile_url, sync=True)

        snapshot_id = initial_response.get("snapshot_id")
        if not snapshot_id:
            log.info("Received synchronous response for profile from Bright Data.")
            return initial_response

        log.info(f"Scrape initiated. Snapshot ID: {snapshot_id}")

        while True:
            log.info(f"Checking status for snapshot {snapshot_id}...")
            status_response = await asyncio.to_thread(bd.download_snapshot, snapshot_id=snapshot_id)
            
            status = status_response.get("status")
            log.info(f"Snapshot status: {status}")

            if status == "done":
                break
            elif status == "failed":
                raise_exception(f"Bright Data snapshot {snapshot_id} failed. Details: {status_response}")
            
            await asyncio.sleep(5)
        
        log.info(f"Snapshot {snapshot_id} is ready. Downloading result.")
        profile_data = await asyncio.to_thread(bd.download_snapshot, snapshot_id=snapshot_id)

        if not profile_data:
            raise_exception("Failed to download profile data from Bright Data snapshot.")

    except Exception as e:
        error_message = f"get_linkedin_profile_brightdata failed: {e}"
        raise NonRetryableError(error_message) from e
    else:
        log.info(f"Successfully scraped profile for {function_input.profile_url}")
        return profile_data
