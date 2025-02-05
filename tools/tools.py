from typing import List, Optional, Type, Dict, Any
from langchain_core.callbacks import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
import pdfplumber, re


# Define input schema for the tool
class PDFPlumberInput(BaseModel):
    pdf_path: str = Field(description="Path to the PDF file to process")


class PDFPlumberTool(BaseTool):
    name: str = "PDFPlumberTool"
    description: str = "Extract text and metadata from PDF documents using PDFPlumber."
    args_schema: Type[BaseModel] = PDFPlumberInput
    return_direct: bool = False

    def detect_page_numbering(self, page_text: str) -> Optional[str]:
        """
        Detect if the page uses Roman or Arabic numbering.

        Args:
            page_text (str): Text content of the page.

        Returns:
            Optional[str]: Detected page number type ("roman", "arabic", or None).
        """
        # Extract potential page number from the text (e.g., top/bottom of the page)
        lines = page_text.splitlines()
        print(lines)
        for line in lines:
            stripped_line = line.strip()
            if stripped_line.isdigit():  # Arabic numerals
                return "arabic"
            elif stripped_line.lower() in ["i", "ii", "iii", "iv", "v", "vi", "vii"]:  # Roman numerals
                return "roman"
        return None  # No numbering detected

    def compute_dynamic_offsets(self, pages: List[Dict[str, Any]]) -> List[int]:
        """
        Compute the dynamic page numbering based on detected Roman and Arabic numbers,
        using "0" for fallback cases where no numbering is detected.

        Args:
            pages (List[Dict[str, Any]]): List of extracted pages.

        Returns:
            List[int]: Adjusted page numbers for each page.
        """
        current_page_number = 1
        numbering_mode = None  # Start without assuming any numbering mode
        adjusted_numbers = []
        for page in pages:
            detected_mode = self.detect_page_numbering(page["content"])

            if detected_mode == "roman" and numbering_mode != "roman":
                # Transition to Roman numbering
                numbering_mode = "roman"
                current_page_number = 1  # Reset numbering for Roman
            elif detected_mode == "arabic" and numbering_mode != "arabic":
                # Transition to Arabic numbering
                numbering_mode = "arabic"
                try:
                    # Attempt to extract the Arabic number from the page content
                    current_page_number = int(page["content"].splitlines()[-1].strip())
                except ValueError:
                    current_page_number = 1  # Default to 1 if parsing fails
            elif detected_mode is None:
                # Fallback: Assign page "0"
                numbering_mode = "fallback"
                adjusted_numbers.append(0)
                continue  # Skip incrementing current_page_number for fallback pages

            adjusted_numbers.append(current_page_number)
            current_page_number += 1
        return adjusted_numbers

    def _run(
        self, pdf_path: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Dict[str, Any]:
        """
        Extract text and metadata from a PDF file, split by pages, and dynamically adjust page numbering.

        Args:
            pdf_path (str): Path to the PDF file.

        Returns:
            dict: Dictionary containing extracted text and metadata from the PDF.
        """
        results = {
            'pages': [],
            'metadata': None
        }

        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Add total pages to metadata
                results['metadata'] = {
                    'total_pages': len(pdf.pages),
                    **(pdf.metadata or {})  # Include existing metadata if available
                }

                # Extract text and page-specific metadata
                extracted_pages = []
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text() or ""
                    word_count = len(page_text.split())  # Count total words in the page

                    # Page-specific metadata
                    page_metadata = {
                        'original_index': i + 1,  # PDF's internal page number
                        'width': page.width,
                        'height': page.height,
                        'word_count': word_count
                    }

                    # Append to extracted pages for further processing
                    results['pages'].append({
                        'page_number': page_metadata["original_index"],
                        'content': page_text,
                        'metadata': page_metadata
                    })

                # Dynamically adjust page numbers (not yet implemented)
                # adjusted_numbers = self.compute_dynamic_offsets(extracted_pages)
                # for page, adjusted_number in zip(extracted_pages, adjusted_numbers):
                #     page['page_number'] = adjusted_number  # Add adjusted number to metadata
                #     results['pages'].append(page)


            print(f"PDF extracted successfully.")
        
        except Exception as e:
            print(f"An error occurred: {e}")
            results['error'] = str(e)
        
        return results

    async def _arun(
        self,
        pdf_path: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Dict[str, Any]:
        """
        Asynchronous version of _run.

        Args:
            pdf_path (str): Path to the PDF file.

        Returns:
            dict: Dictionary containing extracted text and metadata from the PDF.
        """
        return self._run(pdf_path, run_manager=run_manager.get_sync())

class TextNormalizer:
    """
    A utility class for normalizing text formatting issues.
    Ensures:
    - Proper number formatting
    - Removal of unnecessary newlines
    - Correct spacing between words and numbers
    """

    @staticmethod
    def normalize(text: str) -> str:
        """
        Cleans and normalizes text by:
        - Fixing broken number formatting
        - Removing unnecessary line breaks
        - Ensuring correct word spacing
        - Correcting broken words like "b i l l i o n"
        """
        if not text:
            return ""

        # Fix broken commas in numbers
        text = re.sub(r"(\d+),\s*\n(\d+)", r"\1,\2", text)  

        # Fix numbers broken by newlines
        text = re.sub(r"(\d+)\s*\n(\d+)", r"\1\2", text)    

        # Remove unintended newlines
        text = re.sub(r"\s*\n\s*", " ", text)               

        # Fix cases where "b i l l i o n" is incorrectly spaced
        text = re.sub(r"\b(\w) (\w) (\w) (\w) (\w) (\w) (\w)\b", r"\1\2\3\4\5\6\7", text)

        return text.strip()

normalizer_tool = TextNormalizer()
pdf_tool = PDFPlumberTool()


"""
# Example usage
pdf_tool = PDFPlumberTool()
output = pdf_tool.invoke({"pdf_path": "data/Source1.pdf"})
print(output)
"""
