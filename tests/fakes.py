"""SCRIPTED FAKE model shared by the HTTP and browser suites (no network, no API key).

It returns pre-written model turns (tool calls or text) or raises a scripted error, so the tests exercise the
backend and the page: tool execution, card hydration, text checks, sessions and public errors. Real-model
behavior is covered by the benchmark and the smoke scripts, never by these tests.
"""

from __future__ import annotations

import threading
import uuid

from google.genai import types

from app.agent import ModelReply


def call(name: str, **args) -> ModelReply:
    part = types.Part(function_call=types.FunctionCall(id=str(uuid.uuid4()), name=name, args=args))
    return ModelReply(content=types.Content(role="model", parts=[part]), calls=[part.function_call], text="",
                      usage={"input": 1, "output": 1})


def say(text: str) -> ModelReply:
    return ModelReply(content=types.Content(role="model", parts=[types.Part(text=text)]), calls=[], text=text,
                      usage={"input": 1, "output": 1})


class FakeLLM:
    """Scripted stand-in for Gemini. Each generate() pops the next reply or raises the scripted error."""

    model = "fake-scripted"

    def __init__(self, script: list):
        self.script = list(script)
        self.seen: list[list[types.Content]] = []
        self.gate: threading.Event | None = None

    def generate(self, *, system, contents, tools, timeout_s, allow_tools):
        self.seen.append(list(contents))
        if self.gate is not None:
            self.gate.wait(5)
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item
