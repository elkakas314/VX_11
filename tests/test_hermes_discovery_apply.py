import os
from config.db_schema import get_session, CLIProvider
from config.settings import settings


def test_deepseek_registration():
    """Ensure that DeepSeek R1 gets registered when settings.deepseek_base_url is set."""
    orig = getattr(settings, "deepseek_base_url", None)
    settings.deepseek_base_url = "https://api.deepseek.example/v1"
    try:
        db = get_session()
        existing = db.query(CLIProvider).filter_by(name="deepseek_r1").first()
        if existing:
            existing.enabled = False
            db.add(existing)
            db.commit()
        # Invoke the apply behavior by importing and calling register in script
        from scripts.hermes_cli_discovery_playwright import register_providers

        register_providers([])
        prov = db.query(CLIProvider).filter_by(name="deepseek_r1").first()
        assert prov is not None
        assert prov.base_url is not None and "deepseek" in prov.base_url
    finally:
        if orig is None:
            try:
                delattr(settings, "deepseek_base_url")
            except Exception:
                pass
        else:
            settings.deepseek_base_url = orig
        try:
            db.close()
        except Exception:
            pass
