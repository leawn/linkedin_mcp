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
    from src.functions.phantombuster.launch_linkedin_job_details import (
        LaunchJobDetailsInput,
        launch_linkedin_job_details_phantombuster,
    )


@workflow.defn(
    description="Launch a LinkedIn job details export using Phantombuster and return its container ID",
    mcp=True,
)
class LaunchLinkedinJobDetailsWorkflowPhantombuster:
    @workflow.run
    async def run(self, workflow_input: LaunchJobDetailsInput | None = None) -> dict[str, Any]:
        log.info("LaunchLinkedinJobDetailsWorkflowPhantombuster started")
        try:
            result = await workflow.step(
                function=launch_linkedin_job_details_phantombuster,
                function_input=LaunchJobDetailsInput(),
                start_to_close_timeout=timedelta(seconds=120),
                task_queue=TASK_QUEUE,
            )
        except Exception as e:
            error_message = f"Error during launch_linkedin_job_details_phantombuster: {e}"
            raise NonRetryableError(error_message) from e
        else:
            log.info("launch_linkedin_job_details_phantombuster done", result=result)

            return result
