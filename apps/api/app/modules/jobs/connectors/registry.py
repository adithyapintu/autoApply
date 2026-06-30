from app.modules.jobs.connectors.ashby import AshbyConnector
from app.modules.jobs.connectors.base import JobConnector
from app.modules.jobs.connectors.company_pages import CompanyPageConnector
from app.modules.jobs.connectors.greenhouse import GreenhouseConnector
from app.modules.jobs.connectors.indeed import IndeedConnector
from app.modules.jobs.connectors.lever import LeverConnector
from app.modules.jobs.connectors.linkedin import LinkedInConnector
from app.modules.jobs.connectors.naukri import NaukriConnector
from app.modules.jobs.connectors.smartrecruiters import SmartRecruitersConnector
from app.modules.jobs.connectors.wellfound import WellfoundConnector
from app.modules.jobs.connectors.workday import WorkdayConnector

# Sources that accept keyword queries (natural language) — used when source="all"
KEYWORD_SOURCES = {"linkedin", "indeed", "naukri", "wellfound"}


class ConnectorRegistry:
    def __init__(self, connectors: list[JobConnector] | None = None):
        self._connectors = {connector.source: connector for connector in connectors or [
            GreenhouseConnector(),
            LeverConnector(),
            WorkdayConnector(),
            AshbyConnector(),
            SmartRecruitersConnector(),
            WellfoundConnector(),
            LinkedInConnector(),
            IndeedConnector(),
            NaukriConnector(),
            CompanyPageConnector(),
        ]}

    def get(self, source: str) -> JobConnector | None:
        return self._connectors.get(source)

    def all(self) -> list[JobConnector]:
        return list(self._connectors.values())

    def keyword_connectors(self) -> list[JobConnector]:
        """Connectors that accept freeform keyword queries."""
        return [c for c in self._connectors.values() if c.source in KEYWORD_SOURCES]


_registry = ConnectorRegistry()


def get_connector(source: str) -> JobConnector | None:
    return _registry.get(source)


def get_keyword_connectors() -> list[JobConnector]:
    return _registry.keyword_connectors()

