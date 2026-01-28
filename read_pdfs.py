import pypdf
import os

pdf_files = [
    'Propuestas IA_ Nicho y Precios.pdf',
    'Anexos.pdf'
]

for pdf_file in pdf_files:
    if os.path.exists(pdf_file):
        print(f'\n{"="*60}')
        print(f'=== {pdf_file} ===')
        print(f'{"="*60}')
        try:
            reader = pypdf.PdfReader(pdf_file)
            # Leer primeras 5 páginas para tener una idea
            num_pages = min(len(reader.pages), 5)
            for i in range(num_pages):
                page = reader.pages[i]
                text = page.extract_text()
                print(f'\n--- Página {i+1} ---\n')
                print(text)
        except Exception as e:
            print(f"Error leyendo {pdf_file}: {e}")
    else:
        print(f"Archivo no encontrado: {pdf_file}")
