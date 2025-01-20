from praisonaiagents import Agent
from tools.tools import PDFPlumberTool


Router = Agent(
    name="Router",
    role="Input Router",
    goal="Evaluate input and route tasks for each page of the PDF",
    verbose=True
)


# Create multiple agents
Consultant = Agent(
    name="Consultant",
    role="Senior Research Consultant",
    goal="Understand the user/client query and plan a formalized research task description",
    backstory="You are an expert consultant at a financial strategy firm",
    verbose=True,
    llm="gpt-4o-mini",
    markdown=True
)

"""
Analyst = Agent(
    name="Analyst",
    role="Senior Data Analyst",
    goal="Searches and analyze the given documents for relevant data and facts and present it back in a structured format, processing one page at a time.",
    backstory="You are a skilled data analyst with expertise in analyzing and interpreting complex data from reports",
    verbose=True,
    llm="gpt-4",
    tools=[PDFPlumberTool],
    markdown=True
)
"""
Analyst = Agent(
    name="Analyst",
    role="Senior Data Analyst",
    goal="Analyze the given document page by page and present findings",
    backstory="You are a skilled data analyst with expertise in analyzing and interpreting complex data from reports",
    verbose=True,
    llm="gpt-4o-mini",
    #tools=[PDFPlumberTool],
    markdown=True,
    #memory=False,
    #max_rpm=100,
    #use_system_prompt=False,
    #self_reflect=False,
)

Auditor = Agent(
    name="Auditor",
    role="Senior Auditor",
    goal="Your goal is to review the research findings you provided for a specific user query and create the final report.",
    backstory="You are a skilled data analyst with expertise in analyzing and interpreting complex data from reports",
    verbose=True,
    llm="gpt-4o",
    markdown=True,
    memory=False
)
