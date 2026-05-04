"""
Thin wrapper around pyairtable so all table handles are built once
and shared across routers.
"""
from pyairtable import Api
from backend.config import get_settings

_settings = get_settings()
_api: Api | None = None


def get_api() -> Api:
    global _api
    if _api is None:
        _api = Api(_settings.airtable_api_key)
    return _api


def patients_table():
    return get_api().table(_settings.airtable_base_id, _settings.airtable_patients_table_id)


def appointments_table():
    return get_api().table(_settings.airtable_base_id, _settings.airtable_appointments_table_id)


def pipeline_table():
    return get_api().table(_settings.airtable_base_id, _settings.airtable_pipeline_table_id)


def kpi_table():
    return get_api().table(_settings.airtable_base_id, _settings.airtable_kpi_table_id)


def services_table():
    return get_api().table(_settings.airtable_base_id, _settings.airtable_services_table_id)


def audit_table():
    return get_api().table(_settings.airtable_base_id, _settings.airtable_audit_table_id)


def coa_table():
    return get_api().table(_settings.airtable_base_id, _settings.airtable_coa_table_id)


def expenses_table():
    return get_api().table(_settings.airtable_base_id, _settings.airtable_expenses_table_id)


def staff_table():
    return get_api().table(_settings.airtable_base_id, _settings.airtable_staff_table_id)


def inventory_table():
    return get_api().table(_settings.airtable_base_id, _settings.airtable_inventory_table_id)


def get_documents_table():
    return get_api().table(_settings.airtable_base_id, _settings.airtable_documents_table_id)
