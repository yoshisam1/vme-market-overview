from praisonaiagents import Task
from agents.agents import Consultant, Analyst, Auditor, Router
from tools.tools import PDFPlumberTool

# ----------------------------

routing_task = Task(
    name="pdf_routing_task",
    description="Route each page of the PDF for analysis",
    expected_output="Routing decision for each page",
    agent=Router,  # New Router agent to handle routing
    is_start=True,
    task_type="decision",
    condition={
        "pass": "analysis",
        "fail": ["error_handling_task"]
    }
)

# ----------------------------

consultation = Task(
    name="requirement_gathering_task",
    description="Write a structured research",
    expected_output="A structured research plan",
    agent=Consultant
)

# ----------------------------

pdf_tool = PDFPlumberTool() # Create the PDF tool instance
pdf_result = pdf_tool.run("data/Source1.pdf")  # Assuming this returns a dictionary of pages

analysis = []

for page in pdf_result['pages']:
    page_analysis_task = Task(
        name=f"pdf_analysis_task_page_{page['page_number']}",
        description=f"Analyze page {page['page_number']} of the PDF document. Content: {page['content']}",
        #context=, what if the context is all the pages before it? (need to check if it adds token size) <-- i think by enabling memory in the driver tool it already includes this, but makes it makes things increasingly super slow
        expected_output="A structured summary of the page content with key findings",
        agent=Analyst,
        is_start=True,
        async_execution=True
    )
    analysis.append(page_analysis_task)

# ----------------------------

report = Task(
    name="report_making_task",
    description="Create a structured report of the key findings of the whole document.",
    context=analysis,
    expected_output="A structured text report.",
    agent=Auditor
)
