"""Default cron jobs"""
import logging

from ..core.store import store
from ..core.config import settings
from ..gatherers import DiscordGatherer, GitHubGatherer, XGatherer, GmailGatherer
from ..synthesis.llm import filter_commitments, prioritize_commitments

logger = logging.getLogger(__name__)


async def gather_all():
    """Gather commitments from all sources"""
    commitments = []
    errors = {}

    gatherers = {
        "discord": DiscordGatherer(),
        "github": GitHubGatherer(),
        "x": XGatherer(),
        "gmail": GmailGatherer(),
    }

    for name, gatherer in gatherers.items():
        try:
            if await gatherer.test_connection():
                result = await gatherer.run()
                commitments.extend(result.commitments)
                logger.info("gather %s: %d items", name, len(result.commitments))
            else:
                logger.debug("gather %s: not configured, skipping", name)
        except Exception as exc:
            logger.error("gather %s failed: %s", name, exc)
            errors[name] = str(exc)

    if commitments:
        await store.add_many(commitments)

    return len(commitments)


async def reduce_all():
    """Filter and prioritize commitments"""
    pending = await store.get_pending()
    
    if not pending:
        return 0
    
    # Filter noise
    filtered = await filter_commitments(pending)
    
    # Prioritize
    prioritized = await prioritize_commitments(filtered)
    
    # Update store
    for commitment in prioritized:
        await store.update_status(commitment.id, commitment.status)
    
    return len(prioritized)


async def expire_old():
    """Expire old pending commitments"""
    expired = await store.expire_old(hours=settings.commitment_expire_hours)
    return expired