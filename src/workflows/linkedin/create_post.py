from datetime import timedelta
from typing import Any

from restack_ai.workflow import (
    NonRetryableError,
    import_functions,
    log,
    workflow,
)

with import_functions():
    from src.functions.linkedin.create_post import (
        CreatePostInput,
        create_post_on_linkedin,
    )


@workflow.defn(description="Create a post on LinkedIn")
class CreatePostOnLinkedinWorkflow:
    @workflow.run
    async def run(self, workflow_input: CreatePostInput) -> dict[str, Any]:
        log.info("CreatePostOnLinkedinWorkflow started")
        try:
            result = await workflow.step(
                function=create_post_on_linkedin,
                function_input=CreatePostInput(text=workflow_input.text),
                start_to_close_timeout=timedelta(seconds=120),
            )
        except Exception as e:
            error_message = f"Error during create_post_on_linkedin: {e}"
            raise NonRetryableError(error_message) from e
        else:
            log.info("create_post_on_linkedin done", result=result)

            return result