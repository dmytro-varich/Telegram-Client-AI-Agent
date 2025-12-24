import logging
from services.tg.client.base import BaseTelegramClient

logger = logging.getLogger(__name__)

class TelegramClientManager:
    def __init__(self):
        self.clients: dict[str, BaseTelegramClient] = {}
        
    def add_client(self, name: str, client: BaseTelegramClient) -> None:
        """Add a new Telegram client to the manager."""
        if name in self.clients:
            logger.warning("Telegram client with name '%s' already exists. Skipping addition.", name)
            return
        
        self.clients[name] = client
        logger.info("Added Telegram client: %s", name)
        
    def start_all(self) -> None:
        """Start all managed Telegram clients."""
        for name, client in self.clients.items():
            is_success = client.start()
            if is_success: 
                logger.info("Started Telegram client: %s", name)
            else:
                logger.warning("Failed to start Telegram client: %s", name)
        logger.info("All Telegram clients have been started.")
    
    def stop_all(self) -> None:
        """Stop all managed Telegram clients."""
        for name, client in self.clients.items():
            is_success = client.stop()
            if is_success:
                logger.info("Stopped Telegram client: %s", name)
            else:
                logger.warning("Failed to stop Telegram client: %s", name)
        logger.info("All Telegram clients have been stopped.")

    def get_client(self, name: str) -> BaseTelegramClient | None:
        """Get a Telegram client by name."""
        try:
            return self.clients[name]
        except KeyError:
            logger.warning("Telegram client not found: %s", name)
            return None