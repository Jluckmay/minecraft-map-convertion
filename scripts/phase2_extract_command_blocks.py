#!/usr/bin/env python3
"""
Fase 2: Extração e Reconstrução de Cadeias de Command Blocks
Autor: João Lucas Mayrinck
"""

import os
import sys
import json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from converter.world.anvil_reader import AnvilReader

def main():
    world_dir = os.path.join(BASE_DIR, "extracted", "java_world")
    analysis_dir = os.path.join(BASE_DIR, "analysis")
    os.makedirs(analysis_dir, exist_ok=True)

    if not os.path.isdir(world_dir):
        print(f"[ERRO] Diretório do mundo não encontrado: {world_dir}. Execute phase1 primeiro.")
        sys.exit(1)

    print("[*] Iniciando varredura profunda de command blocks em todas as dimensões...")
    cbs = AnvilReader.scan_all_dimensions(world_dir)
    print(f"    [OK] Total de command blocks encontrados: {len(cbs)}")

    print("[*] Reconstruindo conexões em cadeia e ordem de execução (Seção 5 e 6)...")
    cbs_annotated, chains = AnvilReader.build_command_chains(cbs)
    print(f"    [OK] Total de cadeias/sistemas identificados: {len(chains)}")

    # Estatísticas
    type_counts = {}
    for cb in cbs:
        t = cb["type"]
        type_counts[t] = type_counts.get(t, 0) + 1

    report = {
        "total_command_blocks": len(cbs),
        "types": type_counts,
        "total_chains": len(chains),
        "chains_summary": [
            {
                "chain_id": c["chain_id"],
                "dimension": c["dimension"],
                "start_pos": c["start_pos"],
                "length": c["length"],
                "is_loop": c["is_loop"]
            }
            for c in chains
        ],
        "command_blocks": cbs_annotated,
        "systems": chains
    }

    out_file = os.path.join(analysis_dir, "command_blocks.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n[SUCESSO] Relatório de command blocks salvo em: {out_file}")
    for t, count in type_counts.items():
        print(f"    - {t}: {count}")

if __name__ == "__main__":
    main()

