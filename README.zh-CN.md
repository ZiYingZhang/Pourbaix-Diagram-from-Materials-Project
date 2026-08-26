# Pourbaix Studio R4

[English](README.md) | [简体中文](README.zh-CN.md)

Pourbaix Studio R4 是一款 Windows 科研桌面软件，用于从 Materials Project 获取数据，并利用 pymatgen 生成可直接用于论文绘图的 Pourbaix 图（pH–电位稳定图）。软件把体系组成设置、稳定区域显示、图形后处理和科研数据导出集成在同一界面中。

![Pourbaix Studio R4 的 TiO2 示例](tutorial/TiO2.png)

## 主要功能

- 可通过元素周期表选择或直接输入化学式，最多支持 4 种非 H/O 元素。
- 可自由设置元素比例和离子浓度；H 和 O 作为开放储库处理，不设置比例和浓度。
- 通过 Materials Project API 查询固相与水溶液离子数据。
- 分别设置计算使用和最终显示使用的 pH、电位范围（相对于 SHE）。
- 可选择任意稳定区域，并分别设置填充颜色和透明度。
- 修改可视化参数后可基于当前结果重新绘图，不会重复调用 API。
- 可设置物种标签、标签背景、坐标轴标题、字体、刻度数字、刻度方向、主刻度间隔、线条颜色与粗细、图片物理尺寸、DPI 和透明背景。
- 支持平移、缩放、视图复位，以及适合小屏幕的 Focus Plot 模式。
- 图片可导出为 PNG、SVG、TIFF；边界数据可导出为 CSV、XLSX、TXT。
- API key 可仅在本次运行中使用，也可安全保存到 Windows 凭据管理器。

## 下载与运行

1. 打开仓库的 [Releases 页面](https://github.com/ZiYingZhang/Pourbaix-Diagram-from-Materials-Project/releases)，下载 `PourbaixStudioR4-win64.zip`。
2. 将 ZIP 完整解压到新文件夹，不要直接在压缩包内运行程序。
3. 保持 `PourbaixStudioR4.exe` 与 `_internal` 文件夹位于同一目录，双击 EXE 启动。
4. 点击 **API Settings**，通过 [Materials Project API 页面](https://next-gen.materialsproject.org/api) 获取 API key，粘贴到密码框，然后选择 **Use for this session**（仅本次使用）或 **Remember and use**（保存并使用）。
5. 设置体系、组成、浓度、pH 范围和电位范围，然后点击 **Generate diagram**。

![Materials Project API key 设置窗口](tutorial/get%20API%20key%20first.png)

便携版不需要单独安装 Python，也不需要管理员权限。下载新计算数据时需要网络连接和有效的 Materials Project API key。

完整操作步骤请阅读[中文使用教程](USER_GUIDE.zh-CN.md)，英文用户可阅读 [English user guide](USER_GUIDE.md)。

## 从源代码运行

已验证的开发环境为 Windows x64 和 CPython 3.13。在项目根目录运行：

```powershell
python -m venv .venv-pourbaix-py313
.\.venv-pourbaix-py313\Scripts\python.exe -m pip install --no-cache-dir -r requirements-lock-py313-win64-r4.txt
.\.venv-pourbaix-py313\Scripts\python.exe pourbaix_studio_R4.py --self-test
.\.venv-pourbaix-py313\Scripts\python.exe pourbaix_studio_R4.py
```

VS Code 配置使用 `${workspaceFolder}` 相对路径，因此项目文件夹可以移动。移动后建议重新创建虚拟环境，因为 Python 虚拟环境中包含与当前电脑和路径相关的绝对地址。

## 构建 Windows 便携包

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_release_r4.ps1
```

发布脚本会运行 R4 完整测试、源码检查、PyInstaller 封装、封装版和解压版 GUI 检查、MPContribs 解析器检查、敏感文件扫描以及 SHA-256 计算。输出位于 `_release\R4.0`。

## 科学与安全说明

- pH 为无量纲量，电位单位为 V，相对于标准氢电极（SHE）。
- 热力学稳定区域由锁定版本的 mp-api 与 pymatgen 计算，具体版本见 `requirements-lock-py313-win64-r4.txt`。
- 仅修改显示参数不会改变已经计算的边界坐标。
- Materials Project 和 MPContribs 是外部在线服务；若服务或网络短暂中断，可稍后重新查询。
- 新输入的 API key 不会写入仓库或发布包；选择保存时，密钥只存放在当前 Windows 用户的凭据管理器中。

## 文档

- [中文使用教程](USER_GUIDE.zh-CN.md)
- [English user guide](USER_GUIDE.md)
- [中文 VS Code 运行教程](VS_CODE运行教程.md)
- [数值与科学约定](docs/numerical-contract.md)
- [验收清单](docs/acceptance-checklist.md)
- [第三方依赖说明](THIRD_PARTY_NOTICES.md)
- [版本记录](CHANGELOG.md)

## 致谢

本软件使用 [Materials Project](https://materialsproject.org/) 提供的数据和在线服务，并使用 [pymatgen](https://pymatgen.org/) 完成科学计算。将生成结果用于论文时，请按照 Materials Project 和 pymatgen 的要求进行引用。
