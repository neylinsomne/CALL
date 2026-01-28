import pypdf
import sys

try:
    reader = pypdf.PdfReader('Propuestas IA_ Nicho y Precios.pdf')
    print(f"Total páginas: {len(reader.pages)}")
    for i, page in enumerate(reader.pages):
        print(f"\n--- Página {i+1} ---\n")
        print(page.extract_text())
except Exception as e:
    print(f"Error: {e}")
