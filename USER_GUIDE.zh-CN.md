# Pourbaix Studio R4 — Windows 中文使用教程

[English](USER_GUIDE.md) | [简体中文](USER_GUIDE.zh-CN.md)

## 1. 下载与解压

1. 打开项目的 [Releases 页面](https://github.com/ZiYingZhang/Pourbaix-Diagram-from-Materials-Project/releases)。
2. 下载 `PourbaixStudioR4-win64.zip`。
3. 将 ZIP 完整解压到一个新文件夹。不要直接在压缩包内部运行程序。
4. 双击 `PourbaixStudioR4.exe`。必须保持 EXE 与 `_internal` 文件夹位于同一目录；移动软件时请移动整个 `PourbaixStudioR4` 文件夹。

便携版不要求用户另行安装 Python，也不需要管理员权限。

## 2. 设置 Materials Project API key

1. 点击顶部的 **API Settings**。
2. 点击 **Get a Materials Project API key**，或直接访问 <https://next-gen.materialsproject.org/api>。
3. 将 API key 粘贴到密码输入框。
4. 选择 **Use for this session** 表示仅在本次运行中使用；选择 **Remember and use** 表示保存到当前 Windows 用户的凭据管理器并立即使用。
5. **Forget saved key** 会删除已保存的密钥。

![API key 设置窗口](tutorial/get%20API%20key%20first.png)

软件不会把新输入的 API key 写入项目文件或发布压缩包。请勿在公开分享的文件夹中保存 `mp_api_key.txt`。

## 3. 设置化学体系

- 可以直接输入化学式，例如 `TiO2`；也可以点击 **Choose elements**，通过元素周期表选择最多 4 种非 H/O 元素。
- H 和 O 被视为开放储库，不需要设置元素比例或离子浓度。
- 多元素体系可以在 **Composition control** 中设置比例，例如查询 `Sb2Se3` 时设为 `Sb : Se = 2 : 3`。
- 输入发生变化后，需要重新点击 **Generate diagram** 才会生成对应的新热力学结果。

## 4. 高级查询条件

勾选 **Enable advanced options** 后，可以设置：

- **Filter solids**：是否过滤固相；
- **Ion concentrations (M)**：各闭合元素离子的浓度，单位为 mol/L；
- **Diagram range**：计算使用的 pH 与电位范围。

pH 最小值必须小于最大值，电位最小值也必须小于最大值。元素比例和浓度会改变计算结果，修改后必须重新查询。

## 5. 生成和查看结果

点击 **Generate diagram** 后，软件从 Materials Project 获取所需数据并生成结果。中间区域包含三个标签页：

- **Diagram**：Pourbaix 图；
- **Available regions**：当前计算得到的可选稳定区域；
- **Boundary data**：各区域边界顶点的 pH 与电位坐标。

![TiO2 结果与后处理界面](tutorial/TiO2.png)

图形上方工具栏可用于复位、前进/后退、平移、框选缩放、子图调整、图形设置和保存。小屏幕上可点击 **Focus Plot** 暂时隐藏左右边栏。

## 6. 选择填充区域

1. 在右侧 **REGIONS AND FILLS** 中选择感兴趣的区域。
2. 点击 **Add** 添加该区域。
3. 在列表中选中区域，设置 **Selected fill** 颜色和 **Opacity** 透明度。
4. 点击 **Apply to selected region** 应用样式。
5. 可以添加多个区域，并分别设置颜色、透明度和是否显示。

填充对象不限于单一固相，列表显示的任何稳定区域或混合区域都可以选择。

## 7. 图形后处理

右侧功能区可设置：

- 物种标签是否显示、字体、大小、背景色与背景透明度；
- X/Y 坐标轴标题、标题字体和标题大小；
- 刻度是否显示、方向、长度、宽度、主刻度间隔和次刻度；
- 刻度数字的字体和大小；
- 稳定区域边界线和 H/O 水稳定线的颜色、线型与粗细；
- 最终显示的 pH、电位范围；
- 图形的物理宽度、高度和单位；
- 导出 DPI 与透明背景。

修改显示参数后，点击 **Re-plot current result**。此操作基于当前计算结果重新绘图，不会再次访问 Materials Project。只有改变元素、比例、浓度或计算范围时，才需要重新点击 **Generate diagram**。

## 8. 导出图片和数据

- **Export Figure**：导出 PNG、SVG 或 TIFF。PNG/TIFF 使用设置的 DPI，可选择透明背景。
- **Export Data**：导出 CSV、XLSX 或 TXT，内容为稳定区域边界顶点数据。

导出前必须存在当前有效的计算结果。如果修改了查询条件，应先重新生成图形，避免把旧结果以新组成名称导出。

## 9. 故障诊断

- 查询失败时点击 **Diagnostics**，查看失败阶段、类别和详细信息；诊断内容不会显示 API key。
- 如果提示认证失败，请重新打开 **API Settings** 并检查密钥。
- 如果提示网络或 MPContribs 错误，请确认网络连接，稍后重试；Materials Project 属于外部在线服务。
- 如果 EXE 无法运行，确认程序不在 ZIP 内部，并且 `_internal` 文件夹没有丢失。
- 更新版本时，请解压到全新文件夹，不要直接覆盖旧版目录。

可在 PowerShell 中运行以下命令检查封装依赖：

```powershell
.\PourbaixStudioR4.exe --self-test
```

还可使用 `--gui-smoke` 和 `--mpcontribs-smoke` 分别检查 GUI 与 MPContribs 运行资源。

## 10. 从 VS Code 运行源代码

详细步骤请参阅[中文 VS Code 运行教程](VS_CODE运行教程.md)。项目使用相对路径配置；移动项目后应重新创建 `.venv-pourbaix-py313` 虚拟环境。
