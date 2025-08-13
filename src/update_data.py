import sys
import subprocess

def main():
    python_executable = sys.executable  # Uses the current Python interpreter inside your venv

    print("Running scraper...")
    subprocess.run([python_executable, "src/scrape_vahan.py"], check=True)

    print("Processing data...")
    subprocess.run([python_executable, "src/process_data.py"], check=True)

    print("✅ Data updated successfully!")

if __name__ == "__main__":
    main()
