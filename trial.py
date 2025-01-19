from praisonaiagents import Agent, Task, PraisonAIAgents

# Create multiple agents
researcher = Agent(
    name="Researcher",
    role="Senior Research Analyst",
    goal="Uncover cutting-edge developments in AI",
    backstory="You are an expert at a technology research group",
    verbose=True,
    llm="gpt-4o",
    markdown=True
)

writer = Agent(
    name="Writer",
    role="Tech Content Strategist",
    goal="Craft compelling content on tech advancements",
    backstory="You are a content strategist",
    llm="gpt-4o",
    markdown=True
)

# Define multiple tasks
task1 = Task(
    name="research_task",
    description="Analyze 2024's AI advancements",
    expected_output="A detailed report",
    agent=researcher
)

task2 = Task(
    name="writing_task",
    description="Create a blog post about AI advancements",
    expected_output="A blog post",
    agent=writer
)

# Run with hierarchical process
agents = PraisonAIAgents(
    agents=[researcher, writer],
    tasks=[task1, task2],
    verbose=False,
    process="hierarchical",
    manager_llm="gpt-4o"
)

result = agents.start()
print(result)
