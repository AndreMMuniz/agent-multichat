import asyncio
import sys
import os

# Adds current directory to path to import modules
sys.path.append(os.getcwd())

from graph import app_graph

async def main():
    inputs = {
        "topic": "Artificial Intelligence",
        "draft": "",
        "reviews": [],
        "is_finished": False,
        "iteration_count": 0
    }
    print("Invoking graph...")
    try:
        result = await app_graph.ainvoke(inputs)
        print("Success result:")
        print(f"Draft: {result.get('draft')}")
        print(f"Reviews: {result.get('reviews')}")
        print(f"Count: {result.get('iteration_count')}")
    except Exception as e:
        print(f"Error executing graph: {e}")

if __name__ == "__main__":
    asyncio.run(main())
