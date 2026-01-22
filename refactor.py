import shutil
from pathlib import Path

# --- Configuration ---
PROJECT_ROOT = Path.cwd()
SRC_DIR = PROJECT_ROOT / "src"
PYTHON_CORE_DIR = PROJECT_ROOT / "python_core"
BACKEND_DIR = PROJECT_ROOT / "backend"
TESTS_DIR = PROJECT_ROOT / "tests"

# Specific folders to move from src/ to python_core/
FOLDERS_TO_MOVE = [
    "ingestion",
    "transcription",
    "intelligence",
    "vision",
    "retrieval",
    "editing",
    "overlay",
    "packaging",
    "distribution",
    "utils",
    "modes",
    "audio",
]

# Specific files to move from src/ to python_core/
FILES_TO_MOVE = ["pipeline.py", "config_manager.py", "worker.py"]


def update_imports(file_path):
    """
    Reads a python file and replaces 'src.' references with 'python_core.'
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Perform replacements
        # Be careful with "from src import" vs "from src.xxx"
        # We want to replace "src" with "python_core" ONLY when it refers to the python package
        # Simple string replacement handles "from src." -> "from python_core."
        new_content = content.replace("from src.", "from python_core.")
        new_content = new_content.replace("import src.", "import python_core.")
        new_content = new_content.replace("from src ", "from python_core ")

        # Edge case: "from src import ConfigManager" -> "from python_core import ConfigManager"
        # Since src is now just frontend, any python import referencing src is wrong.

        if content != new_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"  [UPDATED IMPORTS]: {file_path.relative_to(PROJECT_ROOT)}")
    except Exception as e:
        print(f"  [ERROR PROCESSING]: {file_path} - {e}")


def main():
    print("🚀 Starting ClipFlowAI Refactor...")
    print(f"   Root: {PROJECT_ROOT}")

    # 1. Create python_core directory
    if not PYTHON_CORE_DIR.exists():
        PYTHON_CORE_DIR.mkdir()
        print("✅ Created directory: python_core/")

    # Create __init__.py package marker
    init_file = PYTHON_CORE_DIR / "__init__.py"
    if not init_file.exists():
        init_file.touch()
        print("✅ Created python_core/__init__.py")

    # 2. Move Python Logic Directories
    if SRC_DIR.exists():
        for folder in FOLDERS_TO_MOVE:
            src_path = SRC_DIR / folder
            dest_path = PYTHON_CORE_DIR / folder

            if src_path.exists():
                if dest_path.exists():
                    print(f"⚠️  Skipping move (Target exists): {folder}")
                else:
                    shutil.move(str(src_path), str(dest_path))
                    print(f"📦 Moved folder: src/{folder} -> python_core/{folder}")
            else:
                pass

        # 3. Move Python Logic Files
        for filename in FILES_TO_MOVE:
            src_path = SRC_DIR / filename
            dest_path = PYTHON_CORE_DIR / filename

            if src_path.exists():
                shutil.move(str(src_path), str(dest_path))
                print(f"📄 Moved file: src/{filename} -> python_core/{filename}")

        # Check for rogue cli.py in src
        rogue_cli = SRC_DIR / "cli.py"
        if rogue_cli.exists():
            # If cli.py was in src, move it to python_core or delete it if we have one in root?
            # The prompt said "Move cli.py and main.py from ROOT to python_core... Decision: Keep cli.py in ROOT"
            # But earlier I might have put cli.py in src/ implicitly via my generation or imports?
            # Let's check. If cli.py is in src, it shouldn't be.
            # I'll just move it to python_core as internal if found.
            # But wait, I am rewriting cli.py in root later. So I can just delete src/cli.py if it exists.
            # Actually, renaming it to be safe.
            shutil.move(str(rogue_cli), str(PYTHON_CORE_DIR / "cli_internal.py"))
            print("⚠️  Moved src/cli.py to python_core/cli_internal.py")

    # 4. Update Imports in ALL relevant python files
    print("\n🔄 Rewriting Import Statements...")

    # Scan these directories for .py files
    scan_dirs = [PYTHON_CORE_DIR, BACKEND_DIR, TESTS_DIR, PROJECT_ROOT]

    for folder in scan_dirs:
        if not folder.exists():
            continue

        # If it's the root, don't recurse into node_modules or venv
        if folder == PROJECT_ROOT:
            files = [f for f in folder.glob("*.py") if f.is_file() and f.name != "refactor.py"]
        else:
            files = folder.rglob("*.py")

        for file_path in files:
            update_imports(file_path)

    print("\n✨ Refactor Complete! 'src/' should now only contain Frontend assets.")


if __name__ == "__main__":
    main()
