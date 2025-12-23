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
        print(f"Clave cargada: {api_key[:5]}...{api_key[-5:]}")
    else:
        print("ERROR: DEEPSEEK_API_KEY no encontrada en el entorno.")
        return

    prompt = """
    VX11 Status Report:
    - Madre: Power API implemented and verified.
    - Spawner: Daughter lifecycle verified.
    - Tentaculo Link: 8/8 modules healthy, E2E routing verified.
    - Switch: Task queue persistence fixed (added 'result' and 'updated_at' columns).
    - Hermes: Internal execution verified.
    
    Task:
    Reason about the next logical step for the 'Auditoría Exhaustiva por Módulo'. 
    Consider:
    1. Hormiguero (State management)
    2. Shubniggurath (Audio/DSP)
    3. MCP (Model Context Protocol)
    4. E2E Flow: Spawn Chain (Daughter triggering another spawn)
    
    Provide a surgical recommendation.
    """

    print("Calling DeepSeek R1 (Reasoner) for architectural analysis...")
    result, latency, confidence = call_deepseek_reasoner(prompt, task_type="architectural_audit")

    if result.get("provider") == "deepseek-r1":
        print(f"\n[LATENCIA: {latency:.2f}ms] [CONFIANZA: {confidence}]\n")
        print("--- RAZONAMIENTO (THOUGHT) ---")
        print(result.get("reasoning", "No reasoning provided"))
        print("\n--- RESPUESTA FINAL ---")
        print(result.get("text", "No text provided"))
    else:
        print("\n--- FALLBACK LOCAL / ERROR ---")
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
