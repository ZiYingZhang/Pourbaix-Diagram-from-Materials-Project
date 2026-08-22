"""Runtime English/Chinese text and non-secret Qt preferences."""

from __future__ import annotations

from typing import Literal

from PySide6.QtCore import QSettings


Language = Literal["en", "zh_CN"]


class TranslationError(ValueError):
    pass


_EN = {
    "system_conditions": "System and conditions", "formula": "Chemical formula", "elements": "Elements",
    "ratios": "Ratios", "ph_range": "pH range", "potential_range": "Potential range",
    "generate": "Generate diagram", "diagram": "Diagram", "available_regions": "Available regions",
    "boundary_data": "Boundary data", "interest_regions": "Interest regions", "add_interest_region": "Add interest region",
    "appearance": "Appearance", "api_settings": "API settings", "export_data": "Export data",
    "export_figure": "Export figure", "diagnostics": "Diagnostics", "clear_cache": "Clear cache",
    "language": "Language", "show_ion_labels": "Show ion labels", "label_background": "Label background",
    "axis_ticks": "Axes and ticks", "water_lines": "Water stability lines", "image_export": "Image export",
    "api_key_required": "Enter a Materials Project API key before querying.",
    "calculation_failed": "Calculation failed. Review the highlighted fields or diagnostics.",
    "export_complete": "Export completed.", "remember_key": "Remember on this computer", "forget_key": "Forget saved key",
}
_ZH = {
    "system_conditions": "体系与条件", "formula": "化学式", "elements": "元素", "ratios": "比例",
    "ph_range": "pH 范围", "potential_range": "电位范围", "generate": "生成图", "diagram": "图",
    "available_regions": "可用区域", "boundary_data": "边界数据", "interest_regions": "关注区域",
    "add_interest_region": "添加关注区域", "appearance": "外观", "api_settings": "API 设置",
    "export_data": "导出数据", "export_figure": "导出图片", "diagnostics": "诊断", "clear_cache": "清除缓存",
    "language": "语言", "show_ion_labels": "显示离子标签", "label_background": "标签背景",
    "axis_ticks": "坐标轴与刻度", "water_lines": "水稳定线", "image_export": "图片导出",
    "api_key_required": "请先输入 Materials Project API 密钥。", "calculation_failed": "计算失败。请检查高亮字段或诊断信息。",
    "export_complete": "导出完成。", "remember_key": "在此电脑上记住", "forget_key": "忘记已保存密钥",
}


class TranslationCatalog:
    def _table(self, language: str) -> dict[str, str]:
        if language == "en": return _EN
        if language == "zh_CN": return _ZH
        raise TranslationError(f"Unsupported language: {language}")

    def keys(self, language: Language) -> set[str]:
        return set(self._table(language))

    def text(self, key: str, language: Language, **values: object) -> str:
        table = self._table(language)
        if key not in table: raise TranslationError(f"Unknown translation key: {key}")
        return table[key].format(**values)


class PreferenceStore:
    """Store only UI preferences; credentials always use the credential layer."""
    def __init__(self, settings: QSettings | None = None):
        self.settings = settings or QSettings("PourbaixStudio", "R4")

    def language(self) -> Language:
        value = self.settings.value("ui/language", "en")
        return value if value in {"en", "zh_CN"} else "en"

    def set_language(self, language: Language) -> None:
        if language not in {"en", "zh_CN"}: raise TranslationError(f"Unsupported language: {language}")
        self.settings.setValue("ui/language", language)
        self.settings.sync()
