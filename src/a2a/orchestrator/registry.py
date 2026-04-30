"""AgentRegistry — discovers A2A agents at startup via their Agent Cards.

Agents are declared in config/agents.yaml. On discover(), the registry fetches
each agent's card from its /.well-known/agent-card.json endpoint and indexes it.

Routing strategy (find_agent):
  1. Match skill tags against words in the user query (case-insensitive).
  2. Fall back to the first registered agent.

To upgrade routing to LLM-based skill matching, replace the body of find_agent()
without touching any other code.

Compatible with a2a-sdk >= 1.0.0 (protobuf AgentCard, well-known path changed).
"""

import logging
from pathlib import Path

import httpx
import yaml
from a2a.client import A2ACardResolver
from a2a.types import AgentCard

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Discovers and routes to A2A agents declared in a YAML config file."""

    def __init__(self, config_path: Path) -> None:
        self._config_path = config_path
        self._cards: list[AgentCard] = []

    async def discover(self) -> None:
        """Fetch Agent Cards from every URL listed in the config file.

        Agents that cannot be reached are skipped with a warning so Chainlit
        can still start even if some agent servers are down.

        In a2a-sdk v1.0+ the well-known path is /.well-known/agent-card.json
        (changed from /.well-known/agent.json in v0.3).
        """
        if not self._config_path.exists():
            logger.warning("Agent config not found at %s", self._config_path)
            return

        config = yaml.safe_load(self._config_path.read_text())
        entries: list[dict] = config.get("agents", [])

        async with httpx.AsyncClient(timeout=10.0) as http:
            for entry in entries:
                url: str = entry["url"]
                try:
                    resolver = A2ACardResolver(httpx_client=http, base_url=url)
                    card = await resolver.get_agent_card()
                    self._cards.append(card)
                    logger.info("Discovered agent '%s' at %s", card.name, url)
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "Could not reach agent at %s (%s) — skipping.", url, exc
                    )

    def find_agent(self, query: str) -> AgentCard | None:
        """Return the best-matching AgentCard for the user query.

        Current strategy: tag-based keyword matching, with first-agent fallback.
        Replace this method body for smarter (e.g. LLM-based) routing.

        In a2a-sdk v1.0+ AgentCard.skills and AgentSkill.tags are protobuf
        repeated fields — iteration works identically to Python lists.
        """
        if not self._cards:
            return None

        query_lower = query.lower()
        for card in self._cards:
            for skill in card.skills:          # protobuf repeated field
                for tag in skill.tags:         # protobuf repeated scalar field
                    if tag.lower() in query_lower:
                        return card

        # Fallback: use the first registered agent
        return self._cards[0]

    @property
    def agents(self) -> list[AgentCard]:
        """Return a snapshot of all discovered agent cards."""
        return list(self._cards)
