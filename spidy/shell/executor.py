import asyncio
import shlex
from dataclasses import dataclass


@dataclass
class ShellResult:
    output: str = ""
    returncode: int = 0
    timed_out: bool = False


class ShellExecutor:
    def __init__(self, timeout: int = 30, allowlist: list[str] | None = None):
        self.timeout = timeout
        self.allowlist = allowlist

    async def run(self, cmd: str) -> ShellResult:
        try:
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            try:
                stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=self.timeout)
                return ShellResult(
                    output=stdout.decode(errors="replace").strip(),
                    returncode=proc.returncode or 0,
                )
            except asyncio.TimeoutError:
                proc.kill()
                return ShellResult(output="[Command timed out]", returncode=-1, timed_out=True)
        except FileNotFoundError:
            return ShellResult(output=f"Command not found: {cmd.split()[0]}", returncode=127)
        except Exception as e:
            return ShellResult(output=str(e), returncode=1)
