from datetime import timedelta
from typing import Any

from restack_ai.workflow import (
    NonRetryableError,
    import_functions,
    log,
    workflow,
)

from src.client import TASK_QUEUE

with import_functions():
    from src.functions.phantombuster.get_linkedin_job_details import (
        GetJobDetailsInput,
        get_linkedin_job_details_phantombuster,
    )


@workflow.defn(description="Get LinkedIn job details using Phantombuster", mcp=True)
class GetLinkedinJobDetailsWorkflowPhantombuster:
    @workflow.run
    async def run(self, workflow_input: GetJobDetailsInput) -> dict[str, Any]:
        log.info("GetLinkedinJobDetailsWorkflowPhantombuster started")
        try:
            result = await workflow.step(
                function=get_linkedin_job_details_phantombuster,
                function_input=GetJobDetailsInput(job_urls=workflow_input.job_urls),
                start_to_close_timeout=timedelta(seconds=600),
                task_queue=TASK_QUEUE,
            )
        except Exception as e:
            error_message = f"Error during get_linkedin_job_details_phantombuster: {e}"
            raise NonRetryableError(error_message) from e
        else:
            log.info("get_linkedin_job_details_phantombuster done", result=result)

            return result
