import asyncio

from tools.llm import llm
from tools.tools import pdf_tool, normalizer_tool
from .parsers import SearchResult, input_parser, summary_parser, search_result_list_parser, verification_parser
from .state import State

import asyncio
import logging
from tools.llm import llm
from tools.tools import pdf_tool, normalizer_tool
from .parsers import SearchResult, input_parser, summary_parser, search_result_list_parser, verification_parser
from .state import State

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


async def process_input(state: State):
    """
    Extracts the query from user input.
    Checks if input is gibberish using LLM before continuing.
    """
    if not state["messages"]:
        raise ValueError("No input provided.")

    # Extract the user message
    user_message = state["messages"][-1].content.strip()

    if not user_message.strip():
        raise ValueError("User query is empty.")

    # ✅ Check if input is gibberish using LLM
    validation_prompt = (
        f"You are an AI input validator. Determine if the following user input is meaningful:\n\n"
        f"User Input: \"{user_message}\"\n\n"
        f"Respond with ONLY `valid` or `gibberish`."
    )

    response = await llm.ainvoke([{"role": "user", "content": validation_prompt}])
    is_valid = "valid" in response.content.lower()

    if not is_valid:
        logging.warning(f"🚨 Gibberish input detected: {user_message}")  # ✅ Log to terminal
        state["messages"].append({"role": "assistant", "content": "⚠️ Your query seems unclear. Please refine and try again."})
        return {"messages": state["messages"], "input_valid": False}  # ✅ Pass `input_valid = False` to routing

    return {"query": user_message, "input_valid": True}


def process_pdf(state: State):
    pdf_paths = state.get("pdf_paths")
    uploaded_files = state.get("uploaded_files")  # Store user filenames

    if not pdf_paths or not isinstance(pdf_paths, list):
        raise ValueError("No PDF paths found.")
    if not uploaded_files or not isinstance(uploaded_files, list):
        raise ValueError("No uploaded filenames found.")

    extracted_pages = []

    for pdf_path, uploaded_file in zip(pdf_paths, uploaded_files):
        document_name = uploaded_file.name
        # Extract pages
        pdf_result = pdf_tool.invoke({"pdf_path": pdf_path})
        pages = pdf_result.get("pages", [])

        # Store extracted pages with correct document names
        for page in pages:
            extracted_pages.append({
                "document_name": document_name,  # ✅ Correct filename
                "page_number": page["page_number"],
                "content": page["content"]
            })

    return {"extracted_pages": extracted_pages}

async def summarize_page(state: State):
    async def summarize(page_data):
        """Helper function to invoke LLM asynchronously for summarization."""
        document_name = page_data["document_name"]  # ✅ Preserve document name
        page_number = page_data["page_number"]
        content = page_data["content"]

        # Define the prompt
        prompt = (
            f"You are an advanced document summarizer. Summarize the following content from page {page_number} "
            f"of the document '{document_name}'. Your summary should have a heading sentence and three key points. "
            "Ensure that at least one of the points is qualitative and one is quantitative. Each point should reflect "
            "significant facts or insights and be concise.\n\n"
            f'"{content}"\n\n'
            "Please respond using the following structure in valid JSON format:\n"
            f"{summary_parser.get_format_instructions()}"
        )

        # Invoke the LLM and parse the response
        response = await llm.ainvoke([{"role": "user", "content": prompt}])
        parsed_summary = summary_parser.parse(response.content)

        # ✅ Return with `document_name` included
        return {
            "document_name": document_name,  # ✅ Fix: Preserve document name
            "page_number": parsed_summary.page_number,
            "heading_sentence": parsed_summary.heading_sentence,
            "key_points": parsed_summary.key_points,
        }

    # Summarize all pages concurrently
    tasks = [summarize(page_data) for page_data in state["extracted_pages"]]
    summarized_pages = await asyncio.gather(*tasks)

    return {"summarized_pages": summarized_pages}

async def search_summaries(state: State):
    query = state.get("query")
    summaries = state.get("summarized_pages")

    if not query:
        raise ValueError("Query not found.")
    if not summaries:
        raise ValueError("Summaries not found.")

    # ✅ Ensure document names are included in the summaries
    concatenated_summaries = "\n\n".join(
        f"📄 **Document: {summary['document_name']}** | Page {summary['page_number']}:\n"
        f"- **Heading Sentence**: {summary['heading_sentence']}\n"
        f"- **Key Points**:\n"
        f"  1. {summary['key_points'][0]}\n"
        f"  2. {summary['key_points'][1]}\n"
        f"  3. {summary['key_points'][2]}"
        for summary in summaries
    )

    # Define the search prompt
    search_prompt = (
        f"The following are summaries from multiple documents:\n\n"
        f"{concatenated_summaries}\n\n"
        f"Based on the query: \"{query}\", extract the top 10 relevant points from the summary. "
        f"Each point should be associated with exactly one document name and page number as its source. "
        f"Please respond using the following structure in valid JSON format:\n"
        f"{search_result_list_parser.get_format_instructions()}"
    )

    # Use the LLM to perform the search
    response = await llm.ainvoke([{"role": "user", "content": search_prompt}])

    try:
        # ✅ Parse the response using Pydantic
        parsed_results = search_result_list_parser.parse(response.content)

        # ✅ Attach the correct `document_name` to each search result
        enriched_results = []
        for result in parsed_results.results:
            matching_summary = next(
                (s for s in summaries if s["page_number"] == result.claimed_page), None
            )
            if matching_summary:
                result_data = {
                    "document_name": matching_summary["document_name"],  # ✅ Add document name
                    "content": result.content,
                    "claimed_page": result.claimed_page,
                }
                enriched_results.append(result_data)

        return {"search_results": enriched_results}

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

    async def verify(result):
        document_name = result["document_name"]  # ✅ Access `document_name`
        claimed_page = result["claimed_page"]
        content = result["content"]

        # Find the matching page in extracted_pages
        matching_page = next(
            (page for page in extracted_pages if page["page_number"] == claimed_page and page["document_name"] == document_name),
            None
        )
        if not matching_page:
            return None  # If no matching page is found, skip verification

        raw_content = normalizer_tool.normalize(matching_page["content"])
        # Define the verification prompt
        verification_prompt = (
            f"Does the following summary originate from the content of Page {claimed_page} in the document '{document_name}'?\n\n"
            f"Summary:\n{content}\n\n"
            f"Page {claimed_page} Content:\n{raw_content}\n\n"
            f"Check the following:\n"
            f"- Does the numerical data match exactly?\n"
            f"- Are qualitative descriptions consistent and supported by the content?\n"
            f"- Ensure no hallucination.\n\n"
            f"Respond using valid JSON format:\n"
            f"{verification_parser.get_format_instructions()}"
        )

        # Call the LLM for verification
        response = await llm.ainvoke([{"role": "user", "content": verification_prompt}])

        try:
            # Parse the verification response
            verification_result = verification_parser.parse(response.content)
            cleaned_content = normalizer_tool.normalize(content) 

            if verification_result.valid:
                return {
                    "content": cleaned_content,
                    "source": f"📄 {document_name} | Page {claimed_page}",
                    "explanation": verification_result.explanation,
                }
        except Exception as e:
            print(f"Error parsing verification result for {document_name} Page {claimed_page}: {e}")
        return None

    # Verify all search results asynchronously
    tasks = [verify(result) for result in search_results]
    all_verified_points = await asyncio.gather(*tasks)

    # Filter out None values and format the results
    verified_results = [point for point in all_verified_points if point]

    # Present the verified results
    formatted_results = "\n\n".join(
        f"💡 **Info:** {result['content']}  \n"
        f"🔍 **Source:** {result['source']}  \n"
        f"📌 **Reasoning:** {result['explanation']}"
        for result in verified_results
    )


    return {
        "messages": [
            {"role": "assistant", "content": f"Verified Results:\n\n{formatted_results}"}
        ],
        "verified_results": verified_results,
    }
