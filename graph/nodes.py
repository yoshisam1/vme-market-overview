import asyncio

from tools.llm import llm
from tools.tools import pdf_tool
from .parsers import SearchResult, input_parser, summary_parser, search_result_list_parser, verification_parser
from .state import State


async def process_input(state: State):
    """
    Extracts the query from user input.
    Streamlit already provides `pdf_path`, so we no longer extract it.
    """
    if not state["messages"]:
        raise ValueError("No input provided.")

    # Extract the user message
    user_message = state["messages"][-1].content

    if not user_message.strip():
        raise ValueError("User query is empty.")

    return {"query": user_message}  # Only return query; Streamlit provides `pdf_path`

def process_pdf(state: State):
    pdf_path = state.get("pdf_path")
    if not pdf_path:
        raise ValueError("PDF path not found.")

    # Use the PDF tool to extract the pages
    pdf_result = pdf_tool.invoke({"pdf_path": pdf_path})
    pages = pdf_result.get("pages", [])

    # Attach both content and page number for processing
    extracted_pages = [
        {"page_number": page["page_number"], "content": page["content"]}
        for page in pages
    ]
    return {"extracted_pages": extracted_pages}

async def summarize_page(state: State):
    async def summarize(page_data):
        """Helper function to invoke LLM asynchronously for summarization."""
        page_number = page_data["page_number"]
        content = page_data["content"]

        # Define the prompt
        prompt = (
            f"You are an advanced document summarizer. Summarize the following content from page {page_number} of a document. "
            "Your summary should have a heading sentence and three key points. Ensure that at least one of the points is qualitative "
            "and one is quantitative. Each point should reflect significant facts or insights and be concise. Below is the content for summarization:\n\n"
            f'"{content}"\n\n'
            "Please respond using the following structure in valid JSON format:\n"
            f"{summary_parser.get_format_instructions()}"
        )

        # Invoke the LLM and parse the response
        response = await llm.ainvoke([{"role": "user", "content": prompt}])
        return summary_parser.parse(response.content)

    # Summarize all pages concurrently
    tasks = [summarize(page_data) for page_data in state["extracted_pages"]]
    summaries = await asyncio.gather(*tasks)

    # Prepare summarized pages
    summarized_pages = [
        {
            "page_number": summary.page_number,
            "heading_sentence": summary.heading_sentence,
            "key_points": summary.key_points,
        }
        for summary in summaries
    ]
    return {"summarized_pages": summarized_pages}

async def search_summaries(state: State):
    query = state.get("query")
    summaries = state.get("summarized_pages")

    if not query:
        raise ValueError("Query not found.")
    if not summaries:
        raise ValueError("Summaries not found.")

    # Combine summaries into a text block
    concatenated_summaries = "\n\n".join(
        f"Page {summary['page_number']}:\n"
        f"- **Heading Sentence**: {summary['heading_sentence']}\n"
        f"- **Key Points**:\n"
        f"  1. {summary['key_points'][0]}\n"
        f"  2. {summary['key_points'][1]}\n"
        f"  3. {summary['key_points'][2]}"
        for summary in summaries
    )

    # Define the search prompt
    search_prompt = (
        f"The following are summaries from a document:\n\n"
        f"{concatenated_summaries}\n\n"
        f"Based on the query: \"{query}\", extract the top 10 relevant points from the summary. "
        f"Each point should be associated with exactly one page number as its source. "
        f"Please respond using the following structure in valid JSON format:\n"
        f"{search_result_list_parser.get_format_instructions()}"
    )

    # Use the LLM to perform the search
    response = await llm.ainvoke([{"role": "user", "content": search_prompt}])
    print("Raw search response:", response.content)

    try:
        # Parse the response using Pydantic
        parsed_results = search_result_list_parser.parse(response.content)
        return {"search_results": parsed_results.results}
    except Exception as e:
        print(f"Error parsing search results: {e}")
        raise ValueError("Failed to parse search results.")

async def verify_results(state: State):
    search_results = state.get("search_results", [])
    extracted_pages = state.get("extracted_pages", [])

    if not search_results:
        raise ValueError("No search results to verify.")
    if not extracted_pages:
        raise ValueError("No extracted pages to verify against.")

    async def verify(result: SearchResult):
        claimed_page = result.claimed_page
        content = result.content

        # Find the matching page in extracted_pages
        matching_page = next(
            (page for page in extracted_pages if page["page_number"] == claimed_page),
            None
        )
        if not matching_page:
            return None  # If no matching page is found, skip verification

        raw_content = matching_page["content"]

        # Define the strict verification prompt
        verification_prompt = (
            f"Does the following summary originate from the content of Page {claimed_page}?\n\n"
            f"Summary:\n{content}\n\n"
            f"Page {claimed_page} Content:\n{raw_content}\n\n"
            f"Check the following:\n"
            f"- Does the numerical data match exactly?\n"
            f"- Are qualitative descriptions consistent and supported by the content?\n"
            f"- Ensure **numbers and currency values are properly formatted**.\n"
            f"- **No broken words or line breaks in numeric data**.\n"
            f"- **Preserve all paragraph and list structures correctly**.\n"
            f"- **Ensure no hallucination or incorrect modifications.**\n\n"
            f"- Ensure there is no hallucination.\n\n"
            f"Respond with the following structure in valid JSON format:\n"
            f"{verification_parser.get_format_instructions()}"
        )

        # Call the LLM for verification
        response = await llm.ainvoke([{"role": "user", "content": verification_prompt}])

        try:
            # Parse the verification response
            verification_result = verification_parser.parse(response.content)

            if verification_result.valid:
                return {
                    "content": content,
                    "source": f"Page {claimed_page}",
                    "explanation": verification_result.explanation,
                }
        except Exception as e:
            print(f"Error parsing verification result for Page {claimed_page}: {e}")
        return None

    # Verify all search results asynchronously
    tasks = [verify(result) for result in search_results]
    all_verified_points = await asyncio.gather(*tasks)

    # Filter out None values and format the results
    verified_results = [point for point in all_verified_points if point]

    # Present the verified results
    formatted_results = "\n\n".join(
        f"{result['content']} (Source: {result['source']})"
        for result in verified_results
    )

    return {
        "messages": [
            {"role": "assistant", "content": f"Verified Results:\n\n{formatted_results}"}
        ],
        "verified_results": verified_results,
    }
