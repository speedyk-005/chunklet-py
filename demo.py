from pprint import pprint
import chunklet.document_chunker.processors as procs

paths = {
    "pdf": "samples/sample-pdf-a4-size.pdf",
    "epub": "samples/minimal.epub",
    "docx": "samples/Lorem Ipsum.docx",
}

processors = {
    "pdf": procs.pdf_processor.PDFProcessor,
    "epub": procs.epub_processor.EpubProcessor,
    "docx": procs.docx_processor.DocxProcessor,
}

doc = "pdf"
proc = processors[doc](paths[doc])

texts = proc.extract_text()
metadata = proc.extract_metadata()

print(list(texts))
pprint(metadata)
