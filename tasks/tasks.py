from praisonaiagents import Task
from agents.agents import Consultant, Analyst, Auditor, Router
from tools.tools import PDFPlumberTool
import asyncio

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
pdf_pages = pdf_tool.run("data/Source1.pdf")  # Assuming this returns a dictionary of pages

async def process_pdf_pages():
    raw_pages = [
        Task(
            name=f"pdf_analysis_task_page_{page['page_number']}",
            description=f"Analyze page {page['page_number']} of the PDF document. Content: {page['content']}",
            #context=, what if the context is all the pages before it? (need to check if it adds token size) <-- i think by enabling memory in the driver tool it already includes this, but makes it makes things increasingly super slow
            expected_output="A structured summary of the page content with key findings",
            async_execution=True # This doesn't rlly matter if we already use asyncio.gather?
        ) for page in pdf_pages['pages']
    ]

    results = await asyncio.gather(
        *[Analyst.achat(page.description) for page in raw_pages]
    )

    return results

# ----------------------------

async def create_report_task():
    results = await process_pdf_pages()
    long_results = "\n\n".join(results)

    report = Task(
        name="report_making_task",
        description=f"Create a structured summary report of the key findings of the whole document, maximum 3 parapgrahs. The analysis and summary of all the pages is: {long_results}",
        expected_output="A structured text report.",
        agent=Auditor,
        async_execution=True
    )

    final_report = await Auditor.achat(report.description)

    return final_report