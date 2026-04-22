import asyncio
import uuid

from src.agents.da_agent.graph import create_data_analysis_agent


async def app():
    agent = await create_data_analysis_agent()
    print("Data Analysis Agent ready. Type 'exit' or 'quit' to stop.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        # Use a unique thread ID per invocation (stateless conversation)
        response = await agent.ainvoke(
            {"messages": user_input},
            config={"configurable": {"thread_id": str(uuid.uuid4())}},
        )
        print(f"Agent: {response['messages'][-1].content}\n")


if __name__ == "__main__":
    asyncio.run(app())


