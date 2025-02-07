from typing import Annotated, List
from typing_extensions import TypedDict
from .parsers import PageSummary, SearchResult, VerificationResult
from langgraph.graph.message import add_messages


class State(TypedDict):
    messages: Annotated[list, add_messages]
    pdf_paths: List[str]
    uploaded_files: List[str]
    query: str
    extracted_pages: List[dict]
    summarized_pages: List[PageSummary]
    search_results: List[SearchResult]
    verified_results: List[VerificationResult]
