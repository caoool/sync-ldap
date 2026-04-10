from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env relative to the project root (one level up from app/)
# Used for local dev; in Docker, env vars come from compose env_file
_env_file = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_env_file) if _env_file.exists() else None,
        env_file_encoding="utf-8",
    )

    # WeCom self-built app (自建应用) with contacts read permission
    wecom_corpid: str = ""
    wecom_corpsecret: str = ""
    wecom_api_base: str = "https://qyapi.weixin.qq.com/cgi-bin"

    # LDAP
    ldap_host: str = "openldap"
    ldap_port: int = 389
    ldap_admin_dn: str = "cn=admin,dc=xzs,dc=dev"
    ldap_admin_password: str = "Xzs123456!"
    ldap_base_dn: str = "dc=xzs,dc=dev"
    ldap_user_ou: str = "people"  # top-level OU for users

    # Default password for new LDAP users (set on creation only)
    ldap_default_password: str = "changeme"  # users should change after first login

    # Email
    email_suffix: str = ""  # e.g. "@example.com" → uid+suffix as mail; blank to skip

    # Sync
    sync_interval_minutes: int = 30
    sync_delete_orphans: bool = False  # safety: don't delete by default
    dry_run: bool = False


settings = Settings()
