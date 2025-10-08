import asyncio
import logging
import webbrowser
from pathlib import Path

from watchfiles import run_process

from src.client import client
from src.functions.create_post_on_linkedin import create_post_on_linkedin
from src.workflows.create_post import CreatePostOnLinkedinWorkflow
from src.functions.get_linkedin_profile import get_linkedin_profile
from src.workflows.get_linkedin_profile import GetLinkedinProfileWorkflow
from src.functions.get_linkedin_profile_posts import get_linkedin_profile_posts
from src.workflows.get_linkedin_profile_posts import GetLinkedinProfilePostsWorkflow
from src.functions.get_linkedin_profile_reactions import get_linkedin_profile_reactions
from src.workflows.get_linkedin_profile_reactions import GetLinkedinProfileReactionsWorkflow


async def main() -> None:
    await client.start_service(
        agents=[],
        workflows=[
            CreatePostOnLinkedinWorkflow,
            GetLinkedinProfileWorkflow,
            GetLinkedinProfilePostsWorkflow,
            GetLinkedinProfileReactionsWorkflow,
        ],
        functions=[
            create_post_on_linkedin,
            get_linkedin_profile,
            get_linkedin_profile_posts,
            get_linkedin_profile_reactions,
        ],
    )

# demo purposes

def run_services() -> None:
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Service interrupted by user. Exiting gracefully.")


def watch_services() -> None:
    watch_path = Path.cwd()
    logging.info("Watching %s and its subdirectories for changes...", watch_path)
    webbrowser.open("http://localhost:5233")
    run_process(watch_path, recursive=True, target=run_services)


if __name__ == "__main__":
    run_services()
