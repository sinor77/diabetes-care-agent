from pypdf import PdfReader
reader = PdfReader("MMU_Showcase_Prep.pdf")
for i, page in enumerate(reader.pages):
    print(f"--- Page {i+1} ---")
    print(page.extract_text())
