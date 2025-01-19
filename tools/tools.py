from langchain_community.document_loaders import PDFPlumberLoader
from typing import Dict, Any
from pydantic import BaseModel
import pdfplumber

class PDFPlumberTool(BaseModel):
    """Wrapper for PDFPlumber document processing."""
    name: str = "PDFPlumberTool"
    description: str = "Extract text and metadata from PDF documents using PDFPlumber."

    def run(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract text and metadata from a PDF file, split by pages, 
        append results, and save to an output file.

        Args:
            pdf_path (str): Path to the PDF file
            output_file (str): Path to the output text file to save results

        Returns:
            dict: Dictionary containing extracted text and metadata from the PDF
        """
        results = {
            'pages': [],
            'metadata': None
        }
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Add metadata
                results['metadata'] = pdf.metadata
                
                # Extract text page by page
                with open("output.txt", "w", encoding="utf-8") as out_file:
                    for i, page in enumerate(pdf.pages[:9]): # Maximum 10 concurrent agents running
                        page_text = page.extract_text()
                        page_metadata = {
                            'page_number': i + 1,
                            'width': page.width,
                            'height': page.height
                        }

                        # Append to results
                        results['pages'].append({
                            'page_number': i + 1,
                            'content': page_text,
                            'metadata': page_metadata
                        })
                        
                        # Write to output file
                        out_file.write(f"Page {i + 1}:\n")
                        out_file.write(page_text or "[No Text Found]\n")
                        out_file.write("=" * 50 + "\n")
            
            print(f"PDF processed successfully. Output saved to output.txt")
        
        except Exception as e:
            print(f"An error occurred: {e}")
            results['error'] = str(e)
        
        return results

# Example usage:
# pdf_tool = PDFPlumberTool()
# output = pdf_tool.run("example.pdf", "output.txt")
# print(output)
