import os
import zipfile
from pathlib import Path

def main():
    # Source directory is the directory containing this script
    source_dir = Path(__file__).parent.resolve()
    
    # Destination directory (Desktop)
    desktop_dir = Path(os.path.expanduser("~/Desktop"))
    zip_filename = "meshcloud_project.zip"
    zip_path = desktop_dir / zip_filename
    
    # Exclude patterns (junk and large local files)
    EXCLUDE_DIRS = {
        "venv", "__pycache__", ".git", ".idea", ".vscode", 
        "storage", "storage_node1", "storage_node2", "logs", 
        "htmlcov", ".pytest_cache", "site", "dist", "build", 
        "meshcloud.egg-info", "node_modules"
    }
    
    EXCLUDE_EXTENSIONS = {".pyc", ".pyo", ".pyd", ".db", ".log", ".DS_Store"}
    
    # Don't include the script itself or the zip if it's being made in the root
    EXCLUDE_FILES = {zip_filename, "create_zip.py"}

    print(f"📦 Zipping project from: {source_dir}")
    print(f"📍 Destination: {zip_path}")
    
    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_dir):
                # Exclude directories
                dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
                
                for file in files:
                    file_path = Path(root) / file
                    
                    # Exclude files by name or extension
                    if file in EXCLUDE_FILES or file_path.suffix in EXCLUDE_EXTENSIONS:
                        continue
                    
                    # Calculate archive name (relative path)
                    archive_name = file_path.relative_to(source_dir)
                    zipf.write(file_path, archive_name)
        
        print(f"\n✅ Successfully created zip file on your Desktop: {zip_filename}")
        
    except Exception as e:
        print(f"\n❌ Error creating zip file: {e}")

if __name__ == "__main__":
    main()