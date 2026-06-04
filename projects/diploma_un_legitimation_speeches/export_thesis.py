import re
import subprocess
import os
from datetime import datetime

PANDOC = r"C:\Users\Aram\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\LocalCache\local-packages\Python311\site-packages\pypandoc\files\pandoc.exe"

BASE = r"C:\Users\Aram\Documents\projects\ResearchOS\projects\diploma_un_legitimation_speeches"

CHAPTERS = [
    r"chapters\00_introduction.md",
    r"chapters\01_literature_review.md",
    r"chapters\02_theoretical_framework.md",
    r"chapters\03_methodology.md",
    r"chapters\04_empirical_analysis.md",
    r"chapters\05_discussion.md",
    r"chapters\06_conclusion.md",
    r"chapters\07_references.md",
]


def strip_internal_sections(text):
    # Remove Self-review and everything after the separator before it
    cleaned = re.sub(r'\n---\n+##\s+Self-review.*$', '', text, flags=re.DOTALL)
    # Also remove any standalone --- at end of file
    cleaned = cleaned.rstrip()
    if cleaned.endswith('\n---'):
        cleaned = cleaned[:-4]
    return cleaned.strip()


parts = []
for chapter in CHAPTERS:
    path = os.path.join(BASE, chapter)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    cleaned = strip_internal_sections(content)
    parts.append(cleaned)

# Join chapters with page breaks
combined = "\n\n\\newpage\n\n".join(parts)

# Write temp combined file
combined_path = os.path.join(BASE, "output", "thesis_combined_temp.md")
with open(combined_path, 'w', encoding='utf-8') as f:
    f.write(combined)

# Output path
date_str = datetime.now().strftime("%Y-%m-%d")
output_path = os.path.join(BASE, "output", f"thesis_{date_str}.docx")
reference_doc = os.path.join(BASE, "reference.docx")

cmd = [
    PANDOC,
    combined_path,
    "-o", output_path,
    "--reference-doc", reference_doc,
    "--wrap=none",
    "--toc=false",
]

print(f"Running: {' '.join(cmd)}")
result = subprocess.run(cmd, capture_output=True, text=True)

print(f"Return code: {result.returncode}")
if result.stdout:
    print(f"Stdout: {result.stdout}")
if result.stderr:
    print(f"Stderr: {result.stderr}")

# Clean up temp file
os.remove(combined_path)

if result.returncode == 0:
    print(f"\nSuccess! Output saved to:\n{output_path}")
else:
    print("\nExport failed.")
