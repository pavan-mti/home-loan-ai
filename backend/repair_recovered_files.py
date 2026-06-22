import os
import ast
import json
from pathlib import Path

def repair_file(file_path: Path):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    
    content_stripped = content.strip()
    
    # Check if the file is stored as a single escaped string.
    # Usually it starts with a double quote " or single quote '
    # AND it contains escaped newlines (\\n).
    if not (content_stripped.startswith('"') or content_stripped.startswith("'")):
        return False
        
    if "\\n" not in content_stripped:
        return False
        
    print(f"Detecting corrupted file: {file_path}")
    
    # Check quote character
    quote_char = content_stripped[0]
    
    # Handle missing closing quote due to truncation
    if not content_stripped.endswith(quote_char):
        print(f"File {file_path} seems truncated (missing closing quote). Appending quote character: {quote_char}")
        content_stripped += quote_char
        
    # Attempt to decode
    decoded = None
    try:
        decoded = ast.literal_eval(content_stripped)
    except Exception as e:
        print(f"ast.literal_eval failed for {file_path}: {e}. Trying json.loads...")
        if quote_char == '"':
            try:
                decoded = json.loads(content_stripped)
            except Exception as je:
                print(f"json.loads failed: {je}")
                
    if decoded is None or not isinstance(decoded, str):
        # Fallback to manual codec decoding
        try:
            raw_str = content_stripped[1:-1]
            decoded = raw_str.encode('utf-8').decode('unicode_escape')
        except Exception as e:
            print(f"Manual decode failed for {file_path}: {e}")
            return False
            
    if decoded:
        # Write decoded python code back to the file
        with open(file_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(decoded)
        print(f"SUCCESS: Repaired and overwrote: {file_path}")
        return True
        
    return False

def main():
    backend_dir = Path("app") # We are running in e:\home\backend
    if not backend_dir.exists():
        backend_dir = Path("backend/app")
        
    repaired_count = 0
    scanned_count = 0
    
    for root, _, files in os.walk(backend_dir):
        for file in files:
            if file.endswith(".py"):
                scanned_count += 1
                file_path = Path(root) / file
                if repair_file(file_path):
                    repaired_count += 1
                    
    print(f"\nScan complete. Scanned {scanned_count} python files. Repaired {repaired_count} files.")

if __name__ == "__main__":
    main()
