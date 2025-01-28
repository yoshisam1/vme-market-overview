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

async def astream_graph_updates(user_input: str):
    initial_state = {
        "messages": [{"role": "user", "content": user_input}],
        "pdf_path": "",
        "query": "",
        "extracted_pages": [],
        "summarized_pages": [],
    }
    async for event in graph.astream(initial_state):
        for value in event.values():
            if "messages" in value:
                last_message = value["messages"][-1]
                if isinstance(last_message, dict) and "content" in last_message:
                    print("Assistant:", last_message["content"])

if __name__ == "__main__":
    while True:
        try:
            user_input = input("User: ")
            if user_input.lower() in ["quit", "exit", "q", "bye"]:
                print("Goodbye!")
                break
            asyncio.run(astream_graph_updates(user_input))
        except Exception as e:
            print(f"Error: {e}")
            break
