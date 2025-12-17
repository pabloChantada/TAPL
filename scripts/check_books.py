import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Error: No se encontró GEMINI_API_KEY en el archivo .env")
    exit()

genai.configure(api_key=api_key)

books_env = os.getenv("THEORY_BOOKS", "")
book_ids = [b.strip() for b in books_env.split(",") if b.strip()]

print(f"Checking books from .env: {book_ids}")

for book_id in book_ids:
    try:
        file_ref = genai.get_file(book_id)
        print(f"Found book: {file_ref.name} - {file_ref.display_name} ({file_ref.state.name})")
    except Exception as e:
        print(f"Error finding book {book_id}: {e}")

print("\nListing all files:")
try:
    for f in genai.list_files():
        print(f" - {f.name}: {f.display_name}")
except Exception as e:
    print(f"Error listing files: {e}")
