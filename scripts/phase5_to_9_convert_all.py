#!/usr/bin/env python3
"""
Fases 5 a 9: Conversão Integrada de Recursos, Comandos, Pacotes e Injeção no LevelDB
Autor: João Lucas Mayrinck
"""

import os
import sys
import json
import zipfile
import shutil
import re

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from converter.resource_pack.rp_generator import ResourcePackGenerator
from converter.behavior_pack.bp_generator import BehaviorPackGenerator
from converter.commands.translator import CommandTranslator
from converter.world.leveldb_manager import BedrockLevelDBManager

def main():
    print("=================================================================")
    print(" INICIANDO FASES 5 A 9: CONVERSÃO DE RECURSOS, COMANDOS E MUNDO ")
    print("=================================================================")

    analysis_file = os.path.join(BASE_DIR, "analysis", "world_structure.json")
    world_name = "ConvertedWorld"
    safe_name = "converted_world"
    if os.path.exists(analysis_file):
        with open(analysis_file, "r", encoding="utf-8") as f:
            w_struct = json.load(f)
            raw_n = w_struct.get("level_info", {}).get("LevelName", "ConvertedWorld")
            world_name = re.sub(r'§.', '', raw_n).strip() or "ConvertedWorld"
            safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', world_name).strip('_').lower() or "converted_world"

    print(f"[*] Nome do Mundo: {world_name} (Slug: {safe_name})")

    extracted_world = os.path.join(BASE_DIR, "extracted", "java_world")
    extracted_rp = os.path.join(BASE_DIR, "extracted", "java_resource_pack")
    output_dir = os.path.join(BASE_DIR, "output")
    os.makedirs(output_dir, exist_ok=True)

    target_rp = os.path.join(output_dir, "resource_pack")
    target_bp = os.path.join(output_dir, "behavior_pack")
    target_world = os.path.join(output_dir, "converted_world")

    # 1. Fase 5: Conversão de Recursos (Resource Pack)
    print("\n[*] [FASE 5] Gerando Resource Pack Bedrock em:", target_rp)
    rp_meta = ResourcePackGenerator.generate(extracted_rp, target_rp, world_name, safe_name)
    print(f"    [OK] Resource Pack gerado com sucesso ({rp_meta['textures_count']} texturas, variações: {rp_meta['has_variations']})")
    print(f"    [OK] UUID do RP Header: {rp_meta['header_uuid']}")

    # 2. Fases 6, 7 e 8: Conversão de Comandos e Geração do Behavior Pack
    print("\n[*] [FASES 6, 7 e 8] Gerando Behavior Pack Bedrock em:", target_bp)
    dp_dir = os.path.join(extracted_world, "datapacks")
    bp_meta = BehaviorPackGenerator.generate(dp_dir, target_bp, world_name, safe_name, rp_meta["header_uuid"])
    print(f"    [OK] Behavior Pack gerado com sucesso ({bp_meta['functions_count']} funções convertidas)")
    print(f"    [OK] NPCs identificados e registrados: {bp_meta['known_npcs']}")
    print(f"    [OK] UUID do BP Header: {bp_meta['header_uuid']}")

    # 3. Fase 9: Conversão do Mundo Bedrock (LevelDB Injection)
    print("\n[*] [FASE 9] Preparando e Atualizando Mundo Bedrock em:", target_world)
    base_bedrock = os.path.join(BASE_DIR, "input", "bedrock-version.mcworld")
    if not os.path.exists(base_bedrock):
        base_bedrock = os.path.join(BASE_DIR, "inputs", "bedrock-version.mcworld")

    if not os.path.exists(base_bedrock):
        print(f"[ERRO] Base Bedrock não encontrada em inputs/bedrock-version.mcworld")
        sys.exit(1)

    if os.path.exists(target_world):
        shutil.rmtree(target_world)
    print(f"    -> Extraindo base Bedrock de {base_bedrock}...")
    with zipfile.ZipFile(base_bedrock, "r") as z:
        z.extractall(target_world)

    # Injeção in-place dos comandos traduzidos no LevelDB
    db_dir = os.path.join(target_world, "db")
    print("    -> Atualizando blocos de comando diretamente no banco LevelDB (.ldb)...")
    known_npcs_set = set(bp_meta["known_npcs"])
    modified_cbs = BedrockLevelDBManager.update_command_blocks(
        db_dir,
        lambda cmd: CommandTranslator.translate(cmd, known_npcs_set, safe_name)
    )
    print(f"    [OK] Total de blocos de comando convertidos e atualizados no LevelDB: {modified_cbs}")

    # Integração de pacotes no mundo Bedrock
    print("    -> Integrando Behavior Pack e Resource Pack dentro do mundo...")
    bp_dest = os.path.join(target_world, "behavior_packs", f"{safe_name}_bp")
    rp_dest = os.path.join(target_world, "resource_packs", f"{safe_name}_rp")
    if os.path.exists(bp_dest):
        shutil.rmtree(bp_dest)
    if os.path.exists(rp_dest):
        shutil.rmtree(rp_dest)
    shutil.copytree(target_bp, bp_dest)
    shutil.copytree(target_rp, rp_dest)

    world_bp = [{"pack_id": bp_meta["header_uuid"], "version": [1, 0, 0]}]
    world_rp = [{"pack_id": rp_meta["header_uuid"], "version": [1, 0, 0]}]

    with open(os.path.join(target_world, "world_behavior_packs.json"), "w", encoding="utf-8") as f:
        json.dump(world_bp, f, indent=2)
    with open(os.path.join(target_world, "world_resource_packs.json"), "w", encoding="utf-8") as f:
        json.dump(world_rp, f, indent=2)

    print("\n=================================================================")
    print(" FASES 5 A 9 CONCLUÍDAS COM SUCESSO!")
    print("=================================================================")

if __name__ == "__main__":
    main()

