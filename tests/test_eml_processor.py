from chunklet.document_chunker.processors.eml_processor import EmlProcessor


def test_extract_metadata_returns_all_available_fields():
    processor = EmlProcessor.__new__(EmlProcessor)
    processor.file_path = "sample.eml"
    processor._parsed = {
        "subject": "Project update",
        "from": "alice@example.com",
        "to": ["bob@example.com"],
        "message_id": "<message@example.com>",
        "attachment": [{"name": "report.pdf"}],
        "inline": [{"name": "logo.png"}],
    }

    assert processor.extract_metadata() == {
        "source": "sample.eml",
        "subject": "Project update",
        "from": "alice@example.com",
        "to": ["bob@example.com"],
        "message_id": "<message@example.com>",
        "attachment_names": ["report.pdf"],
        "inline_names": ["logo.png"],
    }
