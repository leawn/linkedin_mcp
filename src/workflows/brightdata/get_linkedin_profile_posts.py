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
    from src.functions.brightdata.get_linkedin_profile_posts import (
        GetProfilePostsInput,
        trigger_linkedin_profile_posts_scrape,
    )
    from src.functions.brightdata.get_linkedin_profile import (
        SnapshotIdInput,
        download_brightdata_snapshot,
    )


@workflow.defn(description="Get a LinkedIn profile's posts")
class GetLinkedinProfilePostsWorkflowBrightdata:
    @workflow.run
    async def run(self, workflow_input: GetProfilePostsInput) -> Any:
        log.info("GetLinkedinProfilePostsWorkflowBrightdata started")
        try:
            # Step 1: Trigger the scrape and get snapshot_id
            trigger_result = await workflow.step(
                function=trigger_linkedin_profile_posts_scrape,
                function_input=GetProfilePostsInput(profile_url=workflow_input.profile_url),
                start_to_close_timeout=timedelta(seconds=30),
                task_queue=TASK_QUEUE,
            )
            
            # If we got data directly (shouldn't happen, but handle it)
            if "snapshot_id" not in trigger_result:
                log.info("Received synchronous response, returning directly")
                return trigger_result
            
            snapshot_id = trigger_result["snapshot_id"]
            log.info(f"Posts scrape triggered, snapshot_id: {snapshot_id}")
            
            # Step 2: Wait a bit for Bright Data to start processing
            # Posts typically take longer, so wait 60 seconds (like in your TypeScript example)
            await workflow.sleep(60)
            
            # Step 3: Download the snapshot with retry policy
            # Retry with exponential backoff: start at 1m, max 10 attempts, 2x backoff
            retry_policy = RetryPolicy(
                initial_interval=timedelta(minutes=1),
                maximum_attempts=10,
                backoff_coefficient=2.0,
            )
            
            result = await workflow.step(
                function=download_brightdata_snapshot,
                function_input=SnapshotIdInput(snapshot_id=snapshot_id),
                start_to_close_timeout=timedelta(minutes=30),
                retry_policy=retry_policy,
                task_queue=TASK_QUEUE,
            )
            
        except Exception as e:
            error_message = f"Error during get_linkedin_profile_posts_brightdata: {e}"
            raise NonRetryableError(error_message) from e
        else:
            log.info("get_linkedin_profile_posts_brightdata done", result=result)
            return result
