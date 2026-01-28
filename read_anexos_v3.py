import pypdf
import os

pdf_file = 'Anexos .pdf'

if os.path.exists(pdf_file):
    print(f'Leyendo "{pdf_file}"...')
    try:
        reader = pypdf.PdfReader(pdf_file)
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text() + "\n\n"
        print(full_text)
    except Exception as e:
        print(f"Error leyendo PDF: {e}")
else:
    print(f"Error: No se encuentra el archivo '{pdf_file}'")
