from app.modules.jobs.connectors.registry import ConnectorRegistry


def test_connector_registry_exposes_required_sources() -> None:
    sources = {connector.source for connector in ConnectorRegistry().all()}

    assert {
        "greenhouse",
        "lever",
        "workday",
        "ashby",
        "smartrecruiters",
        "wellfound",
        "company_pages",
    }.issubset(sources)

