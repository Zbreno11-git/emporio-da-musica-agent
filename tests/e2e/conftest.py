"""Browser tests: the real page and a real uvicorn server in a thread, with the SCRIPTED FAKE model (no API key).

Set QA_SCREENS_DIR to save the screenshots the QA report uses (docs/qa/README.md); without it nothing is written.
"""

from __future__ import annotations

import os
import socket
import threading
import time
from dataclasses import replace
from pathlib import Path

import pytest
import uvicorn

from app.main import create_app
from tests.fakes import FakeLLM

playwright_api = pytest.importorskip("playwright.sync_api")


class LiveServer:
    def __init__(self, settings, script):
        self.llm = FakeLLM(script)
        self.app = create_app(settings, llm=self.llm)
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            self.port = sock.getsockname()[1]
        self.server = uvicorn.Server(uvicorn.Config(self.app, host="127.0.0.1", port=self.port, log_level="warning"))
        self.thread = threading.Thread(target=self.server.run, daemon=True)
        self.thread.start()
        deadline = time.monotonic() + 10
        while not self.server.started:
            if time.monotonic() > deadline:
                raise RuntimeError("test server did not start")
            time.sleep(0.02)
        self.url = f"http://127.0.0.1:{self.port}"

    def stop(self):
        self.server.should_exit = True
        self.thread.join(5)


@pytest.fixture
def live(settings):
    servers = []

    def start(script, **overrides):
        server = LiveServer(replace(settings, **overrides), script)
        servers.append(server)
        return server

    yield start
    for server in servers:
        server.stop()


@pytest.fixture(scope="session")
def browser():
    with playwright_api.sync_playwright() as p:
        try:
            b = p.chromium.launch()
        except Exception as exc:  # browsers not installed
            pytest.skip(f"chromium unavailable: {exc}")
        yield b
        b.close()


@pytest.fixture
def page_for(browser):
    """New isolated context per call; collects console errors (CSP violations included) and checks them at the end."""
    contexts, errors = [], []

    def open_page(width=390, height=844, **options):
        ctx = browser.new_context(viewport={"width": width, "height": height}, locale="pt-BR",
                                  timezone_id="America/Campo_Grande", reduced_motion="reduce", **options)
        contexts.append(ctx)
        page = ctx.new_page()
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" and "status of 4" not in m.text
                and "status of 5" not in m.text else None)
        page.on("pageerror", lambda e: errors.append(str(e)))
        return page

    yield open_page
    for ctx in contexts:
        ctx.close()
    assert errors == [], errors


def shot(page, name):
    target = os.environ.get("QA_SCREENS_DIR")
    if target:
        Path(target).mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(Path(target) / f"{name}.png"))
