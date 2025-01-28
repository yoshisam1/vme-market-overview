from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser
from typing import List


# Define the Pydantic model for structured output
class InputData(BaseModel):
    pdf_path: str = Field(description="The path to the PDF file.")
    query: str = Field(description="The user's query or purpose.")
class PageSummary(BaseModel):
    page_number: int = Field(description="The page number of the PDF.")
    heading_sentence: str = Field(description="A single sentence summarizing the main idea of the page.")
    key_points: List[str] = Field(description="Three key points summarizing the content.")
class SearchResult(BaseModel):
    content: str = Field(description="The relevant information extracted from the summaries.")
    claimed_page: int = Field(description="The single page where the information originates.")
class SearchResultList(BaseModel):
    results: List[SearchResult] = Field(description="A list of search results.")
class VerificationResult(BaseModel):
    valid: bool = Field(description="Indicates whether the summary matches the page content.")
    explanation: str = Field(description="Provides the reason for the validity of the match.")

# Create parsers
input_parser = PydanticOutputParser(pydantic_object=InputData)
summary_parser = PydanticOutputParser(pydantic_object=PageSummary)
search_result_parser = PydanticOutputParser(pydantic_object=SearchResult)
search_result_list_parser = PydanticOutputParser(pydantic_object=SearchResultList)
verification_parser = PydanticOutputParser(pydantic_object=VerificationResult)
