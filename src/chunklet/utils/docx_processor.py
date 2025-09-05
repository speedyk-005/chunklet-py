import regex as re
from pathlib import Path
    
class DOCXProcessor:
    """
    A utility for extracting text content from DOCX files.

    This processor converts DOCX documents into Markdown format using the
    `mammoth` library, and then performs additional cleanup on the resulting
    Markdown text.
    """
    def extract_text(self, docx_path: str) -> str:
        """
        Extracts text from a DOCX file and converts it to Markdown.

        This method uses the `mammoth` library to perform the conversion and
        then applies a regex-based cleanup to remove unnecessary escape
        characters from the Markdown output.

        Args:
            docx_path (str): The absolute path to the DOCX file.

        Returns:
            str: The extracted and cleaned content of the DOCX file in Markdown format.
        """
        try:
            import mammoth
        except ImportError:
            raise ImportError(
                "The 'mammoth' library is not installed. "
                "Please install it with 'pip install mammoth' or install the document processing extras "
                "with 'pip install 'chunklet-py[document]''"
            )

        def ignore_image(image):
            return []
    
        # Resolve absolute path
        docx_path = str(Path(docx_path).resolve())
        
        # Open document and convert to Markdown while removing image syntax
        with open(docx_path, "rb") as docx_file:
            result = mammoth.convert_to_markdown(docx_file, convert_image=ignore_image)
            markdown_content = result.value
        
        
        
        # Simpler escape removal
        markdown_content = re.sub(r'\\(\p{P})', r'\1', markdown_content)
        
        return markdown_content


# Usage Example
def main():
    # Path to the DOCX file
    docx_path = "samples/Lorem.docx"
    
    processor = DOCXProcessor()
    
    # Extract text
    content = processor.extract_text(docx_path)
    
    # Print sections to demonstrate conversion
    print("=== Content ===")
    print(content)
    
# Run the script
if __name__ == "__main__":
    main()
