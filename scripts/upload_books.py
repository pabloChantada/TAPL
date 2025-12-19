import google.generativeai as genai
import os
import glob
from dotenv import load_dotenv

# Cargar variables de entorno (API KEY)
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Error: No se encontró GEMINI_API_KEY en el archivo .env")
    exit()

genai.configure(api_key=api_key)

def upload_all_books():
    # 1. Definir la ruta de la carpeta de libros
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    books_dir = os.path.join(base_dir, "docs", "books")

    print(f"Buscando libros en: {books_dir} ...")

    # 2. Encontrar todos los .pdf
    pdf_files = glob.glob(os.path.join(books_dir, "*.pdf"))

    if not pdf_files:
        print("No se encontraron archivos .pdf en la carpeta.")
        return

    uploaded_ids = []

    print(f"Se encontraron {len(pdf_files)} libros. Subiendo a Gemini...\n")

    # 3. Subir uno a uno
    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        print(f"   Subiendo: {filename} ...", end=" ", flush=True)
        
        try:
            # Subida del archivo
            file_ref = genai.upload_file(pdf_path, display_name=filename)
            
            print(f"OK ID: {file_ref.name}")
            uploaded_ids.append(file_ref.name)
            
        except Exception as e:
            print(f"Error: {e}")
    # 4. Generar la línea para el .env
    print("\n" + "="*50)
    print("Lito. Copia esta línea en tu archivo .env:")
    print("="*50 + "\n")
    
    env_string = ",".join(uploaded_ids)
    print(f"THEORY_BOOKS={env_string}")
    
    print("\n" + "="*50)

if __name__ == "__main__":
    upload_all_books()