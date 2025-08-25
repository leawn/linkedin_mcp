import asyncio
import sys
import time

from restack_ai import Restack


async def main() -> None:
    client = Restack()

    workflow_id = f"{int(time.time() * 1000)}-CreatePostOnLinkedin"
    runId = await client.schedule_workflow(
        workflow_name="CreatePostOnLinkedin",
        workflow_id=workflow_id
    )

    await client.get_workflow_result(
        workflow_id=workflow_id,
        run_id=runId
    )

    sys.exit(0)


def run_schedule() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    run_schedule()
