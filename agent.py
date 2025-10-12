from dotenv import load_dotenv

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, ChatContext
from livekit.plugins import (
    noise_cancellation,
)
from livekit.plugins import google
from prompts import AGENT_INSTRUCTION, SESSION_INSTRUCTION
from mem0 import AsyncMemoryClient
import logging
import json
import os
load_dotenv()

class Assistant(Agent):
    def __init__(self, chat_ctx=None) -> None:
        super().__init__(
            instructions=AGENT_INSTRUCTION,
            llm=google.beta.realtime.RealtimeModel(
                voice="aoede",
                temperature=0.3,
            ),
            chat_ctx=chat_ctx
        )

async def entrypoint(ctx: agents.JobContext):

    async def shutdown_hook(chat_ctx: ChatContext, memo: AsyncMemoryClient, memory_str: str):
        logging.info("Shutting down...")

        messages_formatted = []
        logging.info(f"Chat context messages: {chat_ctx.items}")

        for item in chat_ctx.items:  # Fixed typo: 'iteam' -> 'item'
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
            content=f"The user name is {user_name}, and this is relevant context about him {memory_str}",  # Fixed typo: 'relvant' -> 'relevant'
        )

    await session.start(
        room=ctx.room,
        agent=Assistant(chat_ctx=initial_ctx),
        room_input_options=RoomInputOptions(
            # LiveKit Cloud enhanced noise cancellation
            # - If self-hosting, omit this parameter
            # - For telephony applications, use `BVCTelephony` for best results
            video_enabled=True,
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await ctx.connect()

    await session.generate_reply(
        instructions=SESSION_INSTRUCTION,
    )
    
    # Fixed: Add the shutdown callback properly
    ctx.add_shutdown_callback(lambda: shutdown_hook(session._agent.chat_ctx, memo, memory_str))


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))