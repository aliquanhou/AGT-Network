"""
Autonomous Engine — Opportunity Detector (v0.3)

Scans for value creation opportunities that Agents can act on.

Detection strategies:
1. Code Analysis: scan codebases for optimization opportunities
2. Knowledge Gap: identify missing documentation or knowledge entries
3. Tool Gap: detect missing tools or utilities
4. Quality Improvement: find areas where quality can be improved

The detector produces Opportunity records — potential value creation points.
These feed into the TaskGenerator to become formal task proposals.
"""

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class OpportunityType(str, Enum):
    CODE_OPTIMIZATION = "code_optimization"
    KNOWLEDGE_GAP = "knowledge_gap"
    TOOL_GAP = "tool_gap"
    QUALITY_IMPROVEMENT = "quality_improvement"
    SECURITY_FIX = "security_fix"
    DOCUMENTATION = "documentation"


@dataclass
class Opportunity:
    """A detected value creation opportunity"""
    opportunity_id: str
    type: OpportunityType
    title: str
    description: str
    source: str = ""  # e.g., repo URL, issue link
    estimated_difficulty: int = 3  # 1-10
    estimated_value: float = 20.0  # AGT Credit
    context: dict = field(default_factory=dict)  # Additional context
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def novelty_hash(self) -> str:
        """Hash for duplicate detection"""
        core = f"{self.type.value}:{self.title}:{self.source}"
        return hashlib.sha256(core.encode()).hexdigest()

    def to_dict(self) -> dict:
        return {
            "opportunity_id": self.opportunity_id,
            "type": self.type.value,
            "title": self.title,
            "description": self.description,
            "source": self.source,
            "estimated_difficulty": self.estimated_difficulty,
            "estimated_value": self.estimated_value,
            "context": self.context,
            "novelty_hash": self.novelty_hash,
        }


class OpportunityDetector:
    """
    Scans for value creation opportunities.

    v0.3: Heuristic + LLM-assisted detection.
    v0.5+: Real-time scanning of connected data sources.
    """

    def __init__(self, llm_client=None):
        self.llm = llm_client
        self._recent_hashes: set[str] = set()  # For novelty checking
        self._max_recent_hashes = 500

    async def scan(
        self,
        domain: str = "general",
        context: dict = None,
    ) -> list[Opportunity]:
        """
        Scan for opportunities in a given domain.

        Returns a list of detected opportunities.
        """
        opportunities = []

        if domain == "code" or domain == "general":
            opportunities.extend(self._scan_code_domain(context))

        if domain == "knowledge" or domain == "general":
            opportunities.extend(self._scan_knowledge_domain(context))

        if domain == "tool" or domain == "general":
            opportunities.extend(self._scan_tool_domain(context))

        # Use LLM for deeper analysis if available
        if self.llm and context:
            try:
                llm_opps = await self._llm_scan(domain, context)
                opportunities.extend(llm_opps)
            except Exception as e:
                logger.warning(f"[Detector] LLM scan failed: {e}")

        # Filter out recently seen opportunities
        fresh = [o for o in opportunities if o.novelty_hash not in self._recent_hashes]
        for o in fresh:
            self._recent_hashes.add(o.novelty_hash)

        # Keep bounded
        if len(self._recent_hashes) > self._max_recent_hashes:
            self._recent_hashes = set(list(self._recent_hashes)[-self._max_recent_hashes:])

        logger.info(f"[Detector] Found {len(fresh)} opportunities in domain '{domain}'")
        return fresh

    def _scan_code_domain(self, context: dict = None) -> list[Opportunity]:
        """Scan for code-related opportunities"""
        import uuid
        opps = []

        # Heuristic: code complexity signals optimization opportunity
        if context and "code_sample" in context:
            code = context["code_sample"]
            lines = len(code.split("\n"))
            if lines > 50:
                opps.append(Opportunity(
                    opportunity_id=f"opp-{uuid.uuid4().hex[:8]}",
                    type=OpportunityType.CODE_OPTIMIZATION,
                    title="Code Refactoring Opportunity",
                    description=f"Code sample of {lines} lines may benefit from refactoring",
                    source=context.get("source", ""),
                    estimated_difficulty=max(2, min(8, lines // 25)),
                    estimated_value=20.0 + lines * 0.5,
                    context=context,
                ))

        return opps

    def _scan_knowledge_domain(self, context: dict = None) -> list[Opportunity]:
        """Scan for knowledge gaps"""
        import uuid
        opps = []

        # Heuristic: missing documentation signals knowledge gap
        if context and "missing_topics" in context:
            for topic in context["missing_topics"]:
                opps.append(Opportunity(
                    opportunity_id=f"opp-{uuid.uuid4().hex[:8]}",
                    type=OpportunityType.KNOWLEDGE_GAP,
                    title=f"Knowledge Entry: {topic}",
                    description=f"Missing knowledge entry for: {topic}",
                    estimated_difficulty=2,
                    estimated_value=15.0,
                    context={"topic": topic},
                ))

        return opps

    def _scan_tool_domain(self, context: dict = None) -> list[Opportunity]:
        """Scan for tool gaps"""
        import uuid
        opps = []

        if context and "missing_tools" in context:
            for tool in context["missing_tools"]:
                opps.append(Opportunity(
                    opportunity_id=f"opp-{uuid.uuid4().hex[:8]}",
                    type=OpportunityType.TOOL_GAP,
                    title=f"Tool Needed: {tool}",
                    description=f"Missing tool/utility: {tool}",
                    estimated_difficulty=5,
                    estimated_value=40.0,
                    context={"tool_name": tool},
                ))

        return opps

    async def _llm_scan(self, domain: str, context: dict) -> list[Opportunity]:
        """Use LLM for deeper opportunity detection"""
        import uuid

        prompt = (
            f"Analyze the following context and identify value creation opportunities "
            f"in the '{domain}' domain. For each opportunity, provide: "
            f"title, description, difficulty (1-10), value (AGT Credit).\n\n"
            f"Context: {context}\n\n"
            f"Output as JSON list."
        )
        resp = await self.llm.chat(prompt, temperature=0.5, max_tokens=1024)

        # Parse LLM response (basic — v0.3 heuristic extraction)
        opps = []
        try:
            import json
            items = json.loads(resp.content)
            for item in items if isinstance(items, list) else [items]:
                opps.append(Opportunity(
                    opportunity_id=f"opp-llm-{uuid.uuid4().hex[:6]}",
                    type=OpportunityType(item.get("type", "quality_improvement")),
                    title=item.get("title", "Untitled")[:200],
                    description=item.get("description", "")[:500],
                    estimated_difficulty=max(1, min(10, item.get("difficulty", 3))),
                    estimated_value=max(5.0, min(100.0, item.get("value", 20.0))),
                ))
        except Exception:
            pass

        return opps

    def is_novel(self, opportunity: Opportunity) -> bool:
        """Check if an opportunity has been seen recently"""
        return opportunity.novelty_hash not in self._recent_hashes
