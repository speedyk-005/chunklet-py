from collections.abc import Generator
from typing import Any

from chunklet.document_chunker.processors.base_processor import BaseProcessor


class EmlProcessor(BaseProcessor):
    """
    Processor class for extracting text and metadata from EML (RFC 822) email files.

    Text content is extracted from the decoded plain-text body of the email.

    This processor focuses on extracting commonly used **email header metadata**
    together with the names of attached and inline files. The extracted metadata
    corresponds to fields available from the parsed mail object returned by the
    underlying email parser. Not all available message fields are extracted.

    For more details on the parsed mail object and the available fields, refer to
    the MailParser documentation:

    https://nodemailer.com/extras/mailparser/#returned-mail-object
    """

    def __init__(self, file_path: str):
        """
        Initializes the EmlProcessor with a path to the EML file
        and parses the email into memory.

        Args:
            file_path: Path to the EML file.
        """
        super().__init__(file_path)
        try:
            from mailparse import EmailDecode
        except ImportError as e:  # pragma: no cover
            raise ImportError(
                "The 'mailparse' library is not installed. "
                "Please install it with 'pip install mailparse>=1.0.1'."
            ) from e
        self._parsed = EmailDecode.open(self.file_path)

    def extract_metadata(self) -> dict[str, Any]:
        """
        Extracts commonly used email metadata from the parsed message.

        Returns:
            A dictionary containing metadata fields.
                - source
                - subject
                - from
                - to
                - cc
                - date
                - message_id
                - in_reply_to
                - references
                - attachment_names
                - inline_names
        """
        return {
            "source": str(self.file_path),
            "subject": self._parsed.get("subject"),
            "from": self._parsed.get("from"),
            "to": self._parsed.get("to", []),
            "cc": self._parsed.get("cc", []),
            "date": self._parsed.get("date"),
            "message_id": self._parsed.get("message-id"),
            "in_reply_to": self._parsed.get("in-reply-to"),
            "references": self._parsed.get("references", []),
            "attachment_names": [
                attachment["name"]
                for attachment in self._parsed.get("attachments", [])
                if attachment.get("name")
            ],
            "inline_names": [
                inline["name"]
                for inline in self._parsed.get("inlines", [])
                if inline.get("name")
            ],
        }

    def extract_text(self) -> Generator[str, None, None]:
        """
        Yields the decoded plain-text body of the email.

        Yields:
            Plain-text content extracted from the email body.
        """
        text = self._parsed.get("text")
        if text:
            yield text


# --- Example usage ---
if __name__ == "__main__":  # pragma: no cover
    file_path = "samples/sample.eml"
    processor = EmlProcessor(file_path)

    metadata = processor.extract_metadata()
    print("Metadata:")
    for key, value in metadata.items():
        print(f"{key}: {value}")

    print("\nText content preview:\n")
    for i, text in enumerate(processor.extract_text(), start=1):
        print(f"--- Body Part {i} ---")
        print(text[:512])
        if len(text) > 512:
            print("...")
        print("\n---\n")
