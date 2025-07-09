import os
import re
import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# === CONFIGURATION ===
HEADERS = {"User-Agent": "Mozilla/5.0"}
DOWNLOAD_FOLDER = "downloads"
TEXT_FOLDER = "text_data"
METADATA_FOLDER = "metadata"
DOCUMENT_EXTENSIONS = ('.pdf', '.zip', '.rar', '.xml', '.doc', '.docx', '.xls', '.xlsx')
COMBINED_TEXT_FILE = os.path.join(TEXT_FOLDER, "mosdac_combined.txt")
COMBINED_METADATA_FILE = os.path.join(METADATA_FOLDER, "combined.json")

# === UTILITY FUNCTIONS ===
def sanitize_filename(name):
    return "".join(c if c.isalnum() or c in ['_', '-'] else "_" for c in name)

def save_file_from_url(url, folder):
    try:
        filename = sanitize_filename(os.path.basename(urlparse(url).path))
        filepath = os.path.join(folder, filename)
        print(f"[DOWNLOAD] {filename}")

        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.ok:
            with open(filepath, 'wb') as f:
                f.write(response.content)
            print(f"[✓] Saved to: {filepath}")
        else:
            print(f"[✗] Failed to download: {url}")
    except Exception as e:
        print(f"[ERROR] Download failed: {url} | {e}")

def extract_text_and_metadata(url, combined_text_path, metadata_collection):
    try:
        print(f"[PROCESS] {url}")
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        page_title = soup.title.string.strip() if soup.title else "Untitled"
        headings, paragraphs, tables = [], [], []

        for i in range(1, 7):
            for tag in soup.find_all(f'h{i}'):
                text = tag.get_text(strip=True)
                if text:
                    headings.append({"level": f"h{i}", "text": text})

        for tag in soup.find_all('p'):
            text = tag.get_text(strip=True)
            if text:
                paragraphs.append(text)

        for table in soup.find_all('table'):
            for row in table.find_all('tr'):
                cols = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]
                if cols:
                    tables.append(cols)

        # Append to text file
        filename = sanitize_filename(url.replace("https://www.mosdac.gov.in/", ""))
        with open(combined_text_path, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"File: {filename}\n")
            f.write(f"URL: {url}\n")
            f.write(f"{'='*60}\n\n")
            f.write(f"TITLE: {page_title}\n\n")
            for h in headings:
                f.write(f"[{h['level'].upper()}] {h['text']}\n")
            for p in paragraphs:
                f.write(p + "\n")
            for row in tables:
                f.write(" | ".join(row) + "\n")

        # Add to metadata list (not saving individual JSONs)
        metadata_collection.append({
            "url": url,
            "title": page_title,
            "headings": headings,
            "paragraphs": paragraphs,
            "tables": tables
        })

        print(f"[✓] Processed: {filename}")

    except Exception as e:
        print(f"[ERROR] Text extraction failed: {url} | {e}")

def process_links_from_file(file_path):
    os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
    os.makedirs(TEXT_FOLDER, exist_ok=True)
    os.makedirs(METADATA_FOLDER, exist_ok=True)

    # Empty combined output files if they exist
    open(COMBINED_TEXT_FILE, 'w').close()

    links = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                # Remove leading numbers (e.g., "42. https://...")
                cleaned = re.sub(r'^\d+\.\s*', '', line)
                links.append(cleaned)

    print(f"[INFO] Processing {len(links)} links...")
    all_metadata = []

    for url in links:
        if any(url.lower().endswith(ext) for ext in DOCUMENT_EXTENSIONS):
            save_file_from_url(url, DOWNLOAD_FOLDER)
        else:
            extract_text_and_metadata(url, COMBINED_TEXT_FILE, all_metadata)

    # Save one combined metadata file
    with open(COMBINED_METADATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_metadata, f, indent=2)

    print(f"\n✅ All links processed.")
    print(f"📝 Text saved to: {COMBINED_TEXT_FILE}")
    print(f"📦 Metadata saved to: {COMBINED_METADATA_FILE}")
    print(f"📁 Downloads saved to: {DOWNLOAD_FOLDER}/")

# === ENTRY POINT ===
if __name__ == "__main__":
    input_file = r"C:\Users\getin\Desktop\crawler\mosdac_links.txt"
    
    if os.path.exists(input_file):
        print(f"[INFO] Using input file: {input_file}")
        process_links_from_file(input_file)
    else:
        print(f"[ERROR] File not found: {input_file}")
