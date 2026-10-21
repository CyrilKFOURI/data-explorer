"""The agent's tools on the app's V1 analyses (spec 026, § 5.2). Read-only in 026a."""

from dataclasses import dataclass
from typing import Any

from app.domain.columns.service import ColumnService
from app.domain.compare.service import CompareService
from app.domain.correlations.service import CorrelationService
from app.domain.profiling.service import ProfilingService
from app.domain.report.service import ReportService
from app.domain.variable.service import VariableService
from app.modules.agent.engine.tools import Tool, ToolRegistry


@dataclass(frozen=True)
class AppServices:
    """The app's services the tools call, injected at setup (no import of other modules)."""

    columns: ColumnService
    profiling: ProfilingService
    variable: VariableService
    compare: CompareService
    correlations: CorrelationService
    reports: ReportService


def default_registry(services: AppServices, extra: list[Tool[Any]] | None = None) -> ToolRegistry:
    """The agent's own tools on the V1 analyses, then the tools the modules offer."""
    from app.modules.agent.tools.dataset import (
        CountRows,
        GetDatasetOverview,
        ListColumns,
        ProfileColumn,
    )
    from app.modules.agent.tools.relations import (
        CompareColumns,
        GetCorrelations,
        RankAssociationsWith,
    )
    from app.modules.agent.tools.report import ExportReport

    return ToolRegistry(
        [
            GetDatasetOverview(services),
            ListColumns(services),
            ProfileColumn(services),
            CountRows(services),
            CompareColumns(services),
            GetCorrelations(services),
            RankAssociationsWith(services),
            ExportReport(services),
            *(extra or []),
        ]
    )
