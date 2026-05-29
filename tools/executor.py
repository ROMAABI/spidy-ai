import yaml
import subprocess
import threading

with open("config.yaml") as f:
    config = yaml.safe_load(f)

SAFETY = config["safety"]

class Executor:
    def __init__(self, on_speak=None, on_status=None):
        self.on_speak  = on_speak   # callback → TTS speak
        self.on_status = on_status  # callback → UI status update
        self.pending   = None       # dangerous command waiting for permission

    def execute(self, command: str):
        """Main entry — routes through safety gate first"""
        if self._is_dangerous(command):
            self._request_permission(command)
        else:
            self._run(command)

    def confirm(self, user_input: str):
        """Call this when user responds to a permission request"""
        if not self.pending:
            return

        confirm_words = ["yes", "pannu", "sari", "ok", "ama", "do it", "confirm"]
        cancel_words  = ["no", "venda", "cancel", "stop", "nope"]

        if any(w in user_input.lower() for w in confirm_words):
            cmd = self.pending
            self.pending = None
            self._speak("Sari anna, pannureen!")
            self._run(cmd)
        elif any(w in user_input.lower() for w in cancel_words):
            self.pending = None
            self._speak("Sari anna, cancel panniten.")
        # If neither — keep waiting

    def has_pending(self) -> bool:
        return self.pending is not None

    def _is_dangerous(self, command: str) -> bool:
        cmd_lower = command.lower()
        has_danger = any(k in cmd_lower for k in SAFETY["dangerous_keywords"])
        has_sudo   = "sudo" in cmd_lower
        return has_danger or (has_sudo and SAFETY["sudo_requires_permission"])

    def _request_permission(self, command: str):
        self.pending = command
        msg = f"Anna, ithu dangerous command: `{command}` — pannava?"
        self._speak(msg)
        self._set_status("waiting_permission")

    def _run(self, command: str):
        """Execute shell command in background thread"""
        self._set_status("executing")

        def _worker():
            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    executable="/usr/bin/fish",
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    output = result.stdout.strip()
                    msg = f"Command finished anna. {output[:100] if output else ''}"
                else:
                    msg = f"Command failed anna. {result.stderr.strip()[:100]}"
            except subprocess.TimeoutExpired:
                msg = "Command timed out anna."
            except Exception as e:
                msg = f"Error anna: {str(e)}"

            self._speak(msg)
            self._set_status("listening")

        threading.Thread(target=_worker, daemon=True).start()

    def _speak(self, text: str):
        if self.on_speak:
            self.on_speak(text)
        else:
            print(f"[Executor] {text}")

    def _set_status(self, status: str):
        if self.on_status:
            self.on_status(status)
        else:
            print(f"[Executor] Status: {status}")