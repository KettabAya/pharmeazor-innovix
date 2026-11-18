
import re
import time
from urllib.parse import urljoin

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import expect, sync_playwright
DOSSIER_PDF = Path("data/row-data/PDF/pdf-françe-")
DOCUMENTS = {
    "fiche_info": ("Fiche info", "tabpanel-fiche-info-panel"),
    "rcp": ("Resume des caracteristiques du produit", "tabpanel-rcp-panel"),
    "notice": ("Notice", "tabpanel-notice-panel"),
    "bon_usage": ("Bon usage", "tabpanel-bon-usage-panel"),
}
class DocumentIndisponible(Exception):
    """Onglet ou contenu absent, desactive, masque ou vide."""


def telecharger_documents(url, nom_fichier , id):
    dossier = DOSSIER_PDF / nom_fichier
    dossier.mkdir(parents=True, exist_ok=True)
    resultats = {document: None for document in DOCUMENTS}

    with sync_playwright() as p:
        navigateur = p.chromium.launch(headless=True)
        try:
            page = navigateur.new_page(
                viewport={"width": 1440, "height": 1000},
                locale="fr-FR",
                color_scheme="light",
            )
            page.set_default_timeout(10000)
            reponse = page.goto(url, wait_until="load", timeout=60000)
            if reponse is None or not reponse.ok:
                raise RuntimeError("Impossible de charger la fiche du medicament.")

            # Attendre le JavaScript du site avant de selectionner l'onglet.
            page.wait_for_function("typeof window.printMedicament === 'function'")
            page.evaluate("document.fonts.ready")

            for document, (libelle, panneau_id) in DOCUMENTS.items():
                try:
                    onglet = page.locator(
                        f"button[role='tab'][aria-controls='{panneau_id}']"
                    )
                    if onglet.count() == 0:
                        raise DocumentIndisponible("onglet absent")
                    if (
                        not onglet.is_enabled()
                        or onglet.get_attribute("aria-disabled") == "true"
                    ):
                        raise DocumentIndisponible("onglet desactive")
                    if not onglet.is_visible():
                        raise DocumentIndisponible("onglet masque")

                    panneau = page.locator(f"#{panneau_id}")
                    if panneau.count() == 0:
                        raise DocumentIndisponible("contenu absent")

                    print(f"Generation : {libelle}")
                    onglet.click()
                    expect(onglet).to_have_attribute("aria-selected", "true")
                    expect(panneau).to_be_visible()
                    if not panneau.inner_text().strip():
                        raise DocumentIndisponible("contenu vide")

                    page.evaluate("document.fonts.ready")
                    chemin = dossier / f"{nom_fichier}_{document}_{id}.pdf"

                    # Impression PDF de l'onglet selectionne.
                    contenu_pdf = page.pdf(
                        format="A4",
                        print_background=True,
                        prefer_css_page_size=True,
                        margin={
                            "top": "10mm", "bottom": "10mm",
                            "left": "10mm", "right": "10mm",
                        },
                    )
                    if not contenu_pdf.startswith(b"%PDF-"):
                        raise RuntimeError("Le PDF genere est invalide.")
                    chemin.write_bytes(contenu_pdf)
                    resultats[document] = chemin
                    print(f"[OK] {chemin}")

                except DocumentIndisponible as erreur:
                    print(f"[IGNORE] {libelle} : {erreur}. Onglet suivant.")

                except (PlaywrightTimeoutError, AssertionError):
                    print(f"[DELAI DEPASSE] {libelle}. Onglet suivant.")

                except Exception as erreur:
                    # Continuer avec les autres onglets en cas d'echec.
                    resultats[document] = None
                    print(f"[ERREUR] {libelle} : {erreur}")
        except Exception as erreur:
            # Une fiche absente ou inaccessible ne bloque pas l'appelant.
            print(f"[ERREUR FICHE] {url} : {erreur}")
        finally:
            navigateur.close()

    nombre = sum(chemin is not None for chemin in resultats.values())
    print(f"\nTermine : {nombre}/{len(DOCUMENTS)} PDF enregistres dans {dossier}")
    return resultats


df = pd.read_excel("config/Projet2_Liste_40_medicaments.xlsx")
medicines = (
    df["DCI (nom de la substance)"]
    .dropna()
    .astype(str)
    .str.strip()
    .tolist()
)
result = []
for medicine in medicines:
    result.append(medicine)
    if "+" in medicine:
        match = re.search(r"\((.*?)\)", medicine)

        if match:
            main_name = medicine[:match.start()].strip()

            if main_name:
                result.append(main_name)

            components = match.group(1).split("+")

            result.extend([
                component.strip()
                for component in components
                if component.strip()
            ])

        else:
            result.extend([
                part.strip()
                for part in medicine.split("+")
                if part.strip()
            ])
DRUG = list(dict.fromkeys(result))
BASE_URL = "https://base-donnees-publique.medicaments.gouv.fr/"

TABLE_ID = "table-accordeon-fetch-result"

LINK_SELECTOR = (
    f"#{TABLE_ID} tbody "
    'a[href^="/medicament/"][href$="/extrait"]'
)

NEXT_SELECTOR = (
    f"#{TABLE_ID}_wrapper "
    'a[data-dt-idx="next"]'
)


# ==========================================
# 1. SEARCH MEDICATION
# ==========================================

def search_medication(driver, drug):

    driver.get(BASE_URL)

    wait = WebDriverWait(driver, 30)

    # Find visible search input
    search = None

    selectors = [
        "#input-mobile-search-medicament",
        'input[name="input-mobile-search-medicament"]',
        'input[type="search"][placeholder="Rechercher"]',
        'input[placeholder="Rechercher"]'
    ]

    for selector in selectors:

        elements = driver.find_elements(
            By.CSS_SELECTOR,
            selector
        )

        for element in elements:

            if element.is_displayed() and element.is_enabled():
                search = element
                break

        if search:
            break

    if search is None:
        print("Search input not found.")
        return False

    search.clear()
    search.send_keys(drug)

    print(f"\nSearching for: {drug}")

    # Submit search
    try:
        form = search.find_element(
            By.XPATH,
            "./ancestor::form[1]"
        )

        buttons = form.find_elements(
            By.CSS_SELECTOR,
            'button[type="submit"]'
        )

        if buttons:
            buttons[0].click()
        else:
            search.send_keys(Keys.ENTER)

    except Exception:
        search.send_keys(Keys.ENTER)

    # Wait for result table
    try:
        wait.until(
            EC.presence_of_element_located(
                (By.ID, TABLE_ID)
            )
        )

        wait.until(
            lambda d: (
                len(d.find_elements(
                    By.CSS_SELECTOR,
                    LINK_SELECTOR
                )) > 0
                or "aucun résultat" in d.page_source.lower()
                or "aucun médicament" in d.page_source.lower()
            )
        )

        print("Results page loaded.")
        return True

    except TimeoutException:
        print("Results not detected.")
        return False


# ==========================================
# 2. EXTRACT LINKS FROM ALL PAGES
# ==========================================


def extract_medication_links(driver):

    wait = WebDriverWait(driver, 30)

    all_links = []
    seen_links = set()
    visited_pages = set()

    page_number = 1

    def get_page_links():
        # Read URLs directly from the DOM to avoid stale elements.
        return driver.execute_script("""
            return Array.from(
                document.querySelectorAll(
                    '#table-accordeon-fetch-result tbody a[href^="/medicament/"][href$="/extrait"]'
                )
            ).map(a => a.href);
        """)

    def get_current_page():
        return driver.execute_script("""
            const active = document.querySelector(
                '#table-accordeon-fetch-result_wrapper .fr-pagination__link.current'
            );

            return active
                ? active.getAttribute('data-dt-idx')
                : null;
        """)

    while True:

        wait.until(
            EC.presence_of_element_located(
                (By.ID, "table-accordeon-fetch-result")
            )
        )

        # Wait until DataTables finishes processing.
        wait.until(
            lambda d: d.execute_script("""
                const processing = document.querySelector(
                    '#table-accordeon-fetch-result_processing'
                );

                return !processing ||
                       getComputedStyle(processing).display === 'none';
            """)
        )

        page_links = get_page_links()
        current_page = get_current_page()

        if not page_links:
            print("No links found.")
            break

        signature = (current_page, tuple(page_links))

        if signature in visited_pages:
            print("Page already visited. Stopping.")
            break

        visited_pages.add(signature)

        for link in page_links:

            if link not in seen_links:
                seen_links.add(link)
                all_links.append(link)

        print(
            f"Page {page_number}: "
            f"{len(page_links)} links found"
        )

        # Get next-page status from DOM.
        next_status = driver.execute_script("""
            const next = document.querySelector(
                '#table-accordeon-fetch-result_wrapper a[data-dt-idx="next"]'
            );

            if (!next) {
                return {exists: false, disabled: true};
            }

            const parent = next.parentElement;

            return {
                exists: true,
                disabled:
                    next.classList.contains('disabled') ||
                    next.getAttribute('aria-disabled') === 'true' ||
                    (parent && parent.classList.contains('disabled'))
            };
        """)

        if not next_status["exists"] or next_status["disabled"]:
            print("Last page reached.")
            break

        old_page = current_page
        old_links = tuple(page_links)

        # Re-find button each time.
        next_button = wait.until(
            EC.element_to_be_clickable((
                By.CSS_SELECTOR,
                '#table-accordeon-fetch-result_wrapper a[data-dt-idx="next"]'
            ))
        )

        driver.execute_script(
            "arguments[0].click();",
            next_button
        )

        try:
            # Wait for the actual data/page change.
            wait.until(
                lambda d: (
                    get_current_page() != old_page
                    or tuple(get_page_links()) != old_links
                )
            )

        except TimeoutException:
            print("Next page did not change.")
            break

        page_number += 1

    print("\n========== ALL MEDICATION LINKS ==========")

    for index, link in enumerate(all_links, start=1):
        print(f"{index}. {link}")

    print("\nTotal links:", len(all_links))

    return all_links


    wait = WebDriverWait(driver, 20)

    all_links = []
    seen_links = set()
    visited_pages = set()

    page_number = 1

    while True:

        # Wait for table
        wait.until(
            EC.presence_of_element_located(
                (By.ID, TABLE_ID)
            )
        )

        # Read all medication links
        elements = driver.find_elements(
            By.CSS_SELECTOR,
            LINK_SELECTOR
        )

        page_links = []

        for element in elements:

            href = element.get_attribute("href")

            if not href:
                continue

            full_url = urljoin(BASE_URL, href)

            page_links.append(full_url)

            if full_url not in seen_links:

                seen_links.add(full_url)
                all_links.append(full_url)

        # Avoid infinite loop
        page_signature = tuple(page_links)

        if not page_links:
            print("No medication links on this page.")
            break

        if page_signature in visited_pages:
            print("Page already visited. Stopping.")
            break

        visited_pages.add(page_signature)

        print(
            f"Page {page_number}: "
            f"{len(page_links)} links found"
        )

        # Find next page button
        next_buttons = driver.find_elements(
            By.CSS_SELECTOR,
            NEXT_SELECTOR
        )

        if not next_buttons:
            print("No next-page button.")
            break

        next_button = next_buttons[0]

        # Check whether the next button is disabled
        parent_class = next_button.find_element(
            By.XPATH,
            ".."
        ).get_attribute("class") or ""

        button_class = next_button.get_attribute(
            "class"
        ) or ""

        aria_disabled = next_button.get_attribute(
            "aria-disabled"
        )

        if (
            "disabled" in button_class.lower()
            or "disabled" in parent_class.lower()
            or aria_disabled == "true"
        ):
            print("Last page reached.")
            break

        # Save current page before clicking
        old_signature = page_signature

        # Click next page
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});",
            next_button
        )

        next_button.click()

        # Wait until page content changes
        try:
            wait.until(
                lambda d: tuple(
                    element.get_attribute("href")
                    for element in d.find_elements(
                        By.CSS_SELECTOR,
                        LINK_SELECTOR
                    )
                ) != old_signature
            )

        except TimeoutException:
            print("Next page did not load.")
            break

        page_number += 1

        time.sleep(0.5)

    print("\n=================================")
    print("ALL MEDICATION LINKS")
    print("=================================")

    for index, link in enumerate(all_links, start=1):
        print(f"{index}. {link}")

    print("\nTotal links:", len(all_links))

    return all_links


# ==========================================
# 3. MAIN
# ==========================================


def main():

    driver = webdriver.Chrome()
    driver.maximize_window()

    try:
        # Reprendre après Tramadol
        start_drug = "paracétamol + codéine"

        start_index = next(
            i for i, drug in enumerate(DRUG)
            if drug.strip().lower() == start_drug.lower()
        )

        # Start from Paracétamol + Codéine
        for drug in DRUG[start_index:]:

            nom_fichier = drug
            print(f"\n========== {drug} ==========")

            try:
                # 1. Search medication
                if not search_medication(driver, drug):
                    print(f"No results for: {drug}")
                    continue

                # 2. Extract all medication URLs
                medication_links = extract_medication_links(driver)

                print(f"{drug}: {len(medication_links)} links found")

                # 3. Download documents for each medication
                for index, url in enumerate(medication_links, start=1):

                    match = re.search(
                        r"/medicament/(\d+)/",
                        url
                    )

                    if not match:
                        continue

                    medication_id = match.group(1)

                    print(
                        f"\n[{index}/{len(medication_links)}] "
                        f"Downloading: {url}"
                    )

                    try:
                        telecharger_documents(
                            url,
                            nom_fichier,
                            medication_id
                        )

                    except Exception as error:
                        print(f"Download error: {error}")

            except Exception as error:
                print(f"Error processing {drug}: {error}")

    finally:
        driver.quit()
        print("\nChrome closed automatically.")


if __name__ == "__main__":
    main()
