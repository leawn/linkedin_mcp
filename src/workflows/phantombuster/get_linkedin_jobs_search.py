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
    from src.functions.phantombuster.get_linkedin_jobs_search import (
        GetJobsSearchInput,
        get_linkedin_jobs_search_phantombuster,
    )


@workflow.defn(description="Get LinkedIn jobs search results using Phantombuster", mcp=True)
class GetLinkedinJobsSearchWorkflowPhantombuster:
    @workflow.run
    async def run(self, workflow_input: GetJobsSearchInput | None = None) -> dict[str, Any]:
        log.info("GetLinkedinJobsSearchWorkflowPhantombuster started")
        try:
            search_url = workflow_input.search_url if workflow_input else None
            result = await workflow.step(
                function=get_linkedin_jobs_search_phantombuster,
                function_input=GetJobsSearchInput(search_url=search_url),
                start_to_close_timeout=timedelta(seconds=300),
                task_queue=TASK_QUEUE,
            )
        except Exception as e:
            error_message = f"Error during get_linkedin_jobs_search_phantombuster: {e}"
            raise NonRetryableError(error_message) from e
        else:
            log.info("get_linkedin_jobs_search_phantombuster done", result=result)

            return result
