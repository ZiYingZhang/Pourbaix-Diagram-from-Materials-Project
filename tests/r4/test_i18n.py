import pytest
from PySide6.QtCore import QSettings

from pourbaix_r4.i18n import PreferenceStore, TranslationCatalog, TranslationError


def test_bilingual_catalog_has_matching_key_sets_and_translates_ui_text():
    catalog = TranslationCatalog()

    assert catalog.keys("en") == catalog.keys("zh_CN")
    assert catalog.text("generate", "en") == "Generate diagram"
    assert catalog.text("generate", "zh_CN") == "生成图"
    assert catalog.text("api_key_required", "zh_CN") == "请先输入 Materials Project API 密钥。"


def test_catalog_rejects_unknown_keys_and_languages():
    catalog = TranslationCatalog()

    with pytest.raises(TranslationError, match="Unknown translation key"):
        catalog.text("missing", "en")
    with pytest.raises(TranslationError, match="Unsupported language"):
        catalog.text("generate", "de")


def test_preference_store_persists_only_non_secret_language(tmp_path):
    settings = QSettings(str(tmp_path / "preferences.ini"), QSettings.Format.IniFormat)
    store = PreferenceStore(settings)

    assert store.language() == "en"
    store.set_language("zh_CN")

    reloaded = PreferenceStore(QSettings(str(tmp_path / "preferences.ini"), QSettings.Format.IniFormat))
    assert reloaded.language() == "zh_CN"
    assert "api" not in " ".join(reloaded.settings.allKeys()).lower()
