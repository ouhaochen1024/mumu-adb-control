# skill.md — MuMu 模拟器 ADB 控制技能

## 概述
本技能封装了对 **MuMu 模拟器** 的 ADB 控制能力，支持自动发现正在运行的模拟器、执行截图、点击、滑动、文字输入、按键事件以及获取前台应用信息等操作。适用于 OpenClaw 等自动化流程中需要对模拟器进行 UI 交互的场景。

## 依赖环境
- 已安装 **ADB** (Android Debug Bridge)，并可在命令行中直接调用 `adb`。
- 已安装 **MuMu 模拟器**（12 及以上版本），且 MuMuManager.exe 可访问（默认路径参见配置）。
- Python 3.7+，需要 `config` 模块提供以下配置项：
  - `MUMU_MANAGER_PATH`：MuMuManager.exe 的完整路径（可选，代码会尝试默认路径）。
  - `SCREENSHOT_DIR`：截图保存目录（仅在未指定保存路径时使用）。

## 技能名
`mumu_adb_control`

## 初始化
具体代码在 scripts/ 文件夹
在调用具体方法前，需创建 `MumuAdbClient` 实例。该过程会自动完成设备连接与状态检测。

```python
from mumu_adb_clint import MumuAdbClient

# 自动检测并连接运行中的 MuMu 模拟器（推荐）
client = MumuAdbClient()

# 或手动指定 ADB 序列号（如 "127.0.0.1:16384"）
client = MumuAdbClient(serial="127.0.0.1:16384")
# 如果只有一个模拟器可以不指定 如下
client = MumuAdbClient()

# 初始化后可以调用一些方法
client.screencap()
