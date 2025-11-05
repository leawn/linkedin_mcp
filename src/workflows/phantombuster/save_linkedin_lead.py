from datetime import timedelta
from typing import Any, Dict

from restack_ai.workflow import (
    NonRetryableError,
    import_functions,
    log,
    workflow,
)

with import_functions():
    from src.functions.phantombuster.save_linkedin_lead import (
        SaveLeadInput,
        save_linkedin_lead_phantombuster,
    )

@workflow.defn(description="Save a LinkedIn lead to Phantombuster storage.")
class SaveLinkedinLeadWorkflowPhantombuster:
    @workflow.run
    async def run(self, workflow_input: SaveLeadInput) -> dict[str, Any]:
        log.info("SaveLinkedinLeadWorkflowPhantombuster started")
        try:
            result = await workflow.step(
                function=save_linkedin_lead_phantombuster,
                function_input=SaveLeadInput(linkedin_profile_url=workflow_input.linkedin_profile_url),
                start_to_close_timeout=timedelta(seconds=60),
            )
        except Exception as e:
            error_message = f"Error during save_linkedin_lead_phantombuster: {e}"
            raise NonRetryableError(error_message) from e
        else:
            log.info("save_linkedin_lead_phantombuster done", result=result)
            return result
