# Pourbaix Studio R4：使用 VS Code 从源码运行（Windows 中文教程）

本教程适用于以下项目目录：

```text
E:\Research Library\Data\materials project\r4-foundation
```

> 重要：本机命令行中的默认 `python` 是 Python 3.10，不能用于当前 R4 环境。R4 已验证的版本是 Python 3.13.15，因此请使用下面给出的完整 Python 3.13 路径。

## 一、第一次用 VS Code 打开项目

1. 启动 VS Code。
2. 点击菜单 **File → Open Folder...（文件 → 打开文件夹）**。
3. 选择：

   ```text
   E:\Research Library\Data\materials project\r4-foundation
   ```

4. 点击 **Select Folder（选择文件夹）**。
5. 如果 VS Code 询问是否信任此文件夹，确认这是自己的项目后选择信任。
6. 确认左侧文件列表中可以看到：

   ```text
   pourbaix_studio_R4.py
   pourbaix_r4
   requirements-lock-py313-win64-r4.txt
   tests
   ```

建议安装微软官方的 **Python** 扩展。打开扩展面板，搜索 `Python`，发布者应为 Microsoft。

## 二、打开 VS Code 终端

点击菜单 **Terminal → New Terminal（终端 → 新建终端）**。

终端提示符所在目录应为：

```text
PS E:\Research Library\Data\materials project\r4-foundation>
```

如果不是该目录，在终端执行：

```powershell
Set-Location -LiteralPath "E:\Research Library\Data\materials project\r4-foundation"
```

## 三、第一次创建 Python 3.13 虚拟环境

移动源码目录后不要复制旧虚拟环境，应在新目录重新创建。

在 VS Code 终端执行：

```powershell
& "C:\Users\hp\AppData\Local\Python\pythoncore-3.13-64\python.exe" -m venv .venv-pourbaix-py313
```

创建完成后，项目根目录中会出现：

```text
.venv-pourbaix-py313
```

检查虚拟环境的 Python 版本：

```powershell
.\.venv-pourbaix-py313\Scripts\python.exe --version
```

预期显示：

```text
Python 3.13.15
```

## 四、安装 R4 所需依赖

继续在项目根目录执行：

```powershell
.\.venv-pourbaix-py313\Scripts\python.exe -m pip install --no-cache-dir -r requirements-lock-py313-win64-r4.txt
```

第一次安装需要联网，科学计算、Qt 和 Materials Project 依赖较多，可能需要几分钟。不要在安装尚未结束时关闭终端。

安装完成后，可以检查关键依赖：

```powershell
.\.venv-pourbaix-py313\Scripts\python.exe -c "import PySide6, pymatgen, mp_api; print('Dependencies: OK')"
```

预期显示：

```text
Dependencies: OK
```

## 五、让 VS Code 选择正确解释器

项目的 `.vscode/settings.json` 已经使用相对路径指向：

```text
${workspaceFolder}\.venv-pourbaix-py313\Scripts\python.exe
```

如果 VS Code 没有自动识别：

1. 按 `Ctrl+Shift+P`。
2. 输入并选择 **Python: Select Interpreter**。
3. 选择项目中的：

   ```text
   .venv-pourbaix-py313\Scripts\python.exe
   ```

4. 如果列表中没有，选择 **Enter interpreter path...**，再定位到上述文件。
5. 必要时按 `Ctrl+Shift+P`，运行 **Developer: Reload Window**。

不要选择 Python 3.10 或旧项目目录里的虚拟环境。

## 六、先执行自检

在启动图形界面前运行：

```powershell
.\.venv-pourbaix-py313\Scripts\python.exe pourbaix_studio_R4.py --self-test
```

正常结果为：

```text
R4 self-test: OK
```

还可以运行一次不会访问 Materials Project 的 GUI 冒烟测试：

```powershell
.\.venv-pourbaix-py313\Scripts\python.exe pourbaix_studio_R4.py --gui-smoke
```

正常结果为：

```text
R4 GUI smoke: OK
```

## 七、正式启动 Pourbaix Studio R4

执行：

```powershell
.\.venv-pourbaix-py313\Scripts\python.exe pourbaix_studio_R4.py
```

出现 **Pourbaix Studio R4** 窗口即表示源码启动成功。启动后请保留终端窗口；关闭软件窗口后，命令会结束并返回 PowerShell 提示符。

## 八、第一次查询的建议步骤

1. 点击顶部 **API Settings**。
2. 通过 Materials Project 链接获取自己的 API Key。
3. 不要把 API Key 写入源码、教程、截图、Git 或普通文本文件。
4. 关闭 API 设置后，在左侧输入或选择元素。
5. 设置比例、浓度、pH 范围和电位范围。
6. 点击 **Generate diagram**。

当前开发版本已经记录一个待修复缺陷：API Key 需要支持“仅本次会话使用”、保存后立即生效，并在失败时显示安全且明确的诊断原因。在该修复完成前，如果只看到 `Calculation failed. See diagnostics for details.`，不要反复输入或公开 API Key，应先更新到修复后的版本。

## 九、以后再次运行

虚拟环境和依赖已经创建后，再次打开项目只需要：

```powershell
Set-Location -LiteralPath "E:\Research Library\Data\materials project\r4-foundation"
.\.venv-pourbaix-py313\Scripts\python.exe pourbaix_studio_R4.py
```

通常不需要重复创建虚拟环境，也不需要重复安装依赖。只有删除、移动虚拟环境，或者依赖锁文件发生变化时才需要重新安装。

## 十、不使用 VS Code，直接运行封装版

如果只想运行软件，不准备修改源码，可以直接双击：

```text
E:\Research Library\Data\materials project\r4-foundation\_release\R4.0\PourbaixStudioR4\PourbaixStudioR4.exe
```

封装版不需要 `.venv-pourbaix-py313`，但必须保持 `PourbaixStudioR4.exe` 与 `_internal` 文件夹在一起。

## 十一、常见问题

### 1. `ModuleNotFoundError: No module named 'PySide6'`

原因通常是使用了错误的 Python。请使用：

```powershell
.\.venv-pourbaix-py313\Scripts\python.exe pourbaix_studio_R4.py
```

不要直接执行：

```powershell
python pourbaix_studio_R4.py
```

### 2. VS Code 显示找不到解释器

先确认下面的文件存在：

```text
.venv-pourbaix-py313\Scripts\python.exe
```

如果不存在，重新执行本教程第三、四部分。

### 3. `py -3.13` 提示 Python 3.13 未安装

本机的 Python Launcher 当前没有登记 Python 3.13。请使用本教程提供的完整路径创建环境：

```powershell
& "C:\Users\hp\AppData\Local\Python\pythoncore-3.13-64\python.exe" -m venv .venv-pourbaix-py313
```

### 4. 移动项目后不能运行

源码目录可以移动，但移动后应重新创建 `.venv-pourbaix-py313`。不要复制旧虚拟环境。项目内其他运行路径已采用相对路径。

### 5. 查询失败但没有具体原因

这是已经记录的 API Key/诊断缺陷，不代表 Ti 或其他体系一定计算错误。更新到修复版本后再测试；不要在聊天、日志或截图中公开 Key。
