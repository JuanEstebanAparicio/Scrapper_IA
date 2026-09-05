# src/generate_usecases.py
import json
import os
import re
import sys
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

def detect_language(code):
    code = code.lower()
    if "import " in code or "def " in code or "print(" in code:
        return "python"
    if "function " in code or "const " in code or "=> " in code:
        return "javascript"
    if "<svg" in code or "<div" in code:
        return "html"
    return "unknown"

def make_script_template(usecase_title, lang, snippet):
    if lang == "python":
        return f"# {usecase_title}\n{snippet}\n"
    if lang == "javascript":
        return f"// {usecase_title}\n{snippet}\n"
    if lang == "html":
        return f"<!-- {usecase_title} -->\n{snippet}\n"
    return f"# {usecase_title}\n{snippet}\n"

def generate(usecase_count=3, source_file=None, lib_name=None):
    if source_file is None:
        files = list(DATA_DIR.glob("*.json"))
        if not files:
            raise FileNotFoundError("No hay archivos JSON en data/")
        source_file = files[0]

    data = json.load(open(source_file, encoding="utf-8"))
    blocks = data.get("blocks", [])
    lib_name = lib_name or data.get("meta", {}).get("url", "libreria")

    # Crear nombre de salida único según la librería
    lib_clean = Path(source_file).stem.split("_")[-1]
    OUT = DATA_DIR / f"usecases_{lib_clean}.json"

    usecases = []
    for i in range(usecase_count):
        snippet = blocks[i]["code"] if i < len(blocks) else f"# Ejemplo minimalista de {lib_name}"
        lang = detect_language(snippet)
        title = f"Caso de uso {i+1} - {lib_name}"
        desc = [
            "Ejemplo básico para entender la funcionalidad.",
            "Integración con una API o flujo externo.",
            "Automatización o pipeline de uso práctico."
        ][i % 3]
        script = make_script_template(title, lang, snippet)
        usecases.append({"title": title, "description": desc, "lang": lang, "script": script})

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(usecases, f, ensure_ascii=False, indent=2)
    print(f"Generados {len(usecases)} casos en {OUT}")

    # === Actualizar libraries.json automáticamente ===
    libraries_file = DATA_DIR / "libraries.json"
    libraries = []
    if libraries_file.exists():
        try:
            libraries = json.load(open(libraries_file, encoding="utf-8"))
        except Exception:
            libraries = []

    # Evitar duplicados
    if OUT.name not in libraries:
        libraries.append(OUT.name)

    with open(libraries_file, "w", encoding="utf-8") as f:
        json.dump(libraries, f, ensure_ascii=False, indent=2)
    print(f"Librerías actualizadas en {libraries_file}")

if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else None
    generate(source_file=src)
