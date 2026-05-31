---
name: mumu_adb_control
description: 通过 ADB 控制 MuMu 模拟器，支持截图、点击、滑动、文字输入、按键事件及获取前台应用信息等操作。
version: 1.0.0
triggers:
  - "模拟器"
  - "mumu"
  - "刷"
  - "点击"
  - "截图"
  - "滑动"
  - "输入文字"
  - "按键"
tools:
  - bash
  - read
  - write
---

# MuMu 模拟器 ADB 控制技能

## 概述

本技能封装了对 **MuMu 模拟器** 的 ADB 控制能力，提供 `MumuAdbClient` 类，用于自动化流程中执行屏幕交互操作。支持自动发现运行中的模拟器、截图、点击、滑动、文本输入、按键事件以及获取前台应用信息。

## 适用场景

- 自动化操作 MuMu 模拟器内的 App（如游戏、社交媒体、测试工具）
- 获取模拟器屏幕内容并进行图像识别
- 模拟用户点击、滑动、文字输入等行为

## 依赖环境

- 已安装 **ADB**（Android Debug Bridge），并确保 `adb` 命令可在命令行中直接调用
- 已安装 **MuMu 模拟器**（12 及以上版本），并至少启动一个模拟器实例
- Python 3.7+
- 配置文件 `config.py` 需包含以下变量（可选，脚本包含默认值）：
  - `MUMU_MANAGER_PATH`：MuMuManager.exe 的完整路径（默认自动探测常见安装路径）
  - `SCREENSHOT_DIR`：截图保存目录（未指定保存路径时自动使用）

## 使用步骤

### 1. 引入客户端类

```python
from mumu_adb_clint import MumuAdbClient
```

### 2. 创建客户端实例

```python
# 方式一：自动检测并连接正在运行的模拟器（推荐）
client = MumuAdbClient()

# 方式二：手动指定 ADB 连接串（如 "127.0.0.1:16384"）
client = MumuAdbClient(serial="127.0.0.1:16384")
```
- 如果只有一个模拟器在运行，会自动选择。
- 如果有多个模拟器运行，会列出所有可用实例，等待用户输入序号选择。

### 3. 执行操作

客户端实例化后即可调用以下方法。

## 可用方法详解

| 方法 | 说明 | 参数 | 返回值 |
|------|------|------|--------|
| `screencap(save_path=None)` | 截取当前屏幕并保存为 PNG 文件 | `save_path` (str, 可选) - 保存路径，不含则自动生成在 `SCREENSHOT_DIR` | 无（文件保存至磁盘） |
| `tap(x, y)` | 点击屏幕指定坐标 | `x` (int), `y` (int) | 无 |
| `swipe(x1, y1, x2, y2, duration_ms=300)` | 从起点滑动到终点 | `x1,y1` 起点；`x2,y2` 终点；`duration_ms` 滑动耗时（毫秒） | 无 |
| `input_text(text)` | 在当前焦点输入框输入文字 | `text` (str) - 要输入的文本 | 无 |
| `keyevent(key)` | 发送按键事件 | `key` (str) - 按键代码或名称，如 `"KEYCODE_HOME"`, `"HOME"`, `"3"`, `"26"`（电源键） | 无 |
| `get_foreground_app()` | 获取当前前台应用信息 | 无 | `(package_name, activity_name)` 元组，如 `("com.android.settings", ".Settings")` |
| `is_available()` | 检查设备是否在线且响应 | 无 | `bool` - True 表示正常 |

## 使用示例

### 示例 1：截图并保存到指定路径



```python
client = MumuAdbClient()
client.screencap("D:/my_screenshots/test.png")
```

### 示例 2：点击坐标 (500, 1000)

```python
client.tap(500, 1000)
```

### 示例 3：从 (200, 800) 滑动到 (200, 300)，耗时 500 毫秒

```python
client.swipe(200, 800, 200, 300, 500)
```

### 示例 4：输入文本（自动转义特殊字符）

```python
client.input_text("Hello, 世界!")
```

### 示例 5：发送 Home 按键

```python
client.keyevent("HOME")
```

### 示例 6：获取当前打开的应用包名

```python
pkg, act = client.get_foreground_app()
print(f"当前应用: {pkg}, Activity: {act}")
```

### 示例 7：组合操作 – 打开应用、点击、滑动、截图

```python
# 假设已知某应用的启动 Activity
client.keyevent("HOME")                     # 返回桌面
client.tap(100, 200)                        # 点击桌面图标（坐标需实测）
time.sleep(2)
client.swipe(300, 1000, 300, 500, 300)      # 向上滑动
client.screencap("result.png")
```

## 注意事项

1. **模拟器必须处于运行状态**：如果未检测到运行中的模拟器，`MumuAdbClient()` 会抛出异常。
2. **ADB 连接**：首次连接时脚本会自动执行 `adb connect`，确保 ADB 服务已启动（可手动运行 `adb start-server`）。
3. **坐标系统**：屏幕坐标原点 (0,0) 为左上角，向右 x 增加，向下 y 增加。可通过截图查看分辨率。
4. **截图目录权限**：如果config.py 配置了保存的文件夹则直接调用不需要参数以配置的为准，如果指定自定义保存路径，请确保父目录存在且可写；使用自动路径时需确保 `config.SCREENSHOT_DIR` 存在或脚本能自动创建。
5. **文本输入**：仅适用于当前焦点在可输入控件（如输入框）。若需要输入中文，请确保模拟器输入法支持 ADB 输入（通常 Android 原生支持）。
6. **按键代码参考**：常用按键包括 `KEYCODE_HOME`（主页）、`KEYCODE_BACK`（返回）、`KEYCODE_APP_SWITCH`（多任务）、`KEYCODE_ENTER`（回车）等。数字键 `3` 代表 Home，`4` 代表返回。
7. **截图以后不要主动去分析截图页面**：后续会有其他技能去对截图解析，

## 常见问题

**Q: 提示“未找到 MuMuManager.exe”**  
A: 请检查 MuMu 模拟器是否正确安装。可将 `MUMU_MANAGER_PATH` 在 `config.py` 中手动设置为正确路径。

**Q: 提示“设备状态异常”或连接失败**  
A: 尝试手动执行 `adb kill-server` 然后 `adb start-server`，重启模拟器，或检查防火墙是否阻止了 ADB 端口（一般为 16384、16385 等）。

**Q: 截图返回空数据或黑屏**  
A: 确保模拟器屏幕已亮起（未锁屏），且当前应用允许截屏（部分银行/支付类应用会屏蔽）。

**Q: 多模拟器环境下如何选择非交互模式？**  
A: 可在创建客户端前通过 `client._get_running_emulators()` 获取列表，然后手动设置 `serial`。或者修改 `_auto_select_emulator` 方法实现自动策略（如始终选第一个）。本技能默认提供交互选择。

## 技能文件结构

本技能所需脚本均位于 `scripts/` 文件夹中：

```
scripts/
├── config.py            # 配置文件（路径等）
├── mumu_adb_clint.py    # MumuAdbClient 类实现
├── example.py           # 简单使用示例
└── SKILL.md             # 本技能文档
```

调用时请确保将 `scripts` 目录加入 Python 路径，或直接在同级目录下运行。

## 扩展建议

- 可将 `get_foreground_app()` 与条件判断结合，实现针对不同 App 的差异化操作。
- 结合图像识别库（如 OpenCV、PIL）对截图进行分析，动态计算点击坐标。
- 封装更高层的方法，如 `wait_for_element(image_path, timeout)` 等待特定 UI 出现。

---

> 本技能设计为 OpenClaw 可调用的原子能力，使用时请保持 ADB 环境稳定，并在每次操作前确保模拟器处于活跃状态。
```

---

**优化说明**：
- 增加了完整的 **方法表格**、**参数说明**、**返回值**，方便 AI 快速查阅。
- 提供了 **多个实际场景示例**，展示从初始化到组合操作的完整流程。
- 补充了 **注意事项** 和 **常见问题**，减少 AI 误用风险。
- 明确了 **技能文件结构** 和 **调用方式**，符合 OpenClaw 技能规范。
- 语言简洁、结构化，便于大语言模型解析和生成正确代码。