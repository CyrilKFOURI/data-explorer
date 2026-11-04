"""The dataset's HTML report (feature 025), generated for the user to download."""

from typing import ClassVar

from pydantic import BaseModel

from app.modules.agent.engine.tools import (
    AppLink,
    Tool,
    ToolContext,
    ToolError,
    ToolOutput,
    wait_for,
)
from app.modules.agent.tools import AppServices


class NoInput(BaseModel):
    pass


class ExportReport(Tool[NoInput]):
    name: ClassVar[str] = "export_report"
    kind = "compute"
    description: ClassVar[str] = (
        "Generate the dataset's HTML report over the filtered rows (summary, key findings, a card "
        "per variable, relationships, correlations, missing values) and give the user a link to "
        "download it. Use it when the user wants something to share or keep."
    )
    Input: ClassVar[type[BaseModel]] = NoInput

    def __init__(self, services: AppServices) -> None:
        self.services = services

    def label(self, args: NoInput) -> str:
        return "Writing the HTML report"

    def run(self, ctx: ToolContext, args: NoInput) -> ToolOutput:
        reports = self.services.reports
        job = reports.start(ctx.dataset_id, ctx.conditions)
        job = wait_for(
            lambda: reports.job(job.id),
            lambda j: j.status != "running",
            ctx,
            describe=lambda j: (j.message or "Writing", j.progress),
            cancel=lambda: reports.cancel(job.id),
        )
        if job.status != "done":
            raise ToolError(f"The report {job.status}: {job.error or 'no detail'}")
        return ToolOutput(
            f"Report ready: {job.file_name}",
            {"file": job.file_name, "note": "The user downloads it from the link under this step."},
            AppLink("report_file", {"job": job.id}, f"Download {job.file_name}"),
        )
