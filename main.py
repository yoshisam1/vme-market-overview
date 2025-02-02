import asyncio
from graph import process_input, process_pdf, summarize_page, search_summaries, verify_results
from graph import State
from tools import llm, pdf_tool
from langgraph.graph import StateGraph, START, END

# Initialize LangGraph
graph_builder = StateGraph(State)

# Add nodes to the graph
graph_builder.add_node("process_input", process_input)
graph_builder.add_node("process_pdf", process_pdf)
graph_builder.add_node("summarize_page", summarize_page)
graph_builder.add_node("search_summaries", search_summaries)
graph_builder.add_node("verify_results", verify_results)

graph_builder.add_edge(START, "process_input")
graph_builder.add_edge("process_input", "process_pdf")
graph_builder.add_edge("process_pdf", "summarize_page")
graph_builder.add_edge("summarize_page", "search_summaries")
graph_builder.add_edge("search_summaries", "verify_results")
graph_builder.add_edge("verify_results", END)

# Compile the graph
graph = graph_builder.compile()


# Function to process the document and query asynchronously
async def process_query(pdf_path: str, user_query: str):
    """Handles the processing of a PDF file with a user query."""
    initial_state = {
        "messages": [{"role": "user", "content": user_query}],
        "pdf_path": pdf_path,
        "query": user_query,
        "extracted_pages": [],
        "summarized_pages": [],
        "search_results": [],
        "verified_results": [],
    }

    results = []
    async for event in graph.astream(initial_state):
        for value in event.values():
            if "messages" in value:
                last_message = value["messages"][-1]
                if isinstance(last_message, dict) and "content" in last_message:
                    results.append(last_message["content"])

    return results


# If running as a standalone script (for testing without Streamlit)
if __name__ == "__main__":
    while True:
        try:
            user_input = input("User: ")
            if user_input.lower() in ["quit", "exit", "q", "bye"]:
                print("Goodbye!")
                break

            # Run asynchronously in CLI
            pdf_path = input("Enter PDF file path: ")
            results = asyncio.run(process_query(pdf_path, user_input))

            for res in results:
                print(f"Assistant: {res}")

        except Exception as e:
            print(f"Error: {e}")
            break
