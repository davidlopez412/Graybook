import pdfplumber

pdf_path = "1_Inputs/Nimitz_Graybook Volume 1.pdf"

with pdfplumber.open(pdf_path) as pdf:
    for i, page in enumerate(pdf.pages[:15], start=1):
        text = page.extract_text()
        print(f"\n{'='*60}")
        print(f"PAGE {i}")
        print(f"{'='*60}")
        print(text if text else "[No text extracted]")
