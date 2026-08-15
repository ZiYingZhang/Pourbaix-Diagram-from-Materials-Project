# Pourbaix-Diagram-from-Materials-Project

Pourbaix GUI R2 — PyQt5 desktop app to generate Pourbaix (pH–potential) diagrams using Materials Project via pymatgen. Interactive UI for multi‑element systems, tunable plot styling, and export of images and boundary data. The packaged Windows build includes the frozen executable and runtime files so non‑Python users can run the tool directly.

## Key features

- Interactive GUI for building Pourbaix diagrams (elements, ratios, pH/potential ranges)
- Export diagram images (PNG / JPEG / TIFF / SVG) and boundary data (CSV / XLSX / TXT)
- Robust handling of API fetches with local caching and sanitized ion records

## Quick start

1. Download and extract `pourbaix_gui_R2-win64.zip`.
2. Launch `pourbaix_gui_R2.exe` and paste your Materials Project API key into the API Key field.
3. Enter elements (comma separated) and ratios, set pH/potential ranges, then click “Generate Pourbaix Diagram”.
4. Use “Export Data” or “Export Figure Image” to save outputs to a writable folder (Documents/Desktop recommended).

## Notes

- The app requires internet access and a valid Materials Project API key. Do not distribute API keys with the package.
- If export fails, choose a user-writable folder (Documents or Desktop) and send `pourbaix_gui_R2_runtime.log` for debugging.

---

This README is plain Markdown suitable for Markwon and other Markdown renderers.

# Pourbaix GUI R2 (标准在线模式 / Option B 已实施)

当前版本：R2.8

新增 (R2.5 → R2.8) 关键改进：
- R2.5-R2.6: 明确 Qt 后端收集，解决打包后 backend_qt5agg 丢失问题。
- R2.7: 图像导出（PNG / JPG / TIFF / SVG）。
- R2.8: 
	* 图像导出支持自定义 DPI (50–1200) 与透明背景选项。
	* 在线获取结果缓存（默认 5 分钟）减少重复访问 API。
	* Diagnostics 诊断窗口：查看后端、版本、最近条目数、耗时、是否触发 sanitation 重试、缓存条目数。
	* 一键清空缓存按钮。
	* 结构化内部指标（便于后续加进度条或远程日志）。

仍保留：
- 自动数据清洗：缺失 MajElements / RefSolid 的离子记录自动补全并重试。
- 仅在线模式（不再内置离线 / 合成数据）。

## 使用步骤
1. 激活虚拟环境：
```bat
cd /d "E:\Research Library\Data\materials project\pourbaix diagram"
pourbaix_env\Scripts\activate.bat
```
2.（推荐）固定已验证可用的 mp-api 版本（示例 0.44.0，可根据需要调整）：
```bat
pip uninstall -y mp-api
pip install "mp-api==0.44.0" mpcontribs-client
```
3. 运行脚本测试（开发态）：
```bat
python pourbaix_gui_R2.py
```
4. 打包（使用现有 spec）：
```bat
rmdir /s /q build
rmdir /s /q dist
pyinstaller pourbaix_gui_R2.spec
```
5. 分发 dist\pourbaix_gui_R2 目录中的 exe 与依赖文件。

# Pourbaix GUI R2 (在线模式)

当前版本：R2.8

本项目为基于 PyQt5 的桌面工具，用于调用 Materials Project（通过 mp-api 和 pymatgen）生成 Pourbaix（pH–电位）相图。提供交互式界面、图像与数据导出，以及运行时日志帮助诊断问题。

## 主要更新（R2.5 → R2.8）

- R2.5–R2.6：改进 Qt 后端选择，解决打包后后端缺失的问题。
- R2.7：支持图像导出（PNG/JPG/TIFF/SVG）。
- R2.8：
	- 图像导出支持自定义 DPI（50–1200）与透明背景选项。
	- 在线数据结果缓存（默认 5 分钟），减少重复请求。
	- Diagnostics 窗口：查看后端、版本、最近条目数、耗时、是否触发 sanitation 重试、缓存条目数。
	- 一键清空缓存按钮与结构化内部指标。

## 使用快速指南（开发 / 打包）

1. 激活虚拟环境（开发）：

```bat
cd /d "E:\Research Library\Data\materials project\pourbaix diagram"
pourbaix_env\Scripts\activate.bat
```

2. 推荐固定 mp-api 版本以保证可重复性（示例）：

```bat
pip uninstall -y mp-api
pip install "mp-api==0.44.0" mpcontribs-client
```

3. 开发时运行：

```bat
python pourbaix_gui_R2.py
```

4. 使用 PyInstaller 打包（示例）：

```bat
rmdir /s /q build
rmdir /s /q dist
pyinstaller pourbaix_gui_R2.spec
```

5. 分发：将 `dist\pourbaix_gui_R2` 中的可执行文件和 `_internal` 目录一起分发，或使用生成的 ZIP。

## 常见问题与对策

- API 返回 0 entries：检查网络连通性与 API Key；尝试常见体系（如 Ti-O、Fe-O）；如需离线展示，可恢复旧的离线逻辑模块。
- KeyError: MajElements / RefSolid：已经实现自动修补与重试；若仍报错，尝试更换 mp-api 版本。
- 401 Unauthorized：请确认使用当前有效的 Materials Project API Key。

如果导出失败，请先尝试将文件保存到 `Documents` 或 `Desktop`（用户可写目录），并把 `pourbaix_gui_R2_runtime.log` 的最后 200 行一并提供以便诊断。

## 运行时日志

- `pourbaix_gui_R2_runtime.log`：主运行日志，位于应用同一目录。
- `pourbaix_gui_R2.log`：兼容旧命名。

Diagnostics 窗口会显示当前 matplotlib backend、mp-api/pymatgen 版本、缓存与最近获取情况。

## 精简打包建议

- 不需要 Excel 导出时可移除 `openpyxl`。
- 如可接受较粗糙的多边形裁剪，可移除 `shapely` 以减小体积。

## 建议的 requirements（示例）

```
mp-api==0.44.0
mpcontribs-client
pymatgen
PyQt5
matplotlib
shapely
pandas
openpyxl
```

安装：

```bat
pip install -r requirements.txt
```

## 后续可选改进

1. 异步请求与进度指示（避免 GUI 卡顿）。
2. 本地持久化磁盘缓存以跨会话复用数据。
3. 输入实时校验与自动大写元素符号。
4. 批量生成与自动导出功能。
5. 增加 CLI 支持以便无 GUI 批量处理。

---

如需恢复离线模式、调整缓存策略或自动导出图片，请在对话中说明。

