"""Composition root for the AI backend WSGI application."""

from __future__ import annotations

from agent_platform.startup.service_factory import AgentPlatformServiceFactory
from ai_backend.application import AiBackendApplication
from runtime.provider import SettingsProvider, SettingsRequest


def create_app() -> AiBackendApplication:
    settings = SettingsProvider(SettingsRequest(backend_ai_backend=True)).bundle.backend_ai_backend
    agent_app = AgentPlatformServiceFactory().build()
    return AiBackendApplication(settings=settings, agent_app=agent_app)
