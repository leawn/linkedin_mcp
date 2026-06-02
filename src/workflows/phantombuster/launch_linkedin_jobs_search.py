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
    from src.functions.phantombuster.launch_linkedin_jobs_search import (
        LaunchJobsSearchInput,
        launch_linkedin_jobs_search_phantombuster,
    )


@workflow.defn(
    description="Launch a LinkedIn jobs search export using Phantombuster and return its container ID",
    mcp=True,
)
class LaunchLinkedinJobsSearchWorkflowPhantombuster:
    @workflow.run
    async def run(self, workflow_input: LaunchJobsSearchInput | None = None) -> dict[str, Any]:
        log.info("LaunchLinkedinJobsSearchWorkflowPhantombuster started")
        try:
            search_url = workflow_input.search_url if workflow_input else None
            result = await workflow.step(
                function=launch_linkedin_jobs_search_phantombuster,
                function_input=LaunchJobsSearchInput(search_url=search_url),
                start_to_close_timeout=timedelta(seconds=120),
                task_queue=TASK_QUEUE,
            )
        except Exception as e:
            error_message = f"Error during launch_linkedin_jobs_search_phantombuster: {e}"
            raise NonRetryableError(error_message) from e
        else:
            log.info("launch_linkedin_jobs_search_phantombuster done", result=result)

            return result
