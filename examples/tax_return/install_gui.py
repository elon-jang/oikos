#!/usr/bin/env python3
"""
기부금 영수증 MCP 서버 GUI 설치 도우미

비개발자를 위한 원클릭 설치 GUI입니다.
더블클릭으로 실행하면 Docker 이미지 설치와 Claude Desktop 설정을 자동으로 수행합니다.
"""

import os
import sys
import json
import platform
import subprocess
import threading
import tempfile
import shutil
from pathlib import Path

# Tkinter import
try:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog
except ImportError:
    print("tkinter가 설치되어 있지 않습니다.")
    print("macOS: brew install python-tk")
    print("Ubuntu: sudo apt-get install python3-tk")
    sys.exit(1)


class InstallerApp:
    """MCP 서버 설치 GUI"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("기부금 영수증 MCP 설치")
        self.root.geometry("500x600")
        self.root.resizable(False, False)

        # 운영체제 확인
        self.is_macos = platform.system() == "Darwin"
        self.is_windows = platform.system() == "Windows"

        # 기본 데이터 폴더
        if self.is_macos:
            self.default_data_dir = os.path.expanduser("~/기부금영수증")
        elif self.is_windows:
            self.default_data_dir = os.path.join(os.environ.get("USERPROFILE", ""), "기부금영수증")
        else:
            self.default_data_dir = os.path.expanduser("~/기부금영수증")

        # 변수
        self.data_dir = tk.StringVar(value=self.default_data_dir)
        self.status = tk.StringVar(value="설치 준비 중...")
        self.progress = tk.DoubleVar(value=0)
        self.is_installing = False

        self._create_widgets()
        self._check_docker()

    def _create_widgets(self):
        """GUI 위젯 생성"""
        # 제목
        title_frame = tk.Frame(self.root, pady=20)
        title_frame.pack(fill=tk.X)

        tk.Label(
            title_frame,
            text="🎁 기부금 영수증 MCP 서버",
            font=("", 18, "bold")
        ).pack()

        tk.Label(
            title_frame,
            text="Claude Desktop에서 자연어로 영수증을 발행합니다",
            font=("", 11),
            fg="gray"
        ).pack(pady=5)

        # 구분선
        ttk.Separator(self.root, orient="horizontal").pack(fill=tk.X, padx=20)

        # Docker 상태
        docker_frame = tk.Frame(self.root, pady=15)
        docker_frame.pack(fill=tk.X, padx=30)

        tk.Label(docker_frame, text="1. Docker 상태", font=("", 12, "bold")).pack(anchor="w")

        self.docker_status_frame = tk.Frame(docker_frame)
        self.docker_status_frame.pack(fill=tk.X, pady=5)

        self.docker_icon = tk.Label(self.docker_status_frame, text="🔍", font=("", 14))
        self.docker_icon.pack(side=tk.LEFT)

        self.docker_label = tk.Label(
            self.docker_status_frame,
            text="확인 중...",
            font=("", 11)
        )
        self.docker_label.pack(side=tk.LEFT, padx=10)

        self.docker_link = tk.Label(
            docker_frame,
            text="",
            font=("", 10),
            fg="blue",
            cursor="hand2"
        )
        self.docker_link.pack(anchor="w")

        # 데이터 폴더 선택
        folder_frame = tk.Frame(self.root, pady=15)
        folder_frame.pack(fill=tk.X, padx=30)

        tk.Label(folder_frame, text="2. 데이터 폴더", font=("", 12, "bold")).pack(anchor="w")
        tk.Label(
            folder_frame,
            text="영수증 템플릿과 헌금 데이터를 저장할 폴더입니다.",
            font=("", 10),
            fg="gray"
        ).pack(anchor="w", pady=2)

        folder_input_frame = tk.Frame(folder_frame)
        folder_input_frame.pack(fill=tk.X, pady=5)

        tk.Entry(
            folder_input_frame,
            textvariable=self.data_dir,
            font=("", 11),
            width=35
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Button(
            folder_input_frame,
            text="찾아보기",
            command=self._select_folder
        ).pack(side=tk.RIGHT, padx=5)

        # 설치 버튼
        button_frame = tk.Frame(self.root, pady=20)
        button_frame.pack(fill=tk.X, padx=30)

        self.install_button = tk.Button(
            button_frame,
            text="🚀 설치하기",
            font=("", 14, "bold"),
            bg="#4CAF50",
            fg="white",
            height=2,
            command=self._start_install
        )
        self.install_button.pack(fill=tk.X)

        # 진행률
        progress_frame = tk.Frame(self.root, pady=10)
        progress_frame.pack(fill=tk.X, padx=30)

        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress,
            maximum=100
        )
        self.progress_bar.pack(fill=tk.X)

        tk.Label(
            progress_frame,
            textvariable=self.status,
            font=("", 10),
            fg="gray"
        ).pack(pady=5)

        # 로그 출력
        log_frame = tk.Frame(self.root, pady=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=30)

        tk.Label(log_frame, text="설치 로그", font=("", 11, "bold")).pack(anchor="w")

        self.log_text = tk.Text(
            log_frame,
            height=10,
            font=("Courier", 10),
            state=tk.DISABLED,
            bg="#f5f5f5"
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=5)

        # 스크롤바
        scrollbar = ttk.Scrollbar(self.log_text, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)

    def _log(self, message: str):
        """로그 메시지 추가"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update()

    def _select_folder(self):
        """폴더 선택 다이얼로그"""
        folder = filedialog.askdirectory(
            title="데이터 폴더 선택",
            initialdir=os.path.dirname(self.data_dir.get())
        )
        if folder:
            self.data_dir.set(folder)

    def _check_docker(self):
        """Docker 상태 확인"""
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                # Docker 데몬 확인
                result2 = subprocess.run(
                    ["docker", "info"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result2.returncode == 0:
                    self.docker_icon.config(text="✅")
                    self.docker_label.config(text="Docker 실행 중", fg="green")
                    self.docker_link.config(text="")
                    return True
                else:
                    self.docker_icon.config(text="⚠️")
                    self.docker_label.config(text="Docker Desktop을 실행하세요", fg="orange")
                    return False
            else:
                raise FileNotFoundError()
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self.docker_icon.config(text="❌")
            self.docker_label.config(text="Docker가 설치되어 있지 않습니다", fg="red")
            self.docker_link.config(text="👉 Docker Desktop 다운로드")
            self.docker_link.bind("<Button-1>", self._open_docker_download)
            return False

    def _open_docker_download(self, event=None):
        """Docker 다운로드 페이지 열기"""
        import webbrowser
        if self.is_macos:
            webbrowser.open("https://docs.docker.com/desktop/install/mac-install/")
        elif self.is_windows:
            webbrowser.open("https://docs.docker.com/desktop/install/windows-install/")
        else:
            webbrowser.open("https://docs.docker.com/desktop/")

    def _start_install(self):
        """설치 시작"""
        if self.is_installing:
            return

        # Docker 재확인
        if not self._check_docker():
            messagebox.showerror(
                "Docker 필요",
                "Docker Desktop이 실행 중이어야 합니다.\n"
                "Docker Desktop을 설치하고 실행한 후 다시 시도하세요."
            )
            return

        self.is_installing = True
        self.install_button.config(state=tk.DISABLED, text="설치 중...")

        # 별도 스레드에서 설치 실행
        thread = threading.Thread(target=self._install)
        thread.daemon = True
        thread.start()

    def _install(self):
        """설치 수행 (별도 스레드)"""
        try:
            # 1. 데이터 폴더 생성
            self._update_progress(10, "데이터 폴더 생성 중...")
            data_dir = self.data_dir.get()
            os.makedirs(os.path.join(data_dir, "receipts"), exist_ok=True)
            self._log(f"✅ 폴더 생성: {data_dir}")

            # 2. 소스 코드 다운로드
            self._update_progress(20, "소스 코드 다운로드 중...")
            temp_dir = tempfile.mkdtemp()
            self._log(f"📥 소스 코드 다운로드 중...")

            result = subprocess.run(
                ["git", "clone", "--depth", "1", "https://github.com/elon-jang/oikos.git"],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode != 0:
                raise Exception(f"Git clone 실패: {result.stderr}")

            self._log("✅ 소스 코드 다운로드 완료")

            # 3. Docker 이미지 빌드
            self._update_progress(40, "Docker 이미지 빌드 중... (몇 분 소요)")
            build_dir = os.path.join(temp_dir, "oikos", "examples", "tax_return")
            self._log("🐳 Docker 이미지 빌드 중...")

            result = subprocess.run(
                ["docker", "build", "-t", "oikos-receipt:latest", "."],
                cwd=build_dir,
                capture_output=True,
                text=True,
                timeout=600
            )

            if result.returncode != 0:
                raise Exception(f"Docker 빌드 실패: {result.stderr}")

            self._log("✅ Docker 이미지 빌드 완료")

            # 4. 샘플 파일 복사
            self._update_progress(70, "샘플 파일 복사 중...")
            sample_file = os.path.join(build_dir, "sample_income_summary.xlsx")
            if os.path.exists(sample_file):
                shutil.copy(sample_file, data_dir)
                self._log("✅ 샘플 파일 복사 완료")

            # 5. Claude Desktop 설정
            self._update_progress(85, "Claude Desktop 설정 중...")
            self._configure_claude_desktop(data_dir)
            self._log("✅ Claude Desktop 설정 완료")

            # 6. 임시 폴더 정리
            self._update_progress(95, "정리 중...")
            shutil.rmtree(temp_dir, ignore_errors=True)

            # 완료
            self._update_progress(100, "설치 완료!")
            self._log("")
            self._log("🎉 설치가 완료되었습니다!")
            self._log(f"📂 데이터 폴더: {data_dir}")
            self._log("")
            self._log("다음 단계:")
            self._log("1. 데이터 폴더에 템플릿과 헌금 데이터를 넣으세요")
            self._log("2. Claude Desktop을 재시작하세요")

            self.root.after(0, lambda: messagebox.showinfo(
                "설치 완료",
                f"설치가 완료되었습니다!\n\n"
                f"📂 데이터 폴더: {data_dir}\n\n"
                f"다음 파일을 데이터 폴더에 넣으세요:\n"
                f"- donation_receipt_template.docx\n"
                f"- YYYY_income_summary.xlsx\n\n"
                f"🔄 Claude Desktop을 재시작하세요."
            ))

        except Exception as e:
            self._log(f"❌ 오류: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror(
                "설치 실패",
                f"설치 중 오류가 발생했습니다:\n{str(e)}"
            ))

        finally:
            self.is_installing = False
            self.root.after(0, lambda: self.install_button.config(
                state=tk.NORMAL,
                text="🚀 설치하기"
            ))

    def _update_progress(self, value: float, status: str):
        """진행률 업데이트 (메인 스레드에서)"""
        self.root.after(0, lambda: self.progress.set(value))
        self.root.after(0, lambda: self.status.set(status))

    def _configure_claude_desktop(self, data_dir: str):
        """Claude Desktop 설정 파일 수정"""
        if self.is_macos:
            config_dir = os.path.expanduser("~/Library/Application Support/Claude")
        elif self.is_windows:
            config_dir = os.path.join(os.environ.get("APPDATA", ""), "Claude")
        else:
            config_dir = os.path.expanduser("~/.config/claude")

        config_file = os.path.join(config_dir, "claude_desktop_config.json")

        # 디렉토리 생성
        os.makedirs(config_dir, exist_ok=True)

        # 기존 설정 로드
        config = {}
        if os.path.exists(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                # 백업
                backup_file = config_file + ".backup"
                shutil.copy(config_file, backup_file)
                self._log(f"📋 기존 설정 백업: {backup_file}")
            except Exception:
                config = {}

        # MCP 서버 추가
        config.setdefault("mcpServers", {})
        config["mcpServers"]["oikos-receipt"] = {
            "command": "docker",
            "args": [
                "run", "-i", "--rm",
                "-v", f"{data_dir}:/data",
                "oikos-receipt:latest"
            ]
        }

        # 저장
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

    def run(self):
        """앱 실행"""
        self.root.mainloop()


def main():
    """메인 함수"""
    app = InstallerApp()
    app.run()


if __name__ == "__main__":
    main()
