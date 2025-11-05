from datetime import timedelta
from typing import Any

from restack_ai.workflow import (
    NonRetryableError,
    import_functions,
    log,
    workflow,
)

with import_functions():
    from src.functions.brightdata.get_linkedin_profile_posts import (
        GetProfilePostsInput,
        get_linkedin_profile_posts_brightdata,
    )


@workflow.defn(description="Get a LinkedIn profile's posts")
class GetLinkedinProfilePostsWorkflowBrightdata:
    @workflow.run
    async def run(self, workflow_input: GetProfilePostsInput) -> dict[str, Any]:
        log.info("GetLinkedinProfilePostsWorkflowBrightdata started")
        try:
            result = await workflow.step(
                function=get_linkedin_profile_posts_brightdata,
                function_input=GetProfilePostsInput(profile_url=workflow_input.profile_url),
                start_to_close_timeout=timedelta(seconds=120),
            )
        except Exception as e:
            error_message = f"Error during get_linkedin_profile_posts_brightdata: {e}"
            raise NonRetryableError(error_message) from e
        else:
            log.info("get_linkedin_profile_posts_brightdata done", result=result)

            return result
