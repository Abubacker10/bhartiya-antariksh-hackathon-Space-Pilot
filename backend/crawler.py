import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

BASE_URL = "https://www.mosdac.gov.in"
SITEMAP_URL = f"{BASE_URL}/sitemap"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def get_all_internal_links_from_sitemap():
    print("[STEP 1] Extracting Set 1 from sitemap...")
    response = requests.get(SITEMAP_URL, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")
    links = set()

    for a_tag in soup.find_all("a", href=True):
        href = a_tag['href']
        full_url = urljoin(BASE_URL, href)
        parsed = urlparse(full_url)
        if BASE_URL in full_url and parsed.path != '/':
            links.add(full_url)

    return sorted(links)

def get_menu_clearfix_links_from_mission_pages(mission_links):
    print("[STEP 2] Extracting Set 2 from mission pages...")
    menu_links = set()

    for mission_url in mission_links:
        try:
            response = requests.get(mission_url, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            # Search for all menu clearfix blocks
            menus = soup.find_all("ul", class_="menu clearfix")

            for ul in menus:
                for li in ul.find_all("li"):
                    a_tag = li.find("a", href=True)
                    if a_tag:
                        full_url = urljoin(BASE_URL, a_tag['href'])
                        menu_links.add(full_url)

        except Exception as e:
            print(f"[ERROR] Failed to load {mission_url} | {e}")

    return sorted(menu_links)

# MAIN
if __name__ == "__main__":
    # Step 1: Get all internal webpage links from sitemap
    set1_links = get_all_internal_links_from_sitemap()

    # Step 2: Filter mission page links from Set 1 (e.g., /insat-3dr, /megha-tropiques, etc.)
    mission_keywords = ['insat', 'megha', 'kalpana', 'saral', 'oceansat', 'scatsat']
    mission_pages = [link for link in set1_links if any(k in link.lower() for k in mission_keywords)]

    # Step 3: Visit each mission page and extract all <ul class="menu clearfix"> links
    set2_links = get_menu_clearfix_links_from_mission_pages(mission_pages)

    # Print results
    output_file = "mosdac_links.txt"

with open(output_file, "w", encoding="utf-8") as f:
    f.write("✅ Set 1: All internal webpage links from sitemap:\n")
    for i, link in enumerate(set1_links, 1):
        f.write(f"{i}. {link}\n")

    f.write("\n✅ Set 2: All <ul class='menu clearfix'> links from mission pages:\n")
    for i, link in enumerate(set2_links, 1):
        f.write(f"{i}. {link}\n")

print(f"\n✅ All links saved to {output_file}")

