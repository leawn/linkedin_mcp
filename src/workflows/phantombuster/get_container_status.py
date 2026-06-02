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
    from src.functions.phantombuster.get_container_status import (
        ContainerStatusInput,
        get_phantombuster_container_status,
    )


@workflow.defn(
    description="Get the status of a Phantombuster container run by its container ID",
    mcp=True,
)
class GetContainerStatusWorkflowPhantombuster:
    @workflow.run
    async def run(self, workflow_input: ContainerStatusInput) -> dict[str, Any]:
        log.info("GetContainerStatusWorkflowPhantombuster started")
        try:
            result = await workflow.step(
                function=get_phantombuster_container_status,
                function_input=ContainerStatusInput(container_id=workflow_input.container_id),
                start_to_close_timeout=timedelta(seconds=60),
                task_queue=TASK_QUEUE,
            )
        except Exception as e:
            error_message = f"Error during get_phantombuster_container_status: {e}"
            raise NonRetryableError(error_message) from e
        else:
            log.info("get_phantombuster_container_status done", result=result)

            return result
