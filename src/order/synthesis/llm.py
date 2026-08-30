"""AI synthesis using LiteLLM"""
import json
import logging
from typing import List
from datetime import datetime

from ..core.models import Commitment
from ..core.config import settings

logger = logging.getLogger(__name__)

try:
    from litellm import acompletion
    HAS_LITELLM = True
except ImportError:
    HAS_LITELLM = False


def _has_llm() -> bool:
    """Return True if a working LLM API key is configured."""
    return HAS_LITELLM and bool(settings.openrouter_api_key or settings.openai_api_key)


def _model() -> str:
    """Pick model: prefer openrouter, fall back to openai."""
    if settings.openrouter_api_key:
        return settings.llm_model
    return "gpt-4o-mini"


async def _complete(messages: list, **kwargs) -> str:
    """Call acompletion and return the text content."""
    response = await acompletion(model=_model(), messages=messages, **kwargs)
    return response.choices[0].message.content


async def extract_commitment(text: str, source: str) -> dict:
    """Extract commitment from raw text"""
    if not _has_llm():
        # Heuristic fallback
        lowered = text.lower()
        is_commitment = any(kw in lowered for kw in (
            "i'll", "i will", "i can", "i'll make sure", "let me",
            "can you", "could you", "please", "by friday", "by eod",
            "deadline", "asap", "urgent",
        ))
        return {
            "is_commitment": is_commitment,
            "task": text[:80].strip(),
            "deadline": None,
            "priority": 1,
        }

    prompt = f"""You are extracting action items from a message.

Source platform: {source}
Message: {text}

Determine if this message contains a commitment or action item that requires follow-up.
A commitment is something someone promised to do, or asked you to do.

Return JSON only:
{{
    "is_commitment": true or false,
    "task": "concise description of what needs to be done (max 100 chars)",
    "deadline": "YYYY-MM-DD if a date is mentioned, otherwise null",
    "priority": 0 (low) | 1 (normal) | 2 (high) | 3 (urgent)
}}"""

    try:
        content = await _complete(
            [{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_tokens=200,
        )
        return json.loads(content)
    except Exception as exc:
        logger.warning("extract_commitment failed: %s", exc)
        return {"is_commitment": False, "task": "", "deadline": None, "priority": 0}


async def filter_commitments(commitments: List[Commitment]) -> List[Commitment]:
    """Filter out noise, keep what matters"""
    if not commitments:
        return []

    if not _has_llm():
        return commitments

    items = [
        f"{i}. [{c.source.value}] {c.extracted_task or c.text[:100]}"
        for i, c in enumerate(commitments[:20])
    ]

    prompt = f"""You are a personal assistant helping filter a list of commitments.
Keep items that are real, actionable commitments. Remove noise, spam, and duplicates.

{chr(10).join(items)}

Return JSON only — an array of indices (0-based) to KEEP:
{{"keep": [0, 2, 3, ...]}}"""

    try:
        content = await _complete(
            [{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_tokens=200,
        )
        result = json.loads(content)
        keep_indices = set(result.get("keep", []))
        return [c for i, c in enumerate(commitments) if i in keep_indices]
    except Exception as exc:
        logger.warning("filter_commitments failed: %s", exc)
        return commitments


async def prioritize_commitments(commitments: List[Commitment]) -> List[Commitment]:
    """Prioritize commitments by importance and urgency"""
    if not commitments:
        return []

    # Items with deadlines first (soonest first), then by priority
    with_deadlines = sorted(
        [c for c in commitments if c.deadline],
        key=lambda c: (c.deadline, -c.priority),
    )
    without_deadlines = sorted(
        [c for c in commitments if not c.deadline],
        key=lambda c: -c.priority,
    )
    return with_deadlines + without_deadlines


async def pick_one_thing(commitments: List[Commitment]) -> Commitment | None:
    """Pick the ONE thing to focus on"""
    if not commitments:
        return None

    if len(commitments) == 1:
        return commitments[0]

    if not _has_llm():
        prioritized = await prioritize_commitments(commitments)
        return prioritized[0]

    candidates = commitments[:10]
    items = "\n".join(
        f"{i}. {c.extracted_task or c.text[:80]} "
        f"(priority={c.priority}, deadline={c.deadline or 'none'}, source={c.source.value})"
        for i, c in enumerate(candidates)
    )

    prompt = f"""You are helping someone who is overwhelmed decide on ONE thing to focus on right now.

Candidates:
{items}

Consider:
- Deadlines (sooner = more urgent)
- Priority level (3=urgent, 2=high, 1=normal, 0=low)
- Impact (what unlocks the most for this person?)

Return JSON only:
{{"pick": <index 0-{len(candidates)-1}>, "reason": "one sentence"}}"""

    try:
        content = await _complete(
            [{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_tokens=150,
        )
        result = json.loads(content)
        idx = int(result.get("pick", 0))
        return candidates[idx] if idx < len(candidates) else candidates[0]
    except Exception as exc:
        logger.warning("pick_one_thing failed: %s", exc)
        prioritized = await prioritize_commitments(commitments)
        return prioritized[0]


async def explain_why(commitment: Commitment) -> str:
    """Explain why this commitment was chosen"""
    if not _has_llm():
        parts = [f"Priority: {commitment.priority}", f"Source: {commitment.source.value}"]
        if commitment.deadline:
            parts.append(f"Deadline: {commitment.deadline.strftime('%b %d')}")
        return ", ".join(parts)

    prompt = f"""Explain in one sentence why this commitment is the best thing to focus on right now:

Task: {commitment.extracted_task or commitment.text[:100]}
Source: {commitment.source.value}
Priority: {commitment.priority}/3
Deadline: {commitment.deadline.strftime('%B %d') if commitment.deadline else 'none'}

One sentence (max 120 chars):"""

    try:
        return await _complete(
            [{"role": "user", "content": prompt}],
            max_tokens=80,
        )
    except Exception as exc:
        logger.warning("explain_why failed: %s", exc)
        return f"Priority {commitment.priority} item from {commitment.source.value}"
