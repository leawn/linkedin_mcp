import json
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
    from src.functions.phantombuster.get_linkedin_job_details import (
        GetJobDetailsInput,
        get_linkedin_job_details_phantombuster,
    )
    from src.functions.phantombuster.get_linkedin_jobs_search import (
        GetJobsSearchInput,
        get_linkedin_jobs_search_phantombuster,
    )


def _parse_result_object(result_object: Any) -> Any:
    if isinstance(result_object, str):
        try:
            return json.loads(result_object)
        except json.JSONDecodeError:
            return result_object

    return result_object


def _extract_job_urls(result_object: Any) -> list[str]:
    parsed_result = _parse_result_object(result_object)
    urls: list[str] = []

    def collect(value: Any) -> None:
        if isinstance(value, dict):
            for key in ("jobUrl", "url", "linkedinJobUrl", "link"):
                url = value.get(key)
                if isinstance(url, str) and "linkedin.com/jobs" in url:
                    urls.append(url)

            for nested_value in value.values():
                collect(nested_value)
        elif isinstance(value, list):
            for item in value:
                collect(item)

    collect(parsed_result)
    return list(dict.fromkeys(urls))


@workflow.defn(description="Scrape LinkedIn job search results and job details using Phantombuster", mcp=True)
class ScrapeLinkedinJobsWorkflowPhantombuster:
    @workflow.run
    async def run(self, workflow_input: GetJobsSearchInput) -> dict[str, Any]:
        log.info("ScrapeLinkedinJobsWorkflowPhantombuster started")
        try:
            search_result = await workflow.step(
                function=get_linkedin_jobs_search_phantombuster,
                function_input=GetJobsSearchInput(search_url=workflow_input.search_url),
                start_to_close_timeout=timedelta(seconds=300),
                task_queue=TASK_QUEUE,
            )

            job_urls = _extract_job_urls(search_result.get("resultObject"))
            if not job_urls:
                raise NonRetryableError("No LinkedIn job URLs found in Phantombuster search result.")

            # Single job per call for now: scrape details for the first job found.
            first_job_url = job_urls[0]
            details_result = await workflow.step(
                function=get_linkedin_job_details_phantombuster,
                function_input=GetJobDetailsInput(job_url=first_job_url),
                start_to_close_timeout=timedelta(seconds=600),
                task_queue=TASK_QUEUE,
            )
        except Exception as e:
            error_message = f"Error during scrape_linkedin_jobs_phantombuster: {e}"
            raise NonRetryableError(error_message) from e
        else:
            result = {
                "search": search_result,
                "jobUrls": job_urls,
                "scrapedJobUrl": first_job_url,
                "details": details_result,
            }
            log.info("scrape_linkedin_jobs_phantombuster done", result=result)

            return result
