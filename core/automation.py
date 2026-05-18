import asyncio
from loguru import logger
from typing import Callable, Coroutine, Any

class AutomationEngine:
    """
    Handles scheduling and running background tasks asynchronously without blocking the main event loop.
    """
    def __init__(self):
        self.active_tasks = []

    def schedule_task(self, delay_seconds: int, coro_func: Callable[[], Coroutine[Any, Any, Any]]):
        """
        Schedules a coroutine to run after a specific delay.
        """
        async def delayed_execution():
            logger.info(f"Task scheduled for {delay_seconds} seconds from now.")
            await asyncio.sleep(delay_seconds)
            logger.info("Executing scheduled task...")
            try:
                await coro_func()
                logger.info("Scheduled task completed successfully.")
            except Exception as e:
                logger.error(f"Scheduled task failed: {e}")

        task = asyncio.create_task(delayed_execution())
        self.active_tasks.append(task)
        # Clean up finished tasks
        task.add_done_callback(lambda t: self.active_tasks.remove(t) if t in self.active_tasks else None)

# Global singleton
automation_engine = AutomationEngine()
