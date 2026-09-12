#!/usr/bin/env python3
"""
ReconX - Subprocess Runner Engine
Executes external tools, captures output, handles timeouts.
"""

import os
import subprocess
import shlex
import time
from .utils import ensure_dir, write_file


class CommandResult:
    def __init__(self, tool, command, stdout, stderr, returncode, duration, timed_out=False):
        self.tool = tool
        self.command = command
        self.stdout = stdout or ""
        self.stderr = stderr or ""
        self.returncode = returncode
        self.duration = duration
        self.timed_out = timed_out

    @property
    def success(self):
        return self.returncode == 0 and not self.timed_out

    @property
    def lines(self):
        return [ln for ln in self.stdout.splitlines() if ln.strip()]

    def __repr__(self):
        status = "OK" if self.success else "FAIL"
        return f"<CommandResult {self.tool} [{status}] {self.duration:.2f}s>"


class Runner:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.history = []

    def run(self, tool, args, timeout=300, cwd=None, env=None, stdin_data=None):
        if isinstance(args, str):
            args = shlex.split(args)

        command = [tool] + args

        start = time.time()
        timed_out = False
        stdout = ""
        stderr = ""
        returncode = -1

        try:
            proc = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd,
                env=env,
                input=stdin_data
            )
            stdout = proc.stdout
            stderr = proc.stderr
            returncode = proc.returncode

        except subprocess.TimeoutExpired as e:
            timed_out = True
            if e.stdout:
                stdout = e.stdout if isinstance(e.stdout, str) else e.stdout.decode("utf-8", errors="ignore")
            if e.stderr:
                stderr = e.stderr if isinstance(e.stderr, str) else e.stderr.decode("utf-8", errors="ignore")
            returncode = -1

        except FileNotFoundError:
            stderr = f"Tool not found: {tool}"
            returncode = 127

        except Exception as e:
            stderr = f"Unexpected error: {e}"
            returncode = -1

        duration = time.time() - start

        result = CommandResult(
            tool=tool,
            command=" ".join(command),
            stdout=stdout,
            stderr=stderr,
            returncode=returncode,
            duration=duration,
            timed_out=timed_out
        )

        self.history.append(result)

        if self.verbose:
            print(f"[runner] {result}")

        return result

    def run_to_file(self, tool, args, output_file, timeout=300):
        result = self.run(tool, args, timeout=timeout)
        if result.stdout:
            ensure_dir(os.path.dirname(output_file))
            write_file(output_file, result.stdout)
        return result

    def summary(self):
        total = len(self.history)
        ok = sum(1 for r in self.history if r.success)
        failed = total - ok
        total_time = sum(r.duration for r in self.history)
        return {
            "total_commands": total,
            "successful": ok,
            "failed": failed,
            "total_duration": round(total_time, 2)
        }
