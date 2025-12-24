import time
import logging
    
# Configure logging    
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)    

from services.tg.utils import load_tdlib_account
from services.tg.client import TDLibClient
from services.tg.client.manager import TelegramClientManager

from config import LIBRARY_PATH, FOLDER_ACCOUNTS
from utils.files import get_account_files

logger = logging.getLogger(__name__)

def main():
    # Initialize the Telegram client manager
    manager = TelegramClientManager()

    # Get all account config files
    account_files = get_account_files(FOLDER_ACCOUNTS)
    logger.info(f"Found {len(account_files)} account files: {account_files}")
    
    for account_file in account_files:
        logger.info(f"Loading account from: {account_file}")
        # Load account configuration
        config = load_tdlib_account(
            account_file, 
            library_path=LIBRARY_PATH, 
            tdlib_verbosity=1
        )
        logger.info(f"Loaded config for account: {config.name}")
        
        # Create a TDLib client for the account
        client = TDLibClient(config)

        # Add the client to the manager
        manager.add_client(config.name, client)     

    # Start all clients
    manager.start_all()

    # Wait for 5 seconds
    time.sleep(5)
    
    # Example operation: get a client info from each client
    # for name in manager.clients.keys():
    #     client = manager.get_client(name)
    #     if client:
    #         me = client.get_me()
    #         logger.info(f"Client '{name}' info: {me}")
    #     else:
    #         logger.warning(f"Client '{name}' is not available.")
            
    # Wait for 5 seconds        
    time.sleep(5)
    
    # Example operation: send a message from each client
    for name in manager.clients.keys():
        client = manager.get_client(name)
        if client:
            try:
                chat_id = '8455168105'  # Replace with a valid chat ID
                message_text = f"Hello from **{name}**! This is a <b>test message.</b>"
                res = client.send_message(chat_id, message_text, 'html')
                logger.info(f"Client '{name}' sent message to chat {chat_id}")
            except Exception as e:
                logger.error(f"Client '{name}' failed to send message: {e}")
        else:
            logger.warning(f"Client '{name}' is not available.")
        
    # Wait for 5 seconds
    time.sleep(5)

    # Example operation: get chat user info from each client
    for name in manager.clients.keys():    
        client = manager.get_client(name)
        if client:
            try:
                user_id = 468331874  # Replace with a valid user ID
                user_info = client.get_user(user_id)
                logger.info(f"Client '{name}' user info: {user_info}")
            except Exception as e:
                logger.error(f"Client '{name}' failed to get user info: {e}")
    
    # Wait for 5 seconds
    time.sleep(5)
    
    # Example operation: get chat history from each client
    for name in manager.clients.keys():    
        client = manager.get_client(name)
        if client:
            try:
                chat_peer = '5070520571'  # Replace with a valid chat ID
                history = client.get_history(chat_peer, limit=5)
                logger.info(f"Client '{name}' chat history: {history}")
            except Exception as e:
                logger.error(f"Client '{name}' failed to get chat history: {e}")
                
    # Wait for 5 seconds
    time.sleep(5)
    
    # Example operation: get chat from each client
    for name in manager.clients.keys():    
        client = manager.get_client(name)
        if client:
            try:
                chat_peer = '2696414403'  # Replace with a valid chat ID
                chat = client.get_chat(chat_peer)
                logger.info(f"Client '{name}' chat info: {chat}")
            except Exception as e:
                logger.error(f"Client '{name}' failed to get chat info: {e}")
    
    # Stop all clients
    manager.stop_all()
    
if __name__ == "__main__":
    main()