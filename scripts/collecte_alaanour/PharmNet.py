"""
PharmNet: collecte des fiches publiques, uniquement si l'accès automatisé
aux pages concernées est autorisé par les conditions d'utilisation du site.
L'utilisateur choisit manuellement la suggestion DCI.
"""
import base64
import csv
import json
import mimetypes
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

BASE_URL = "https://pharmnet-dz.com/"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data"
CARD_SELECTOR = "button.pcard2[data-p]"
EQUIVALENT_SELECTOR = "button.eqrow[data-p]"


def clean_text(text):
    return re.sub(r"\s+", " ", text or "").strip()


def safe_name(value):
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", str(value))
    return re.sub(r"\s+", "_", value.strip())[:90] or "unknown"


def save_json(value, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def folders_for(drug, med=None):
    """Four shared folders for every medicine of the searched DCI."""
    root = OUTPUT_DIR / safe_name(drug)
    paths = {
        "root": root,
        "images": root / "images",
        "table": root / "table",
        "json": root / "json",
        "pdf": root / "pdf",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths


def med_filename(med):
    """Use the site ID to avoid collisions between similar trade names."""
    return safe_name(f"{med['name']}_{med['dose']}_{med['id']}")


CSV_COLUMNS = [
    "Molécule (DCI)",
    "Classe pharmacologique",
    "Laboratoire",
    "Conditionnement",
    "Code d'enregistrement",
    "Origine",
    "Circuit de distribution",
    "Statut",
]


def append_csv_row(paths, row):
    """One CSV for all products; columns match the screenshot exactly."""
    path = paths["table"] / "medicaments.csv"
    is_new = not path.exists() or path.stat().st_size == 0
    with path.open("a", newline="", encoding="utf-8-sig") as output:
        writer = csv.DictWriter(output, fieldnames=CSV_COLUMNS, delimiter=";")
        if is_new:
            writer.writeheader()
        writer.writerow({col: row.get(col, "") for col in CSV_COLUMNS})
    return str(path)


def element_text(parent, selector):
    try:
        return clean_text(parent.find_element(By.CSS_SELECTOR, selector).text)
    except (NoSuchElementException, StaleElementReferenceException):
        return ""


def session_from_driver(driver):
    session = requests.Session()
    session.headers["User-Agent"] = driver.execute_script("return navigator.userAgent")
    session.headers["Referer"] = driver.current_url
    for cookie in driver.get_cookies():
        session.cookies.set(cookie["name"], cookie["value"])
    return session


def open_website(driver):
    driver.get(BASE_URL)
    print("Website:", driver.current_url)


def search_medication(driver, drug):
    locator = (By.XPATH,
        "//input[contains(translate(@placeholder,"
        "'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'DCI')]")
    for attempt in range(5):
        try:
            field = WebDriverWait(driver, 15).until(EC.element_to_be_clickable(locator))
            field.clear()
            field.send_keys(drug)
            print("DCI entered:", drug)
            print("Choose the matching suggestion in Chrome, then wait for results.")
            input("Press Enter AFTER medication cards appear...")
            WebDriverWait(driver, 20).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, CARD_SELECTOR))
            )
            return True
        except (TimeoutException, StaleElementReferenceException):
            print(f"Search retry {attempt + 1}/5")
            time.sleep(1)
    return False


def extract_medications(driver):
    cards = driver.find_elements(By.CSS_SELECTOR, CARD_SELECTOR)
    medicines = []
    seen = set()
    for card in cards:
        try:
            mid = card.get_attribute("data-p")
            if not mid or mid in seen:
                continue
            seen.add(mid)
            medicines.append({
                "id": mid,
                "name": element_text(card, ".c-nom") or "unknown",
                "dose": element_text(card, ".c-dose"),
                "form": element_text(card, ".c-forme"),
                "dci": element_text(card, ".c-dci"),
                "laboratory": element_text(card, ".c-lab-txt"),
                "status": element_text(card, ".c-comm"),
            })
        except StaleElementReferenceException:
            continue
    print(f"Found {len(medicines)} cards")
    return medicines


def open_medication_details(driver, med):
    locator = (By.CSS_SELECTOR, f'button.pcard2[data-p="{med["id"]}"]')
    old_handles = set(driver.window_handles)
    card = WebDriverWait(driver, 20).until(EC.element_to_be_clickable(locator))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", card)
    try:
        card.click()
    except (ElementClickInterceptedException, StaleElementReferenceException):
        card = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(locator))
        card.click()
    new_handles = set(driver.window_handles) - old_handles
    if new_handles:
        driver.switch_to.window(next(iter(new_handles)))
    # The source of vFiche() renders this image and an explicit back button.
    WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "img.fiche-photo"))
    )
    print("Opened details:", med["name"], med["id"])


def scrape_picture(driver, paths, med):
    for element in driver.find_elements(
        By.CSS_SELECTOR, "img.fiche-photo, .fiche-photo img"
    ):
        src = element.get_attribute("src") or element.get_attribute("data-src")
        if not src:
            continue
        # Do not save the graphic placeholder as a medicine photograph.
        if src.startswith("data:image/svg+xml"):
            continue
        try:
            if src.startswith("data:image/"):
                header, payload = src.split(",", 1)
                mime = header.split(";")[0][5:]
                content = base64.b64decode(payload) if ";base64" in header else None
                if content is None:
                    continue
            else:
                url = urljoin(driver.current_url, src)
                if urlparse(url).netloc != urlparse(BASE_URL).netloc:
                    continue  # Only same-site public assets
                response = session_from_driver(driver).get(url, timeout=25)
                response.raise_for_status()
                mime = response.headers.get("Content-Type", "").split(";")[0]
                if not mime.startswith("image/"):
                    continue
                content = response.content
            extension = mimetypes.guess_extension(mime) or ".jpg"
            if extension == ".jpe":
                extension = ".jpg"
            path = paths["images"] / (med_filename(med) + extension)
            path.write_bytes(content)
            return str(path)
        except (ValueError, requests.RequestException):
            continue
    return None


def scrape_table(driver, paths, med):
    """Read the 8 visible information rows and append one record to CSV."""
    extracted = driver.execute_script(r"""
        const photo = document.querySelector('img.fiche-photo');
        if (!photo) return {};
        const root = photo.closest('main') || document.querySelector('main') || document.body;
        const fields = {};
        for (const node of root.querySelectorAll('div')) {
            const kids = Array.from(node.children);
            if (kids.length !== 3 || !kids.every(x => x.tagName === 'SPAN')) continue;
            if (!kids[0].querySelector('svg')) continue;
            const key = (kids[1].innerText || '').replace(/\s+/g, ' ').trim();
            const value = (kids[2].innerText || '').replace(/\s+/g, ' ').trim();
            if (key && value && !(key in fields)) fields[key] = value;
        }
        return fields;
    """) or {}

    # Do not invent missing values. Match labels case/accent-insensitively.
    import unicodedata
    def norm(s):
        return " ".join("".join(
            c for c in unicodedata.normalize("NFKD", str(s).lower())
            if not unicodedata.combining(c)
        ).split())
    normalized = {norm(k): v for k, v in extracted.items()}
    row = {col: normalized.get(norm(col), "") for col in CSV_COLUMNS}
    if not row["Molécule (DCI)"]:
        row["Molécule (DCI)"] = med.get("dci", "")
    if not row["Laboratoire"]:
        row["Laboratoire"] = med.get("laboratory", "")
    # CSV only includes the requested eight column names.
    path = append_csv_row(paths, row)
    missing = [col for col, value in row.items() if not value]
    if missing:
        print("  Missing CSV fields:", ", ".join(missing))
    return path


def extract_generiques(driver, source_med):
    """Extrait les équivalents de la fiche courante sans suivre les boutons."""
    data = driver.execute_script(r"""
        const section = Array.from(document.querySelectorAll('section.card'))
          .find(s => /Équivalents thérapeutiques/i.test(
            s.querySelector('h3')?.innerText || ''));
        if (!section) return null;
        const headline = section.querySelector('h3');
        const description = Array.from(section.querySelectorAll('p'))
          .find(p => /Produits partageant le code DCI/i.test(p.innerText));
        const code = description?.querySelector('.dci')?.innerText?.trim() || '';
        const products = Array.from(section.querySelectorAll('button.eqrow[data-p]'))
          .map(button => {
            const txt = node => (node?.innerText || '').replace(/\s+/g, ' ').trim();
            const tags = Array.from(button.querySelectorAll('.chip')).map(txt);
            const labCountry = txt(button.querySelector('span.mut'));
            const sep = labCountry.lastIndexOf(' · ');
            return {
              id: button.getAttribute('data-p') || '',
              nom: txt(button.querySelector('b')),
              laboratoire: sep < 0 ? labCountry : labCountry.slice(0, sep),
              pays: sep < 0 ? '' : labCountry.slice(sep + 3),
              dosage: tags.find(t => t !== 'Local' && t !== 'Substituable') || '',
              local: tags.includes('Local'),
              substituable_indique: button.classList.contains('exact') || tags.includes('Substituable')
            };
          }).filter(p => p.id);
        return {
          titre: txtFallback(headline),
          code_dci: code,
          nombre_produits: products.length,
          description: description?.innerText?.replace(/\s+/g, ' ').trim() || '',
          produits: products
        };
        function txtFallback(el) { return (el?.innerText || '').trim(); }
    """)
    if data is None:
        print('Section Équivalents thérapeutiques absente')
        return {
            'titre': 'Équivalents thérapeutiques',
            'code_dci': '', 'nombre_produits': 0,
            'description': '', 'produits': [],
            'section_trouvee': False
        }
    data['section_trouvee'] = True
    print(f"  Équivalents: {data['nombre_produits']}")
    return data


def scrape_sections(driver, paths, med):
    """Enregistre les sections visibles et les équivalents structurés dans sections.json."""
    result = {
        "nom_commercial": med.get("name", ""),
        "dosage": med.get("dose", ""),
        "dci": med.get("dci", ""),
    }
    for section in driver.find_elements(By.CSS_SELECTOR, 'section.card'):
        if not section.is_displayed():
            continue
        headings = section.find_elements(By.CSS_SELECTOR, 'h3')
        if not headings:
            continue
        title = clean_text(headings[0].text)
        if title and 'Équivalents thérapeutiques' not in title:
            result[title] = clean_text(section.text)

    equivalents = extract_generiques(driver, med)
    result['Équivalents thérapeutiques'] = equivalents
    save_json(result, paths['json'] / (med_filename(med) + '.json'))
    return result, equivalents


def scrape_pdfs(driver, paths, med):
    """Collect only publicly available document links advertised by doc-on buttons."""
    files = []
    session = session_from_driver(driver)
    try:
        WebDriverWait(driver, 12).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".doc-card"))
        )
    except TimeoutException:
        print("No document cards visible")
        return files

    cards = driver.find_elements(By.CSS_SELECTOR, "button.doc-card.doc-on[data-doc-url]")
    if not cards:
        print("No public Notice/RCP offered for this medicine")
        return files

    for idx, card in enumerate(cards, 1):
        title = clean_text(card.get_attribute("data-doc-titre") or card.text)
        raw = card.get_attribute("data-doc-url")
        if not raw:
            continue
        url = urljoin(BASE_URL, raw)
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or parsed.netloc != urlparse(BASE_URL).netloc:
            print("Skipping external document URL:", url)
            continue
        low = title.lower()
        name = "notice" if "notice" in low else "rcp" if "rcp" in low else f"document_{idx}"
        path = paths["pdf"] / (med_filename(med) + "_" + name + ".pdf")
        try:
            response = session.get(url, timeout=30)
            response.raise_for_status()
            if not response.content.startswith(b"%PDF-"):
                print("Document is not a PDF:", url, "HTTP", response.status_code)
                continue
            path.write_bytes(response.content)
            files.append({"title": title, "url": url, "path": str(path)})
            print("PDF saved:", path)
        except requests.RequestException as error:
            print("PDF not downloaded:", url, error)
    return files


def scrape_medication(driver, drug, med):
    paths = folders_for(drug)
    photo = scrape_picture(driver, paths, med)
    csv_path = scrape_table(driver, paths, med)
    sections, equivalents = scrape_sections(driver, paths, med)
    pdfs = scrape_pdfs(driver, paths, med)
    section_path = paths["json"] / (med_filename(med) + ".json")
    info = {
        "medication": med,
        "picture": photo,
        "table": csv_path,
        "sections_json": str(section_path),
        "pdfs": pdfs,
        "equivalents_count": equivalents["nombre_produits"],
    }
    print("  CSV:", csv_path)
    print("  JSON:", section_path)
    print("  Image:", photo or "Not available")
    print("  PDFs:", len(pdfs))
    return info, equivalents["produits"]


def return_to_results(driver, result_url, old_handles, med):
    extra = set(driver.window_handles) - old_handles
    if extra:
        driver.close()
        driver.switch_to.window(next(iter(old_handles)))
    current = driver.find_elements(By.CSS_SELECTOR, CARD_SELECTOR)
    if current and any(c.is_displayed() for c in current):
        return
    back = driver.find_elements(By.CSS_SELECTOR, 'button[data-act="back"]')
    for button in back:
        if button.is_displayed():
            button.click()
            break
    else:
        if driver.current_url != result_url:
            driver.back()
    WebDriverWait(driver, 15).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, CARD_SELECTOR))
    )


def save_all_generiques(drug, equivalents):
    """Un JSON global, comme demandé précédemment, en plus des sections.json."""
    unique = {}
    for item in equivalents:
        mid = item['id']
        med_source = item['source_medication']
        if mid not in unique:
            unique[mid] = {
                **{k: v for k, v in item.items() if k != 'source_medication'},
                'found_in': [med_source],
            }
        elif med_source not in unique[mid]['found_in']:
            unique[mid]['found_in'].append(med_source)
    path = folders_for(drug)['json'] / 'generiques.json'
    save_json({
        'dci_recherchee': drug,
        'source': BASE_URL,
        'date_collecte_utc': datetime.now(timezone.utc).isoformat(),
        'note': 'Équivalents thérapeutiques affichés; pas nécessairement des médicaments génériques.',
        'total': len(unique),
        'equivalents': list(unique.values()),
    }, path)
    print('Global equivalents:', path)


def scrape_all_medications(driver, drug):
    paths = folders_for(drug)
    csv_file = paths["table"] / "medicaments.csv"
    # Start with a fresh CSV, including the eight required column headers.
    with csv_file.open("w", newline="", encoding="utf-8-sig") as handle:
        csv.DictWriter(handle, fieldnames=CSV_COLUMNS, delimiter=";").writeheader()
    medicines = extract_medications(driver)
    result_url = driver.current_url
    results, errors, equivalents = [], [], []
    for i, med in enumerate(medicines, 1):
        print(f"\n[{i}/{len(medicines)}] {med['name']} {med['dose']}")
        old_handles = set(driver.window_handles)
        opened = False
        try:
            open_medication_details(driver, med)
            opened = True
            result, generiques = scrape_medication(driver, drug, med)
            results.append(result)
            equivalents.extend([
                {**item, 'source_medication': {
                    'id': med['id'], 'name': med['name'], 'dose': med['dose']
                }} for item in generiques
            ])
        except Exception as exc:
            print("Error:", exc)
            errors.append({"id": med["id"], "name": med["name"], "error": str(exc)})
        finally:
            if opened:
                try:
                    return_to_results(driver, result_url, old_handles, med)
                except Exception as exc:
                    print("Cannot safely return to results; stopping:", exc)
                    errors.append({"id": med["id"], "error": "Return failed: " + str(exc)})
                    break
        time.sleep(1.5)

    save_all_generiques(drug, equivalents)
    save_json({
        "dci": drug,
        "found": len(medicines),
        "processed": len(results),
        "errors": errors,
        "medications": results,
    }, folders_for(drug)["json"] / "summary.json")
    print(f"\nProcessed {len(results)}/{len(medicines)} medications.")


def main():
    print("Use only if PharmNet's terms permit automated collection of these public pages.")
    if input("Have you verified permission? (yes/no): ").strip().lower() != "yes":
        print("Collection cancelled.")
        return
    drug = input("Enter DCI: ").strip()
    if not drug:
        print("DCI cannot be empty.")
        return
    driver = webdriver.Chrome()
    driver.maximize_window()
    try:
        open_website(driver)
        if search_medication(driver, drug):
            scrape_all_medications(driver, drug)
        input("\nPress Enter to close Chrome...")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
