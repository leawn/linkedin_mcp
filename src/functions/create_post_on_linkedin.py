import os
from typing import Any

from dotenv import load_dotenv
import aiohttp

from pydantic import BaseModel
from restack_ai.function import NonRetryableError, function, log

load_dotenv()

from pydantic import BaseModel, Field, ValidationError
from typing import Optional

class CreatePostInput(BaseModel):
    """Input parameters for creating a LinkedIn post.
    
    This model defines the required parameters for posting content to LinkedIn
    through the Restack workflow system.
    """
    
    model_config = {
        "strict": True,                    # Enable strict mode
        "extra": "forbid",                 # Reject extra fields (makes it strict)
        "validate_assignment": True,       # Validate on assignment
        "str_strip_whitespace": True,      # Strip whitespace from strings
    }
    
    text: str = Field(
        ...,
        title="Post Content",
        description="The text content of the LinkedIn post. Should be engaging and professional. Supports hashtags and emojis.",
        example="Excited to announce our new AI-powered workflow automation platform! 🚀 #AI #Automation #Tech",
        min_length=1,
        max_length=3000,
        json_schema_extra={"format": "textarea"}
    )

# Usage with validation
def validate_and_use_input(input_data: dict) -> CreatePostInput:
    """Validate input data and return typed model."""
    try:
        # This will raise ValidationError if extra fields are provided (strict mode)
        validated_input = CreatePostInput.model_validate(input_data)
        return validated_input
    except ValidationError as e:
        raise ValueError(f"Invalid input: {e}") from e


def raise_exception(message: str) -> None:
    log.error("create_post_on_linkedin function failed", error=message)
    raise NonRetryableError(message)


@function.defn()
async def create_post_on_linkedin(function_input: CreatePostInput) -> dict[str, Any]:
    try:
            if os.environ.get("LINKEDIN_ACCESS_TOKEN") is None:
                error_message = "LINKEDIN_ACCESS_TOKEN is not set"
                raise_exception(error_message)

            if os.environ.get("LINKEDIN_AUTHOR_URN") is None:
                error_message = "LINKEDIN_AUTHOR_URN is not set"
                raise_exception(error_message)

            access_token=os.environ.get("LINKEDIN_ACCESS_TOKEN")
            author_urn=os.environ.get("LINKEDIN_AUTHOR_URN")
            linkedin_api_url = "https://api.linkedin.com/v2/ugcPosts"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0",
            }
            payload = {
                "author": author_urn,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": function_input.text},
                        "shareMediaCategory": "NONE",
                    }
                },
                "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    linkedin_api_url, json=payload, headers=headers
                ) as response:
                    response.raise_for_status()
                    post_id = response.headers.get("x-restli-id", "Unknown")
    except Exception as e:
        error_message = f"create_post_on_linkedin failed: {e}"
        raise NonRetryableError(error_message) from e
    else:
        log.info(f"Successfully created post on LinkedIn with ID: {post_id}")
        return {
                "status": "success",
                "message": "Successfully created post on LinkedIn",
                "post_id": post_id,
        }
