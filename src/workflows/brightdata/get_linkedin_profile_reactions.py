from datetime import timedelta
from typing import Any

from restack_ai.workflow import (
    NonRetryableError,
    import_functions,
    log,
    workflow,
)

with import_functions():
    from src.functions.brightdata.get_linkedin_profile_reactions import (
        GetReactionsInput,
        get_linkedin_profile_reactions_brightdata,
    )


@workflow.defn(description="Get a LinkedIn profile's reactions (Not Implemented)")
class GetLinkedinProfileReactionsWorkflowBrightdata:
    @workflow.run
    async def run(self, workflow_input: GetReactionsInput) -> dict[str, Any]:
        log.info("GetLinkedinProfileReactionsWorkflowBrightdata started")
        try:
            # The function call will always raise an error in this version.
            result = await workflow.step(
                function=get_linkedin_profile_reactions_brightdata,
                function_input=GetReactionsInput(profile_url=workflow_input.profile_url),
                start_to_close_timeout=timedelta(seconds=60),
            )
        except Exception as e:
            # The error from the function is re-raised to be shown to the user.
            error_message = f"Error during get_linkedin_profile_reactions_brightdata: {e}"
            raise NonRetryableError(error_message) from e
        else:
            log.info("get_linkedin_profile_reactions_brightdata done", result=result)
            return result
