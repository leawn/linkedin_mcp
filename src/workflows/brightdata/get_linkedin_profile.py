from datetime import timedelta
from typing import Any

from restack_ai.workflow import (
    NonRetryableError,
    import_functions,
    log,
    workflow,
    RetryPolicy,
)

from src.client import TASK_QUEUE

with import_functions():
    from src.functions.brightdata.get_linkedin_profile import (
        GetProfileInput,
        SnapshotIdInput,
        download_brightdata_snapshot,
        trigger_linkedin_profile_scrape,
    )


@workflow.defn(description="Get a LinkedIn profile")
class GetLinkedinProfileWorkflowBrightdata:
    @workflow.run
    async def run(self, workflow_input: GetProfileInput) -> Any:
        log.info("GetLinkedinProfileWorkflowBrightdata started")
        try:
            # Step 1: Trigger the scrape and get snapshot_id
            trigger_result = await workflow.step(
                function=trigger_linkedin_profile_scrape,
                function_input=GetProfileInput(profile_url=workflow_input.profile_url),
                start_to_close_timeout=timedelta(seconds=30),
                task_queue=TASK_QUEUE,
            )
            
            # If we got data directly (shouldn't happen with sync=False, but handle it)
            if "snapshot_id" not in trigger_result:
                log.info("Received synchronous response, returning directly")
                return trigger_result
            
            snapshot_id = trigger_result["snapshot_id"]
            log.info(f"Scrape triggered, snapshot_id: {snapshot_id}")
            
            # Step 2: Wait a bit for Bright Data to start processing
            await workflow.sleep(10)
            
            # Step 3: Download the snapshot with retry policy
            # Retry with exponential backoff: start at 10s, max 10 attempts, 2x backoff
            retry_policy = RetryPolicy(
                initial_interval=timedelta(seconds=10),
                maximum_attempts=10,
                backoff_coefficient=2.0,
            )
            
            result = await workflow.step(
                function=download_brightdata_snapshot,
                function_input=SnapshotIdInput(snapshot_id=snapshot_id),
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=retry_policy,
                task_queue=TASK_QUEUE,
            )
            
        except Exception as e:
            error_message = f"Error during get_linkedin_profile_brightdata: {e}"
            raise NonRetryableError(error_message) from e
        else:
            log.info("get_linkedin_profile_brightdata done", result=result)
            return result
