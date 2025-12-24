import logging
import time
import os

import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

from services.tg.client.manager import TelegramClientManager
from services.tg.client import TDLibClient
from services.tg.utils import load_tdlib_account
from services.tg.events.router import EventRouter

# Handlers
from services.tg.events.handlers.chat import PMReplyHandler

# Agent & Models
from services.ai.chat.agent import ChatAgent
from services.ai.chat.openai import OpenAIGPTModel

# Knowledge Base
from services.knowledge_base import KnowledgeBase
from services.knowledge_base.sources.pdf_source import PdfTextSource
from services.knowledge_base.stores.chroma_store import ChromaVectorStore
from services.ai.rag.retriever import Retriever

from config import (
    LIBRARY_PATH, FOLDER_ACCOUNTS, OPENAI_API_KEY, 
    OPENAI_CHAT_MODEL, SYSTEM_PROMPT_FILE, PDF_KNOWLEDGE_BASE, EMBEDDING_MODEL
)
from utils.files import get_account_files
from services.ai.utils import load_prompt

logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def main():
    # 1. Load system prompt
    system_prompt = load_prompt(SYSTEM_PROMPT_FILE)
    logger.info(f"Loaded system prompt: '{system_prompt[:50]}...'")
    
    # 2. Initialize RAG Knowledge Base
    logger.info("Initializing Knowledge Base...")
    
    # Configure OpenAI embedding function
    embedding_function = OpenAIEmbeddingFunction(
        api_key=OPENAI_API_KEY,
        model_name=EMBEDDING_MODEL
    )
    
    # Create ChromaDB client and collection
    chroma_client = chromadb.PersistentClient(path="./data/chroma")
    collection = chroma_client.get_or_create_collection(
        name="company_knowledge",
        metadata={"hnsw:space": "cosine"}, 
        embedding_function=embedding_function
    )
    
    # Wrap collection in store
    vector_store = ChromaVectorStore(collection=collection)
    
    # Create PDF source
    pdf_source = PdfTextSource(file_path=PDF_KNOWLEDGE_BASE)
    
    # Create knowledge base
    kb = KnowledgeBase(
        source=pdf_source,
        store=vector_store,
        chunk_size=500,
        chunk_overlap=50
    )
    
    # Check if we need to rebuild the index
    force_rebuild = os.getenv('REBUILD_KB', 'false').lower() == 'true'
    
    indexed_count = kb.build_index(force_rebuild=force_rebuild)
    
    if indexed_count == 0:
        logger.error("Failed to build knowledge base index!")
        return
    
    logger.info(f"Knowledge base ready: {indexed_count} chunks indexed")
    
    # Create retriever
    retriever = Retriever(kb)
    
    # 3. Initialize AI model
    chat_model = OpenAIGPTModel(
        api_key=OPENAI_API_KEY,
        model=OPENAI_CHAT_MODEL
    )
    
   # 4. Create chat agent (with prompt + RAG)
    chat_agent = ChatAgent(
        chat_model=chat_model,
        system_prompt=system_prompt,
        retriever=retriever,  
        max_history=10
    )
    
    # 5. Create handler (handler только принимает агента)
    pm_handler = PMReplyHandler(
        agent=chat_agent,
        monitored_users={8455168105},  
        escalation_chat_id=5070520571,
    )
    
    # 6. Router
    router = EventRouter()
    router.add_handler(pm_handler)
        
    # 7. Setup Telegram clients
    manager = TelegramClientManager()
    account_files = get_account_files(FOLDER_ACCOUNTS)
    
    for account_file in account_files:
        config = load_tdlib_account(account_file, library_path=LIBRARY_PATH)
        client = TDLibClient(config)
        manager.add_client(config.name, client)
    
    # 8. Start clients
    manager.start_all()
    
    for name, client in manager.clients.items():
        client.listen(router)
        logger.info(f"Client '{name}' connected to router")
        
    # 9. Run
    logger.info("Bot is running. Press Ctrl+C to stop.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping all clients...")
        manager.stop_all()
        logger.info("Program terminated.")

if __name__ == "__main__":
    main()