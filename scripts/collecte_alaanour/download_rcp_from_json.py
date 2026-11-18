import json
import requests
import re
from pathlib import Path


def download_all_rcp(json_folder, output_folder):

    json_folder = Path("data/row_data/json")
    output_folder = Path("data/row_data/Pdf")

    # إنشاء dossier PDF
    output_folder.mkdir(parents=True, exist_ok=True)

    downloaded = 0
    not_found = 0
    errors = 0

    # Loop sur tous les fichiers JSON
    json_files = list(json_folder.glob("*.json"))

    print(f"Nombre de fichiers JSON : {len(json_files)}")

    for json_file in json_files:

        print(f"\nLecture : {json_file.name}")

        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # إذا كان JSON يحتوي على fiche واحدة
            if isinstance(data, dict):
                data = [data]

            # Loop sur les médicaments
            for i, medicament in enumerate(data, start=1):

                rcp_url = medicament.get("RCP PDF")

                nom = medicament.get(
                    "Nom de marque",
                    f"{json_file.stem}_{i}"
                )

                if not rcp_url:
                    print(f"[NON TROUVE] {nom}")
                    not_found += 1
                    continue

                try:
                    print(f"[DOWNLOAD] {nom}")

                    response = requests.get(
                        rcp_url,
                        headers={"User-Agent": "Mozilla/5.0"},
                        timeout=30
                    )

                    response.raise_for_status()

                    # Vérifier que le fichier est un PDF
                    if not response.content.startswith(b"%PDF"):
                        print(f"[ERREUR] Ce lien ne contient pas un PDF : {nom}")
                        errors += 1
                        continue

                    # Nom du fichier sans caractères interdits
                    safe_name = re.sub(r'[<>:"/\\|?*]', "_", str(nom))

                    pdf_path = output_folder / f"{safe_name}.pdf"

                    # Éviter de remplacer un PDF déjà téléchargé
                    if pdf_path.exists():
                        print(f"[EXISTE DEJA] {safe_name}.pdf")
                        continue

                    with open(pdf_path, "wb") as pdf:
                        pdf.write(response.content)

                    print(f"[OK] {pdf_path}")
                    downloaded += 1

                except requests.RequestException as e:
                    print(f"[ERREUR DOWNLOAD] {nom}: {e}")
                    errors += 1

        except (json.JSONDecodeError, OSError) as e:
            print(f"[ERREUR JSON] {json_file.name}: {e}")
            errors += 1

    print("\n========== RESULTAT FINAL ==========")
    print(f"JSON lus              : {len(json_files)}")
    print(f"PDF téléchargés       : {downloaded}")
    print(f"RCP non disponibles   : {not_found}")
    print(f"Erreurs               : {errors}")


# Exécution
download_all_rcp(
    "json_folder",
    "output_folder"
)