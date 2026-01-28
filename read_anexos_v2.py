import pypdf
import os

pdf_file = 'Anexos.pdf'

if os.path.exists(pdf_file):
    print(f'Leyendo {pdf_file}...')
    try:
        reader = pypdf.PdfReader(pdf_file)
        print(f"Total páginas: {len(reader.pages)}")
        for i, page in enumerate(reader.pages):
            print(f'\n--- Página {i+1} ---\n')
            print(page.extract_text())
    except Exception as e:
        print(f"Error leyendo PDF: {e}")
else:
    print(f"Error: No se encuentra el archivo {pdf_file} en {os.getcwd()}")
