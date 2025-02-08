import asyncio
from graph import process_input, process_pdf, summarize_page, search_summaries, verify_results
from graph import State
from tools import llm, pdf_tool
from langgraph.graph import StateGraph, START, END

def route_based_on_input(state: State) -> str:
    if state.get("input_valid"):
        return "process_pdf"
    else:
        # ❌ If gibberish detected, return an error message and end execution
        state["messages"].append({
            "role": "assistant",
            "content": "⚠️ Your query seems unclear or gibberish. Please rephrase it and try again."
        })
        return END  # ✅ Directly go to END to avoid infinite loop


# Initialize LangGraph
graph_builder = StateGraph(State)

# Add nodes to the graph
graph_builder.add_node("process_input", process_input)
graph_builder.add_node("process_pdf", process_pdf)
graph_builder.add_node("summarize_page", summarize_page)
graph_builder.add_node("search_summaries", search_summaries)
graph_builder.add_node("verify_results", verify_results)

graph_builder.add_edge(START, "process_input")
graph_builder.add_conditional_edges("process_input", route_based_on_input)
graph_builder.add_edge("process_pdf", "summarize_page")
graph_builder.add_edge("summarize_page", "search_summaries")
graph_builder.add_edge("search_summaries", "verify_results")
graph_builder.add_edge("verify_results", END)

# Compile the graph
graph = graph_builder.compile()

# ✅ **Updated Function to Handle Multiple PDFs**
async def process_query(pdf_paths: list, uploaded_filenames: list[str], user_query: str):
    """Handles the processing of multiple PDF files with a user query."""
    """Handles the processing of multiple PDF files with their original filenames."""
    if not pdf_paths or not isinstance(pdf_paths, list):
        raise ValueError("No PDF paths provided.")
    if not uploaded_filenames or not isinstance(uploaded_filenames, list):
        raise ValueError("No uploaded filenames provided.")

    initial_state = {
        "messages": [{"role": "user", "content": user_query}],
        "pdf_paths": pdf_paths,  # ✅ Updated to accept a list of PDF paths
        "uploaded_files": uploaded_filenames,
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
            pdf_paths = input("Enter PDF file paths (comma-separated): ").split(",")
            results = asyncio.run(process_query(pdf_paths, user_input))

            for res in results:
                print(f"Assistant: {res}")

        except Exception as e:
            print(f"Error: {e}")
            break
