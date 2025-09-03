from datetime import timedelta
from typing import Any

from pydantic import BaseModel
from restack_ai.workflow import (
    NonRetryableError,
    import_functions,
    log,
    workflow,
)

with import_functions():
    from src.functions.create_post_on_linkedin import CreatePostInput, create_post_on_linkedin_again


@workflow.defn(description="Create a post on LinkedIn")
class CreatePostOnLinkedinWorkflow:
    @workflow.run
    async def run(self, workflow_input: CreatePostInput) -> dict[str, Any]:
        log.info("CreatePostOnLinkedinWorkflow started")
        try:
            result = await workflow.step(
                function=create_post_on_linkedin_again,
                function_input=CreatePostInput(text=workflow_input.text, author_urn=workflow_input.author_urn, access_token=workflow_input.access_token),
                start_to_close_timeout=timedelta(seconds=120),
            )
        except Exception as e:
            error_message = f"Error during create_post_on_linkedin: {e}"
            raise NonRetryableError(error_message) from e
        else:
            log.info("create_post_on_linkedin done", result=result)

            return result