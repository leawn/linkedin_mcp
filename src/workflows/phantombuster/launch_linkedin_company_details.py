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
    from src.functions.phantombuster.launch_linkedin_company_details import (
        LaunchCompanyDetailsInput,
        launch_linkedin_company_details_phantombuster,
    )


@workflow.defn(
    description="Launch a LinkedIn company details export using Phantombuster and return its container ID",
    mcp=True,
)
class LaunchLinkedinCompanyDetailsWorkflowPhantombuster:
    @workflow.run
    async def run(self, workflow_input: LaunchCompanyDetailsInput | None = None) -> dict[str, Any]:
        log.info("LaunchLinkedinCompanyDetailsWorkflowPhantombuster started")
        try:
            result = await workflow.step(
                function=launch_linkedin_company_details_phantombuster,
                function_input=LaunchCompanyDetailsInput(),
                start_to_close_timeout=timedelta(seconds=120),
                task_queue=TASK_QUEUE,
            )
        except Exception as e:
            error_message = f"Error during launch_linkedin_company_details_phantombuster: {e}"
            raise NonRetryableError(error_message) from e
        else:
            log.info("launch_linkedin_company_details_phantombuster done", result=result)

            return result
