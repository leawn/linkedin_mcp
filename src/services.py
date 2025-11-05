import asyncio
import logging
import webbrowser
from pathlib import Path
import os

from watchfiles import run_process

from src.client import client

# Import brightdata functions and workflows
from src.functions.linkedin.create_post import create_post_on_linkedin
from src.workflows.linkedin.create_post import CreatePostOnLinkedinWorkflow
from src.functions.brightdata.get_linkedin_profile import get_linkedin_profile_brightdata
from src.workflows.brightdata.get_linkedin_profile import GetLinkedinProfileWorkflowBrightdata
from src.functions.brightdata.get_linkedin_profile_posts import get_linkedin_profile_posts_brightdata
from src.workflows.brightdata.get_linkedin_profile_posts import GetLinkedinProfilePostsWorkflowBrightdata
from src.functions.brightdata.get_linkedin_profile_reactions import get_linkedin_profile_reactions_brightdata
from src.workflows.brightdata.get_linkedin_profile_reactions import GetLinkedinProfileReactionsWorkflowBrightdata

# Import phantombuster functions and workflows
from src.functions.phantombuster.get_linkedin_profile import get_linkedin_profile_phantombuster
from src.workflows.phantombuster.get_linkedin_profile import GetLinkedinProfileWorkflowPhantombuster
from src.functions.phantombuster.get_linkedin_profile_posts import get_linkedin_profile_posts_phantombuster
from src.workflows.phantombuster.get_linkedin_profile_posts import GetLinkedinProfilePostsWorkflowPhantombuster
from src.functions.phantombuster.get_linkedin_profile_reactions import get_linkedin_profile_reactions_phantombuster
from src.workflows.phantombuster.get_linkedin_profile_reactions import GetLinkedinProfileReactionsWorkflowPhantombuster
from src.functions.phantombuster.save_linkedin_lead import save_linkedin_lead_phantombuster
from src.workflows.phantombuster.save_linkedin_lead import SaveLinkedinLeadWorkflowPhantombuster


async def main() -> None:
    workflows = [
        CreatePostOnLinkedinWorkflow,
        # Phantombuster
        GetLinkedinProfileWorkflowPhantombuster,
        GetLinkedinProfilePostsWorkflowPhantombuster,
        GetLinkedinProfileReactionsWorkflowPhantombuster,
        SaveLinkedinLeadWorkflowPhantombuster,
        # Brightdata
        GetLinkedinProfileWorkflowBrightdata,
        GetLinkedinProfilePostsWorkflowBrightdata,
        GetLinkedinProfileReactionsWorkflowBrightdata,
    ]
    functions = [
        create_post_on_linkedin,
        # Phantombuster
        get_linkedin_profile_phantombuster,
        get_linkedin_profile_posts_phantombuster,
        get_linkedin_profile_reactions_phantombuster,
        save_linkedin_lead_phantombuster,
        # Brightdata
        get_linkedin_profile_brightdata,
        get_linkedin_profile_posts_brightdata,
        get_linkedin_profile_reactions_brightdata,
    ]

    await client.start_service(
        agents=[],
        workflows=workflows,
        functions=functions,
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
