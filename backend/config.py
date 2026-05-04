from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "Zentox Aesthetics CRM"
    debug: bool = False

    # Airtable (base: FiveZeroThree – Operating Hub)
    airtable_api_key: str = ""
    airtable_base_id: str = "appkI2SpAMNfCBvSo"
    airtable_patients_table_id: str = "tblPjNAEk88bk2ta5"
    airtable_appointments_table_id: str = "tblZqUF4SwRgpXL0T"
    airtable_pipeline_table_id: str = "tblU3X0SWlQki32jB"
    airtable_kpi_table_id: str = "tbljBVHkm7QTVn0bO"
    airtable_services_table_id: str = "tblJnheXo8dej0XkG"
    airtable_audit_table_id: str = "tblS4kiozBNkr6MJA"
    airtable_coa_table_id: str = "tblM1nzFuSSzJHQSI"
    airtable_expenses_table_id: str = "tbl431eUodPxY4VKU"
    airtable_staff_table_id: str = "tblTQ3D319BHJSAEK"
    airtable_inventory_table_id: str = "tblkiNYWyl4R8cHVp"
    airtable_documents_table_id: str = "tbloKulA9NfzHxJ1R"

    # File uploads
    upload_dir: str = "uploads/documents"

    # AestheticsPro
    aestheticspro_api_url: str = ""
    aestheticspro_api_key: str = ""

    # GetWeave
    getweave_api_url: str = "https://api.getweave.com"
    getweave_api_key: str = ""
    getweave_location_id: str = ""

    # QuickBooks Online
    qbo_client_id: str = ""
    qbo_client_secret: str = ""
    qbo_refresh_token: str = ""
    qbo_realm_id: str = ""
    qbo_sandbox: bool = False

    # JWT Auth (HIPAA: strong secret required in production)
    jwt_secret_key: str = "CHANGE-ME-USE-256-BIT-RANDOM-IN-PRODUCTION"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60

    # Internal service key (Streamlit → FastAPI)
    internal_api_key: str = "zentox-internal-key-change-in-production"

    # Anthropic (AI agents — claude-haiku-4-5)
    anthropic_api_key: str = ""

    # SMTP (for agent email delivery to info@fivezero3.net)
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""

    # CORS — restrict to your Hostinger domain in production
    allowed_origins: str = "http://localhost:8501,https://crm.zentoxaesthetics.com"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
