from sutram import create_provider, DictCache, Session
import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

async def main():
    # Create a cached provider
    cache = DictCache()
    provider = create_provider(
        name="openrouter",
        model="nvidia/nemotron-3-super-120b-a12b:free",
        api_key=os.environ["OPEN_ROUTER_API_KEY"],
        cache=cache,
    )

    # Test 1: Single call
    print("--- Test 1: call_llm ---")
    result = provider.call_llm("Say hello in one sentence.")
    print(result)

    # Test 2: Cache hit
    print("\n--- Test 2: Cache hit ---")
    result = provider.call_llm("Say hello in one sentence.")
    print(result)

    # Test 3: Multi-turn with Session
    print("\n--- Test 3: Session chat ---")
    session = Session(system_prompt="You are a pirate. Respond in pirate speak.")
    session.add_user_message("What's 2+2?")
    result = provider.chat(session.get_messages())
    print(result)

    # Test 4: Async call
    print("\n--- Test 4: Async call ---")
    result = await provider.acall_llm("Say goodbye in one sentence.")
    print(result)

    print("\n✅ All tests passed!")

if __name__ == "__main__":
    asyncio.run(main())