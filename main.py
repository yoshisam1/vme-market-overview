from praisonaiagents import PraisonAIAgents
from agents.agents import Consultant, Analyst, Auditor
from tasks.tasks import consultation, analysis, report
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
    # Create and start the workflow
    workflow = PraisonAIAgents(
        agents=[Analyst, Auditor],
        tasks= analysis + [report],
        verbose=3,
        process="workflow"
    )

    results = await workflow.astart()

# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())
