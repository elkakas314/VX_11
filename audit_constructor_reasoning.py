import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add repo root to sys.path
repo_root = Path(__file__).resolve().parent
sys.path.append(str(repo_root))

# Cargar tokens.env explícitamente
load_dotenv(repo_root / "tokens.env")

from config.settings import settings
from config.deepseek import call_deepseek_reasoner
import json


def main():
    # Forzar la clave en settings
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if api_key:
        settings.deepseek_api_key = api_key
    else:
        print("ERROR: DEEPSEEK_API_KEY no encontrada.")
        return

    # Leer el TXT de auditoría
    txt_path = repo_root / "docs/audit/vx11_contructor.txt"
    with open(txt_path, "r") as f:
        audit_txt = f.read()

    # Leer el CANONICAL_FS del ZIP extraído
    fs_path = repo_root / "docs/audit/extracted_constructor/CANONICAL_FS_VX11.json"
    with open(fs_path, "r") as f:
        canonical_fs = f.read()

    prompt = f"""
    Analiza los siguientes documentos de auditoría de VX11 (Constructor):
    
    --- TXT DE AUDITORÍA (Resumen) ---
    {audit_txt[:4000]} ... (truncado)
    
    --- CANONICAL_FS_VX11.json (del ZIP) ---
    {canonical_fs[:2000]} ... (truncado)
    
    Tarea:
    1. Identifica qué se tuvo que hacer para integrar Manifestator y Shub-Niggurath.
    2. Busca evidencias de fallos o "gaps" mencionados (ej. input gaps, discrepancias con DOCX).
    3. Razona sobre el estado de Hormiguero: ¿por qué hay tantos archivos en 'attic/' según el FS?
    4. Propón mejoras quirúrgicas para los tests de Hormiguero y Manifestator basadas en estos hallazgos.
    
    Responde con un análisis quirúrgico y recomendaciones técnicas.
    """

    print("Invocando DeepSeek R1 para auditoría profunda...")
    result, latency, confidence = call_deepseek_reasoner(prompt, task_type="deep_audit")

    if result.get("provider") == "deepseek-r1":
        print(f"\n[LATENCIA: {latency:.2f}ms] [CONFIANZA: {confidence}]\n")
        print("--- RAZONAMIENTO (THOUGHT) ---")
        print(result.get("reasoning", "No reasoning provided"))
        print("\n--- ANÁLISIS DE AUDITORÍA ---")
        print(result.get("text", "No text provided"))
    else:
        print("\n--- ERROR ---")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
