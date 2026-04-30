"""A2A streaming client used by the Chainlit orchestrator.

Sends a user message to a remote A2A agent via SSE streaming and yields typed
events so the UI layer can differentiate working-state updates from final answers.

Compatible with a2a-sdk >= 1.0.0 (protobuf-based types, create_client factory).
"""

import logging
from collections.abc import AsyncIterator
from typing import TypedDict
from uuid import uuid4

import httpx
from a2a.client import ClientConfig, create_client
from a2a.types import (
    AgentCard,
    Message,
    Part,
    Role,
    SendMessageRequest,
    StreamResponse,
    TaskState,
)

logger = logging.getLogger(__name__)


class A2AEvent(TypedDict):
    """A parsed SSE event from an A2A agent.

    type    – "working" | "final" | "input_required"
    content – Text payload for this event.
    """

    type: str
    content: str


class A2AAgentClient:
    """Thin async wrapper around the a2a-sdk v1.0 Client for streaming interactions."""

    async def send_streaming(
        self,
        agent_card: AgentCard,
        message: str,
        context_id: str,
    ) -> AsyncIterator[A2AEvent]:
        """Stream A2AEvent dicts from a remote agent.

        Uses create_client() which resolves the correct transport from the
        AgentCard's supported_interfaces list and manages the httpx lifecycle.
        """
        request = SendMessageRequest(
            message=Message(
                role=Role.ROLE_USER,
                parts=[Part(text=message)],
                context_id=context_id,
                message_id=uuid4().hex,
            )
        )
        # Local LLMs can be slow — use a generous read timeout while keeping
        # the connection timeout short.
        httpx_client = httpx.AsyncClient(timeout=httpx.Timeout(timeout=300.0, connect=10.0))
        client_config = ClientConfig(httpx_client=httpx_client)
        async with await create_client(agent_card, client_config=client_config) as client:
            async for stream_response in client.send_message(request):
                event = _parse_stream_response(stream_response)
                if event:
                    yield event


# ── Helpers ──────────────────────────────────────────────────────────────────


def _parse_stream_response(response: StreamResponse) -> A2AEvent | None:
    """Extract a typed A2AEvent from a protobuf StreamResponse.

    StreamResponse is a oneof over: task, message, status_update, artifact_update.
    The ``task`` case occurs when the SDK falls back to the non-streaming transport
    and wraps the full Task object in a StreamResponse.
    """
    try:
        payload_field = response.WhichOneof("payload")

        if payload_field == "task":
            task = response.task
            state = task.status.state
            # Extract final result from artifacts first, then status message.
            if state == TaskState.TASK_STATE_INPUT_REQUIRED:
                if task.status.HasField("message"):
                    text = _parts_text(task.status.message.parts)
                    return A2AEvent(type="input_required", content=text)
            elif state in (
                TaskState.TASK_STATE_COMPLETED,
                TaskState.TASK_STATE_FAILED,
            ):
                for artifact in task.artifacts:
                    text = _parts_text(artifact.parts)
                    if text:
                        return A2AEvent(type="final", content=text)
                if task.status.HasField("message"):
                    text = _parts_text(task.status.message.parts)
                    if text:
                        return A2AEvent(type="final", content=text)

        elif payload_field == "status_update":
            su = response.status_update
            state = su.status.state
            text = ""
            if su.status.HasField("message"):
                text = _parts_text(su.status.message.parts)
            if state == TaskState.TASK_STATE_INPUT_REQUIRED:
                return A2AEvent(type="input_required", content=text)
            if state == TaskState.TASK_STATE_WORKING and text:
                return A2AEvent(type="working", content=text)

        elif payload_field == "artifact_update":
            text = _parts_text(response.artifact_update.artifact.parts)
            if text:
                return A2AEvent(type="final", content=text)

        elif payload_field == "message":
            text = _parts_text(response.message.parts)
            if text:
                return A2AEvent(type="final", content=text)

    except Exception as exc:  # noqa: BLE001
        logger.debug("Could not parse A2A stream response: %s", exc)

    return None


def _parts_text(parts) -> str:
    """Concatenate text fields from a repeated Part protobuf field."""
    return " ".join(p.text for p in parts if p.text)
