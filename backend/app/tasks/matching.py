import asyncio
import logging
import threading
from uuid import UUID

from app.db.session import async_session_factory
from app.models import Item
from app.services.matching import run_matching_algorithm
from app.services.notifications import notify_match_created

logger = logging.getLogger(__name__)


async def _process_item_matches(item_id: UUID) -> None:
    logger.info(f"Processing matches for item {item_id}")
    async with async_session_factory() as session:
        item = await session.get(Item, item_id)
        if item is None:
            logger.warning(f"Item {item_id} not found")
            return
        if not item.is_active:
            logger.info(f"Item {item_id} is not active, skipping matching")
            return

        logger.info(f"Running matching algorithm for item {item_id} (status: {item.status}, description: {item.description[:50]}...)")
        matches = await run_matching_algorithm(session, item)
        logger.info(f"Matching algorithm returned {len(matches)} matches")

        for match in matches:
            await session.refresh(match, attribute_names=["lost_item", "found_item"])
            await session.refresh(match.lost_item, attribute_names=["reported_by"])
            await session.refresh(match.found_item, attribute_names=["reported_by"])
            logger.info(f"Sending notification for match {match.id}")
            try:
                await notify_match_created(match=match, lost_item=match.lost_item, found_item=match.found_item)
            except Exception as e:
                # Log notification errors but don't fail the matching process
                logger.warning(f"Failed to send notification for match {match.id}: {e}")

        if matches:
            await session.commit()
            logger.info(f"Committed {len(matches)} matches to database")
        else:
            logger.info("No matches to commit")


def schedule_matching(item_id: UUID) -> None:
    """Trigger the asynchronous matching algorithm for an item."""
    logger.info(f"schedule_matching called for item {item_id}")
    # BackgroundTasks runs in a thread pool without an event loop,
    # so we create a new event loop in a separate thread
    def run_async():
        logger.info(f"Starting async matching thread for item {item_id}")
        # Create a new event loop for this thread
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        try:
            logger.info(f"Running matching algorithm for item {item_id}")
            new_loop.run_until_complete(_process_item_matches(item_id))
            logger.info(f"Completed matching algorithm for item {item_id}")
        except Exception as e:
            # Log errors but don't crash the background task
            logger.error(f"Error processing matches for item {item_id}: {e}", exc_info=True)
        finally:
            # Clean up the event loop
            try:
                # Cancel any remaining tasks
                pending = asyncio.all_tasks(new_loop)
                for task in pending:
                    task.cancel()
                # Wait for tasks to complete cancellation
                if pending:
                    new_loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            except Exception as cleanup_error:
                logger.error(f"Error during cleanup for item {item_id}: {cleanup_error}")
            finally:
                new_loop.close()
                logger.info(f"Closed event loop for item {item_id}")
    
    thread = threading.Thread(target=run_async, daemon=True, name=f"matching-{item_id}")
    logger.info(f"Starting thread for matching item {item_id}")
    thread.start()
    logger.info(f"Thread started for matching item {item_id}")


