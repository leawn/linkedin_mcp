import os
from typing import Any
from dotenv import load_dotenv
import asyncio
from pydantic import BaseModel, Field
from restack_ai.function import NonRetryableError, function, log
from brightdata import bdclient

load_dotenv()


class GetProfilePostsInput(BaseModel):
    """Input parameters for getting a LinkedIn profile's posts."""

    model_config = {
        "strict": True,
        "extra": "forbid",
        "validate_assignment": True,
        "str_strip_whitespace": True,
    }

    profile_url: str = Field(
        ...,
        title="LinkedIn Profile URL",
        description="The URL of the LinkedIn profile's post section.",
        example="https://www.linkedin.com/in/williamhgates/recent-activity/all/",
    )


def raise_exception(message: str) -> None:
    log.error("get_linkedin_profile_posts function failed", error=message)
    raise NonRetryableError(message)


def construct_activity_url(profile_url: str) -> str:
    """Constructs the recent activity URL from a base profile URL if necessary."""
    if "recent-activity" not in profile_url:
        # Ensure the URL ends with a slash before appending
        if not profile_url.endswith('/'):
            profile_url += '/'
        return f"{profile_url}recent-activity/all/"
    return profile_url


@function.defn()
async def get_linkedin_profile_posts(function_input: GetProfilePostsInput) -> dict[str, Any]:
    try:
        api_token = os.environ.get("BRIGHT_DATA_API_TOKEN")
        if not api_token:
            raise_exception("BRIGHT_DATA_API_TOKEN is not set")

        bd = bdclient(api_token)
        
        profile_url = function_input.profile_url.split('recent-activity')[0]
        log.info(f"Initiating post discovery for profile {profile_url}")

        initial_response = await asyncio.to_thread(
            bd.search_linkedin.posts, profile_url=profile_url
        )

        snapshot_id = initial_response.get("snapshot_id")
        if not snapshot_id:
            log.info("Received synchronous response for posts from Bright Data.")
            return initial_response

        log.info(f"Post discovery initiated. Snapshot ID: {snapshot_id}")

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
        posts_data = await asyncio.to_thread(bd.download_snapshot, snapshot_id=snapshot_id)

        if not posts_data:
            raise_exception("Failed to download posts data from Bright Data snapshot.")

    except Exception as e:
        error_message = f"get_linkedin_profile_posts failed: {e}"
        raise NonRetryableError(error_message) from e
    else:
        log.info(f"Successfully discovered posts for {profile_url}")
        return posts_data
