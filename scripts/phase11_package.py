#!/usr/bin/env python3
"""
Fase 11: Empacotamento Final (.mcpack, .mcworld, .mcaddon e SHA-256) (Seção 34).
Autor: João Lucas Mayrinck
"""

import os
import sys
import zipfile
import hashlib

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

def sha256_file(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def zip_directory(source_dir: str, target_file: str):
    with zipfile.ZipFile(target_file, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(source_dir):
            for file in files:
                full_p = os.path.join(root, file)
                rel_p = os.path.relpath(full_p, source_dir).replace("\\", "/")
                z.write(full_p, rel_p)

def build_mcaddon(bp_dir: str, rp_dir: str, target_addon: str):
    """Cria o pacote .mcaddon contendo os pacotes de comportamento e recursos unificados."""
    with zipfile.ZipFile(target_addon, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(bp_dir):
            for file in files:
                full_p = os.path.join(root, file)
                rel_p = "behavior_pack/" + os.path.relpath(full_p, bp_dir).replace("\\", "/")
                z.write(full_p, rel_p)
        for root, _, files in os.walk(rp_dir):
            for file in files:
                full_p = os.path.join(root, file)
                rel_p = "resource_pack/" + os.path.relpath(full_p, rp_dir).replace("\\", "/")
                z.write(full_p, rel_p)

def main():
    print("=================================================================")
    print(" FASE 11: EMPACOTAMENTO DOS ARTEFATOS FINAIS (SEÇÃO 34) ")
    print("=================================================================")

    rp_dir = os.path.join(OUTPUT_DIR, "resource_pack")
    bp_dir = os.path.join(OUTPUT_DIR, "behavior_pack")
    world_dir = os.path.join(OUTPUT_DIR, "converted_world")

    # Auto-detecta o nome do mundo a partir do analysis/world_structure.json
    analysis_file = os.path.join(BASE_DIR, "analysis", "world_structure.json")
    world_name = "Mazescapist"
    if os.path.exists(analysis_file):
        try:
            with open(analysis_file, "r", encoding="utf-8") as f:
                w_struct = json.load(f)
                raw_n = w_struct.get("level_info", {}).get("LevelName", "Mazescapist")
                import re
                clean_n = re.sub(r'§.', '', raw_n).strip()
                if clean_n:
                    world_name = clean_n
        except Exception:
            pass

    # Limpeza de arquivos de compilações antigas/obsoletas para evitar duplicatas
    stale_files = [
        os.path.join(OUTPUT_DIR, "converted_resource_pack.mcpack"),
        os.path.join(OUTPUT_DIR, "converted_behavior_pack.mcpack"),
        os.path.join(OUTPUT_DIR, "converted_map.mcworld"),
        os.path.join(OUTPUT_DIR, "converted_map.mcaddon"),
    ]
    for sf in stale_files:
        if os.path.exists(sf):
            try:
                os.remove(sf)
            except Exception:
                pass

    final_rp = os.path.join(OUTPUT_DIR, f"{world_name}_RP.mcpack")
    final_bp = os.path.join(OUTPUT_DIR, f"{world_name}_BP.mcpack")
    final_world = os.path.join(OUTPUT_DIR, f"{world_name}.mcworld")
    final_addon = os.path.join(OUTPUT_DIR, f"{world_name}.mcaddon")

    print(f"[*] Empacotando Resource Pack (.mcpack) -> {os.path.basename(final_rp)}...")
    zip_directory(rp_dir, final_rp)
    print(f"    [OK] {final_rp} ({os.path.getsize(final_rp) / 1024:.2f} KB)")

    print(f"[*] Empacotando Behavior Pack (.mcpack) -> {os.path.basename(final_bp)}...")
    zip_directory(bp_dir, final_bp)
    print(f"    [OK] {final_bp} ({os.path.getsize(final_bp) / 1024:.2f} KB)")

    print(f"[*] Empacotando Mundo Bedrock (.mcworld) -> {os.path.basename(final_world)}...")
    zip_directory(world_dir, final_world)
    print(f"    [OK] {final_world} ({os.path.getsize(final_world) / 1024 / 1024:.2f} MB)")

    print(f"[*] Empacotando Pacote Unificado (.mcaddon) -> {os.path.basename(final_addon)}...")
    build_mcaddon(bp_dir, rp_dir, final_addon)
    print(f"    [OK] {final_addon} ({os.path.getsize(final_addon) / 1024:.2f} KB)")

    # Checksums
    checksum_file = os.path.join(OUTPUT_DIR, "SHA256SUMS.txt")
    artifacts = [final_world, final_addon, final_bp, final_rp]
    print("\n[*] Gravando checksums SHA-256...")
    with open(checksum_file, "w", encoding="utf-8") as f:
        f.write("# Checksums SHA-256 dos artefatos finais Bedrock 1.20+\n")
        for art in artifacts:
            csum = sha256_file(art)
            bname = os.path.basename(art)
            f.write(f"{csum} *{bname}\n")
            print(f"    {bname}: {csum}")

    print(f"\n[SUCESSO] Empacotamento concluído com sucesso em: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()

