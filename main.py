from praisonaiagents import PraisonAIAgents
from agents.agents import Consultant, Analyst, Auditor
from tasks.tasks import consultation, create_report_task
import asyncio

"""
# Create and start the workflow
agents = PraisonAIAgents(
    agents=[Analyst, Auditor],
    tasks=analysis + [report],
    #memory=True,
    verbose=1,
    process="sequential",
)

result = agents.start()

"""

async def main():
    report_task = await create_report_task()
    print(report_task)

    """
    print("hi\n\n")

    # Create and start the workflow
    agents = PraisonAIAgents(
        agents=[Auditor],
        tasks= [report_task],
        verbose=True,
    )

    results = await agents.start()
    print(f"Tasks Results: {results}")
    """

# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())
