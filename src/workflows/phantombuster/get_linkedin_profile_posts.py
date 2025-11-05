from datetime import timedelta
from typing import Any

from restack_ai.workflow import (
    NonRetryableError,
    import_functions,
    log,
    workflow,
)

with import_functions():
    from src.functions.phantombuster.get_linkedin_profile_posts import (
        GetProfilePostsInput,
        get_linkedin_profile_posts_phantombuster,
    )


@workflow.defn(description="Get a LinkedIn profile's posts using Phantombuster")
class GetLinkedinProfilePostsWorkflowPhantombuster:
    @workflow.run
    async def run(self, workflow_input: GetProfilePostsInput) -> dict[str, Any]:
        log.info("GetLinkedinProfilePostsWorkflowPhantombuster started")
        try:
            result = await workflow.step(
                function=get_linkedin_profile_posts_phantombuster,
                function_input=GetProfilePostsInput(profile_url=workflow_input.profile_url),
                start_to_close_timeout=timedelta(seconds=120),
            )
        except Exception as e:
            error_message = f"Error during get_linkedin_profile_posts_phantombuster: {e}"
            raise NonRetryableError(error_message) from e
        else:
            log.info("get_linkedin_profile_posts_phantombuster done", result=result)

            return result
