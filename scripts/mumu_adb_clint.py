import subprocess
import time
import json
import os
from typing import List, Dict, Optional, Tuple

import config


class MumuAdbClient:
    def __init__(self, serial: Optional[str] = None):
        """
        :param serial: ADB 设备序列号（如 "127.0.0.1:16384"）。若为 None，则自动检测运行中的 MuMu 模拟器。
        """
        self.serial = serial
        if self.serial is None:
            self.serial = self._auto_select_emulator()
        self._ensure_connected()

    # ----------------------------------------------------------------------
    # 私有辅助方法
    # ----------------------------------------------------------------------
    def _adb_cmd(self, args: List[str], check: bool = True, timeout: int = 30) -> subprocess.CompletedProcess:
        """
        执行一条针对当前设备的 ADB 命令。
        :param args: adb 子命令参数列表（不含 "adb" 和 "-s serial"）
        :param check: 是否检查返回码，为 True 且命令失败时抛出异常
        :param timeout: 超时秒数
        :return: CompletedProcess 对象
        """
        full_args = ["adb", "-s", self.serial] + args
        result = subprocess.run(full_args, capture_output=True, text=True, timeout=timeout)
        if check and result.returncode != 0:
            raise RuntimeError(f"ADB 命令失败: {' '.join(full_args)}\n错误: {result.stderr.strip()}")
        return result

    @staticmethod
    def _get_mumu_manager_path() -> str:
        """返回 MuMuManager.exe 的绝对路径，若找不到则抛出异常"""
        common_paths = [
            config.MUMU_MANAGER_PATH,
            r"C:\Program Files\Netease\MuMu\nx_main\MuMuManager.exe",
            r"C:\Program Files (x86)\Netease\MuMu\nx_main\MuMuManager.exe",
        ]
        for path in common_paths:
            if os.path.isfile(path):
                return path
        raise FileNotFoundError("未找到 MuMuManager.exe，请确认 MuMu 模拟器已安装")

    def _get_running_emulators(self) -> List[Dict]:
        """调用 MuMuManager 获取所有运行中的模拟器信息"""
        manager_path = self._get_mumu_manager_path()
        try:
            result = subprocess.run(
                [manager_path, "info", "-v", "all"],
                capture_output=True,
                text=True,
                check=True,
                encoding='utf-8',
                timeout=10
            )
            data = json.loads(result.stdout)
        except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            raise RuntimeError(f"获取模拟器信息失败: {e}")

        running = []
        for idx, info in data.items():
            if info.get("is_android_started") == True:
                ip = info.get("adb_host_ip", "127.0.0.1")
                port = info.get("adb_port")
                if port is None:
                    continue
                running.append({
                    "index": idx,
                    "name": info.get("name", f"模拟器-{idx}"),
                    "adb_connect": f"{ip}:{port}",
                    "adb_port": port
                })
        return running

    def _auto_select_emulator(self) -> str:
        """自动检测并选择模拟器，返回 ADB 连接串"""
        emulators = self._get_running_emulators()
        count = len(emulators)

        if count == 0:
            raise RuntimeError("未检测到任何运行中的 MuMu 模拟器，请先启动模拟器")

        if count == 1:
            print(f"检测到唯一运行中的模拟器: {emulators[0]['name']} (端口 {emulators[0]['adb_port']})，自动连接")
            return emulators[0]["adb_connect"]

        print("检测到多个运行中的模拟器：")
        for i, emu in enumerate(emulators):
            print(f"  [{i}] {emu['name']} - ADB 端口 {emu['adb_port']}")

        while True:
            try:
                choice = input("请选择要连接的模拟器序号: ").strip()
                idx = int(choice)
                if 0 <= idx < count:
                    selected = emulators[idx]
                    print(f"已选择: {selected['name']} (端口 {selected['adb_port']})")
                    return selected["adb_connect"]
                else:
                    print(f"请输入 0 ~ {count-1} 之间的数字")
            except ValueError:
                print("请输入有效数字")

    def _ensure_connected(self):
        """确保 ADB 已连接到指定设备且状态为 device"""
        if not self.serial:
            raise ValueError("未设置 ADB 序列号")

        # 解析 adb devices 输出，检查设备状态
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=5)
        lines = result.stdout.strip().split('\n')[1:]  # 跳过 "List of devices attached"
        for line in lines:
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 2 and parts[0] == self.serial:
                status = parts[1]
                if status == "device":
                    print(f"设备 {self.serial} 已在线且状态正常")
                    return
                else:
                    # 状态异常，尝试断开后重连
                    print(f"设备 {self.serial} 状态异常 ({status})，尝试重新连接")
                    subprocess.run(["adb", "disconnect", self.serial], capture_output=True, timeout=5)
                    break  # 跳出循环，进入连接逻辑

        # 未找到或状态异常，执行连接
        print(f"正在连接 {self.serial} ...")
        conn_result = subprocess.run(["adb", "connect", self.serial], capture_output=True, text=True, timeout=5)
        if conn_result.returncode != 0 or "unable to connect" in conn_result.stderr.lower():
            raise ConnectionError(f"无法连接到 {self.serial}：{conn_result.stderr.strip()}")

        time.sleep(1)  # 等待连接稳定

        # 最终验证
        verify = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=5)
        if self.serial not in verify.stdout or "device" not in verify.stdout:
            raise ConnectionError(f"连接 {self.serial} 后设备未就绪")
        print(f"连接 {self.serial} 成功")

    # ----------------------------------------------------------------------
    # 公开操作方法
    # ----------------------------------------------------------------------
    def screencap(self, save_path: Optional[str] = None):
        """
        截取屏幕帧缓冲，保存为 PNG 文件。
        ⚠️ 使用 exec-out 直接获取原始 PNG 数据，不会在设备上产生临时文件。
        :param save_path: 本地保存路径（应包含 .png 后缀）
        """
        # 使用 exec-out screencap -p 从 stdout 读取 PNG 数据
        if save_path is None:
            # 确保截图目录存在
            os.makedirs(config.SCREENSHOT_DIR, exist_ok=True)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            save_path = os.path.join(config.SCREENSHOT_DIR, f"screenshot_{timestamp}.png")
        else:
            # 确保用户传入路径的父目录存在
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
        full_cmd = ["adb", "-s", self.serial, "exec-out", "screencap", "-p"]
        with subprocess.Popen(full_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
            png_data, err = proc.communicate(timeout=5)
            if proc.returncode != 0:
                raise RuntimeError(f"screencap 失败: {err.decode('utf-8', errors='ignore')}")
            if not png_data:
                raise RuntimeError("screencap 未返回任何数据")
            with open(save_path, "wb") as f:
                f.write(png_data)

    def tap(self, x: int, y: int):
        """点按屏幕坐标"""
        self._adb_cmd(["shell", "input", "tap", str(x), str(y)])

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300):
        """滑动屏幕"""
        self._adb_cmd(["shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration_ms)])

    def input_text(self, text: str):
        """
        输入文字（模拟键盘）。
        自动转义空格和特殊字符，使用单引号包裹文本。
        """
        # 对文本中的单引号进行转义（如果存在），然后用单引号整体包裹
        escaped = text.replace("'", "\\'")
        self._adb_cmd(["shell", "input", "text", f"'{escaped}'"])

    def keyevent(self, key: str):
        """
        发送按键事件。
        :param key: 按键代码或名称，例如 "KEYCODE_HOME", "HOME", "3", "26"（电源）等
        """
        self._adb_cmd(["shell", "input", "keyevent", key])

    def get_foreground_app(self) -> Tuple[str, str]:
        """
        获取当前前台应用的包名和 Activity。
        :return: (package_name, activity_name) 例如 ("com.android.settings", ".Settings")
        """
        result = self._adb_cmd(["shell", "dumpsys", "window"], check=False)
        if result.returncode != 0:
            return ("unknown", "unknown")

        for line in result.stdout.split("\n"):
            if "mCurrentFocus" in line:
                # 示例: mCurrentFocus=Window{abc123 u0 com.example.app/com.example.MainActivity}
                import re
                match = re.search(r"mCurrentFocus=.*? (\S+?)/(\S+?)[\}]", line)
                if match:
                    package = match.group(1)
                    activity = match.group(2)
                    return (package, activity)
                # 备选解析（不含括号的旧格式）
                parts = line.split()
                for part in parts:
                    if '/' in part and not part.startswith('Window'):
                        pkg_act = part.split('/')
                        if len(pkg_act) == 2:
                            return (pkg_act[0], pkg_act[1])
        return ("unknown", "unknown")

    # 可选：增加一个检查设备是否可用的方法
    def is_available(self) -> bool:
        """检查设备是否在线且响应"""
        result = self._adb_cmd(["shell", "echo", "ok"], check=False)
        return result.returncode == 0 and result.stdout.strip() == "ok"