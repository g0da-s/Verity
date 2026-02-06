"""Claim validation service - ensures claims are specific and testable."""

import logging
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from app.config import settings
from app.utils.retry import invoke_with_retry
from app.utils.sanitize import (
    sanitize_claim,
    wrap_user_content,
    get_security_instruction,
    is_claim_suspicious,
)
import json

logger = logging.getLogger(__name__)


class ClaimValidationError(Exception):
    """Raised when a claim is too vague or not testable."""

    def __init__(self, message: str, suggestions: list[str] | None = None):
        self.message = message
        self.suggestions = suggestions or []
        super().__init__(self.message)


async def validate_claim(claim: str) -> dict:
    """Validate that a health claim is specific and testable.

    A valid claim must have:
    1. A specific intervention (what is being tested)
    2. A specific outcome (what effect is being measured)

    Args:
        claim: The user's health claim

    Returns:
        dict with 'valid' boolean and optional 'suggestions' list

    Raises:
        ClaimValidationError: If the claim is too vague
    """
    # Security: Check and sanitize input
    if is_claim_suspicious(claim):
        logger.warning(f"Suspicious claim detected (possible injection attempt)")

    sanitized_claim = sanitize_claim(claim)

    llm = ChatGroq(
        model="llama-3.3-70b-versatile", api_key=settings.groq_api_key, temperature=0
    )

    system_prompt = """You are a health claim validator. Determine if a claim is SPECIFIC enough to search for scientific evidence.

A VALID claim must have:
1. A specific INTERVENTION (supplement, treatment, activity, food, etc.)
2. A specific OUTCOME (what effect or condition is being measured)

VALID examples:
- "Does creatine improve muscle strength?" (intervention: creatine, outcome: muscle strength)
- "Can vitamin D reduce depression symptoms?" (intervention: vitamin D, outcome: depression)
- "Does intermittent fasting help with weight loss?" (intervention: intermittent fasting, outcome: weight loss)

INVALID examples (too vague):
- "red light therapy" (no outcome specified)
- "is turmeric good for you" (outcome too vague)
- "benefits of exercise" (outcome too vague)
- "creatine" (no outcome specified)

Respond with JSON only:
{
  "valid": true/false,
  "reason": "brief explanation",
  "suggestions": ["specific claim 1", "specific claim 2", "specific claim 3"]
}

If valid, suggestions can be empty. If invalid, provide 2-3 specific claim suggestions based on common research questions about the topic.
""" + get_security_instruction()

    # Wrap user content in tags for clear boundary
    wrapped_claim = wrap_user_content(sanitized_claim)

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Analyze this health claim:\n{wrapped_claim}"),
    ]

    response = await invoke_with_retry(llm, messages)

    # Parse response
    content = response.content
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()

    result = json.loads(content)

    if not result.get("valid", False):
        raise ClaimValidationError(
            message=result.get("reason", "Claim is too vague"),
            suggestions=result.get("suggestions", []),
        )

    return result
