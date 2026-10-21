"""The agent's tools on the app's V1 analyses (spec 026, § 5.2). Read-only in 026a."""

from dataclasses import dataclass

from app.domain.columns.service import ColumnService
from app.domain.compare.service import CompareService
from app.domain.correlations.service import CorrelationService
from app.domain.profiling.service import ProfilingService
from app.domain.variable.service import VariableService
from app.modules.agent.engine.tools import ToolRegistry


@dataclass(frozen=True)
class AppServices:
    """The app's services the tools call, injected at setup (no import of other modules)."""

    columns: ColumnService
    profiling: ProfilingService
    variable: VariableService
    compare: CompareService
    correlations: CorrelationService


def default_registry(services: AppServices) -> ToolRegistry:
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

    return ToolRegistry(
        [
            GetDatasetOverview(services),
            ListColumns(services),
            ProfileColumn(services),
            CountRows(services),
            CompareColumns(services),
            GetCorrelations(services),
            RankAssociationsWith(services),
        ]
    )
