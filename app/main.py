"""
main.py
-------
Entry point for the ToolPilot agent pipeline.
Provides the run() coroutine used by both the CLI and the MCP server.
"""
import asyncio
from app.agent.planner import plan_task
from app.agent.executor import execute


async def run(query: str, history: list[dict] | None = None) -> tuple[dict, str, list[dict]]:
    """Run the full agent pipeline. Returns (plan, result, tool_statuses)."""
    plan = await plan_task(query, history=history)
    result, tool_statuses = await execute(plan)
    return plan, result, tool_statuses


if __name__ == "__main__":
    query = input("Enter your query: ")
    plan, result, statuses = asyncio.run(run(query))
    print("\nPlan:", plan)
    for s in statuses:
        print(s["status"])
    print("\nResult:", result)
