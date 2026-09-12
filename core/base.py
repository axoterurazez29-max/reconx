#!/usr/bin/env python3
"""
ReconX - Base Module
All recon modules inherit from this class.
"""

import os
import time
from abc import ABC, abstractmethod

from .runner import Runner
from . import utils
from . import progress as ui


class BaseModule(ABC):
    """
    Abstract base class for all ReconX modules.

    Each module must:
      - set `name` (display name)
      - set `key` (internal key)
      - set `required_tools` (list of external tools)
      - implement `run(target, output_dir, **kwargs)` returning list of findings
    """

    name = "Base Module"
    key = "base"
    required_tools = []
    description = ""

    def __init__(self, runner=None, threads=50, timeout=300):
        self.runner = runner or Runner(verbose=False)
        self.threads = threads
        self.timeout = timeout
        self.results = []
        self.started_at = None
        self.finished_at = None

    def check_tools(self):
        return utils.check_tools(self.required_tools)

    def tools_available(self):
        status = self.check_tools()
        return all(status.values())

    @abstractmethod
    def run(self, target, output_dir, **kwargs):
        """
        Execute the module.

        Returns:
            list of findings (dicts)
        """
        raise NotImplementedError

    def execute(self, target, output_dir, **kwargs):
        ui.module_start(self.name)

        if self.required_tools and not self.tools_available():
            ui.warn(f"{self.name}: missing tools — skipping")
            return {
                "module": self.key,
                "key": self.key,
                "name": self.name,
                "found": 0,
                "duration": 0.0,
                "status": "skip",
                "results": []
            }

        self.started_at = time.time()

        try:
            self.results = self.run(target, output_dir, **kwargs) or []
            status = "ok" if self.results else "empty"
        except Exception as e:
            ui.error(f"{self.name} failed: {e}")
            self.results = []
            status = "fail"

        self.finished_at = time.time()
        duration = self.finished_at - self.started_at

        ui.module_done(self.name, len(self.results), duration)

        return {
            "module": self.key,
            "key": self.key,
            "name": self.name,
            "found": len(self.results),
            "duration": round(duration, 2),
            "status": status,
            "results": self.results
        }

    def save_raw(self, output_dir, filename, content):
        path = os.path.join(output_dir, "raw", filename)
        utils.write_file(path, content)
        return path
