"""
Example integration of RAG system with the existing agent.

This shows how to modify agent.py to include document retrieval
for enhanced responses with company-specific information.
"""

from dotenv import load_dotenv

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, ChatContext
from livekit.plugins import (
    noise_cancellation,
)
from livekit.plugins import google
from prompts import AGENT_INSTRUCTION, SESSION_INSTRUCTION
from mem0 import AsyncMemoryClient

# RAG imports
from rag.vector_store import CompanyKnowledgeBase
from rag.retrieval_system import SmartRetriever

import logging
import json
import os
load_dotenv()


class AssistantWithRAG(Agent):
    """Enhanced Assistant with RAG capabilities."""
    
    def __init__(self, chat_ctx=None, knowledge_base=None) -> None:
        # Initialize RAG components
        self.knowledge_base = knowledge_base
        self.retriever = SmartRetriever(knowledge_base) if knowledge_base else None
        
        super().__init__(
            instructions=AGENT_INSTRUCTION,
            llm=google.beta.realtime.RealtimeModel(
                voice="aoede",
                temperature=0.3,
            ),
            chat_ctx=chat_ctx
        )
    
    async def on_user_message(self, message: str) -> None:
        """Override to add RAG context before processing."""
        
        if self.retriever:
            try:
                # Retrieve relevant company information
                company_context = self.retriever.retrieve_context(
                    message, 
                    max_context_length=1500  # Limit context size
                )
                
                if company_context:
                    # Add company context to chat before processing
                    context_message = (
                        f"[COMPANY INFORMATION]\n{company_context}\n"
                        f"[END COMPANY INFORMATION]\n\n"
                        f"Use the above company information to provide accurate, "
                        f"specific answers. If the information is not in the company "
                        f"documents, clearly state that you don't have that specific information."
                    )
                    
                    # Add context as system message
                    self.chat_ctx.add_message(role="system", content=context_message)
                    
                    logging.info(f"Added RAG context ({len(company_context)} chars) for query: {message[:50]}...")
                
            except Exception as e:
                logging.error(f"RAG retrieval failed: {e}")
                # Continue without RAG context
        
        # Process message normally with enhanced context
        await super().on_user_message(message)


async def entrypoint(ctx: agents.JobContext):
    
    async def shutdown_hook(chat_ctx: ChatContext, memo: AsyncMemoryClient, memory_str: str):
        logging.info("Shutting down...")

        messages_formatted = []
        logging.info(f"Chat context messages: {chat_ctx.items}")

        for item in chat_ctx.items:
            content_str = ''.join(item.content) if isinstance(item.content, list) else str(item.content)

            if memory_str and memory_str in content_str:
                continue

            if item.role in ['user', 'assistant']:
                messages_formatted.append({
                    "role": item.role,
                    "content": content_str.strip()
                })
        
        logging.info(f"Messages formatted to add to memory: {messages_formatted}")
        await memo.add(messages_formatted, user_id="kundan")
        logging.info("Chat context Saved to Memory, added successfully")

    session = AgentSession()

    memo = AsyncMemoryClient()
    user_name = 'Kundan'

    # Initialize RAG system
    knowledge_base = None
    try:
        knowledge_base = CompanyKnowledgeBase()
        
        # Check if knowledge base has data
        stats = knowledge_base.get_collection_stats()
        total_docs = sum(stats.values())
        
        if total_docs > 0:
            logging.info(f"RAG system initialized with {total_docs} documents")
        else:
            logging.warning("RAG system initialized but no documents found. Run setup_knowledge_base.py first.")
            
    except Exception as e:
        logging.error(f"RAG system initialization failed: {e}")
        logging.info("Continuing without RAG capabilities")
        knowledge_base = None

    # Get user memories
    results = await memo.get_all(user_id=user_name)
    initial_ctx = ChatContext()
    memory_str = ''

    if results:
        memories = [
            {
                "memory": result["memory"],
                "updated_at": result["updated_at"]
            }
            for result in results
        ]
        memory_str = json.dumps(memories)
        logging.info(f"Memories: {memory_str}")
        initial_ctx.add_message(
            role="system",
            content=f"The user name is {user_name}, and this is relevant context about him {memory_str}",
        )

    # Add RAG system context if available
    if knowledge_base:
        rag_context = (
            "You have access to company documents including FAQ, product details, "
            "and order information. When users ask about company-specific topics, "
            "you will receive relevant information from these documents to provide "
            "accurate, up-to-date responses. Always prioritize information from "
            "company documents over general knowledge when available."
        )
        initial_ctx.add_message(role="system", content=rag_context)

    # Start session with enhanced assistant
    await session.start(
        room=ctx.room,
        agent=AssistantWithRAG(chat_ctx=initial_ctx, knowledge_base=knowledge_base),
        room_input_options=RoomInputOptions(
            video_enabled=True,
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await ctx.connect()

    await session.generate_reply(
        instructions=SESSION_INSTRUCTION,
    )
    
    # Add shutdown callback
    ctx.add_shutdown_callback(lambda: shutdown_hook(session._agent.chat_ctx, memo, memory_str))


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))