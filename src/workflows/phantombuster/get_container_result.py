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
    from src.functions.phantombuster.get_container_result import (
        ContainerResultInput,
        get_phantombuster_container_result,
    )


@workflow.defn(
    description="Get the result object of a finished Phantombuster container run by its container ID",
    mcp=True,
)
class GetContainerResultWorkflowPhantombuster:
    @workflow.run
    async def run(self, workflow_input: ContainerResultInput) -> dict[str, Any]:
        log.info("GetContainerResultWorkflowPhantombuster started")
        try:
            result = await workflow.step(
                function=get_phantombuster_container_result,
                function_input=ContainerResultInput(container_id=workflow_input.container_id),
                start_to_close_timeout=timedelta(seconds=60),
                task_queue=TASK_QUEUE,
            )
        except Exception as e:
            error_message = f"Error during get_phantombuster_container_result: {e}"
            raise NonRetryableError(error_message) from e
        else:
            log.info("get_phantombuster_container_result done", result=result)

            return result
