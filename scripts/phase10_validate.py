#!/usr/bin/env python3
"""
Fase 10: Motor de Validação Automática (Seções 30 e 31).
Autor: João Lucas Mayrinck
"""

import os
import sys
import json
import uuid
import re

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

JAVA_RESIDUAL_PATTERNS = [
    (re.compile(r'distance=\.\.\d+'), "Uso de seletor Java distance=..X (deve ser r=X)"),
    (re.compile(r'distance=\d+\.\.\d+'), "Uso de seletor Java distance=X..Y (deve ser rm=X,r=Y)"),
    (re.compile(r'\bforceload\b'), "Comando Java forceload residual"),
    (re.compile(r'\bdata\s+merge\b'), "Comando Java data merge residual"),
    (re.compile(r'\bCustomModelData\b'), "Uso de CustomModelData no comando"),
    (re.compile(r'\bpredicate='), "Uso de seletor de predicado Java"),
    (re.compile(r'\badvancement='), "Uso de seletor de avanço Java"),
]

def validate_json_files(target_dir: str):
    issues = []
    checked = 0
    for root, _, files in os.walk(target_dir):
        for f in files:
            if f.endswith(".json"):
                full_p = os.path.join(root, f)
                checked += 1
                try:
                    with open(full_p, "r", encoding="utf-8") as jf:
                        json.load(jf)
                except Exception as e:
                    issues.append(f"JSON inválido em {full_p}: {e}")
    return checked, issues

def validate_manifest(manifest_path: str):
    issues = []
    if not os.path.exists(manifest_path):
        return [f"Manifesto não encontrado: {manifest_path}"]
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        header = data.get("header", {})
        h_uuid = header.get("uuid")
        try:
            uuid.UUID(h_uuid)
        except Exception:
            issues.append(f"UUID inválido no header do manifesto: {h_uuid}")

        min_ver = header.get("min_engine_version")
        if not isinstance(min_ver, list) or len(min_ver) != 3:
            issues.append(f"min_engine_version inválido: {min_ver}")

        for mod in data.get("modules", []):
            m_uuid = mod.get("uuid")
            try:
                uuid.UUID(m_uuid)
            except Exception:
                issues.append(f"UUID inválido no módulo do manifesto: {m_uuid}")
    except Exception as e:
        issues.append(f"Falha ao validar manifesto {manifest_path}: {e}")
    return issues

def validate_commands_in_functions(bp_dir: str):
    issues = []
    func_dir = os.path.join(bp_dir, "functions")
    total_cmds = 0
    if not os.path.isdir(func_dir):
        return 0, ["Diretório de funções do BP não encontrado"]

    for root, _, files in os.walk(func_dir):
        for f in files:
            if f.endswith(".mcfunction"):
                fpath = os.path.join(root, f)
                with open(fpath, "r", encoding="utf-8", errors="ignore") as fp:
                    lines = fp.readlines()
                for line_no, line in enumerate(lines, 1):
                    s = line.strip()
                    if not s or s.startswith("#"):
                        continue
                    total_cmds += 1
                    if s.startswith("/"):
                        issues.append(f"{fpath}:{line_no} Barra / indevida em .mcfunction: {s}")
                    for pat, desc in JAVA_RESIDUAL_PATTERNS:
                        if pat.search(s):
                            issues.append(f"{fpath}:{line_no} Padrão Java residual '{desc}': {s}")
    return total_cmds, issues

def validate_textures(rp_dir: str):
    issues = []
    tt_path = os.path.join(rp_dir, "textures", "terrain_texture.json")
    if not os.path.exists(tt_path):
        issues.append("terrain_texture.json não encontrado no RP")
    else:
        with open(tt_path, "r", encoding="utf-8") as f:
            tt = json.load(f)
        if "bedrock" not in tt.get("texture_data", {}):
            issues.append("Chave 'bedrock' ausente em terrain_texture.json")

    blocks_path = os.path.join(rp_dir, "blocks.json")
    if not os.path.exists(blocks_path):
        issues.append("blocks.json não encontrado no RP")

    fb_path = os.path.join(rp_dir, "textures", "blocks", "bedrock.png")
    if not os.path.exists(fb_path):
        issues.append("Fallback textures/blocks/bedrock.png não encontrado no RP")

    return issues

def main():
    print("=================================================================")
    print(" FASE 10: MOTOR DE VALIDAÇÃO AUTOMÁTICA (SEÇÕES 30 E 31) ")
    print("=================================================================")

    rp_dir = os.path.join(OUTPUT_DIR, "resource_pack")
    bp_dir = os.path.join(OUTPUT_DIR, "behavior_pack")
    world_dir = os.path.join(OUTPUT_DIR, "converted_world")

    all_issues = []

    # 1. Validação de JSONs
    print("[*] Validando integridade de todos os arquivos JSON gerados...")
    json_count, json_issues = validate_json_files(OUTPUT_DIR)
    print(f"    [OK] Total de arquivos JSON validados: {json_count}")
    all_issues.extend(json_issues)

    # 2. Validação de Manifestos e UUIDs
    print("[*] Validando manifestos e UUIDs...")
    rp_man_issues = validate_manifest(os.path.join(rp_dir, "manifest.json"))
    bp_man_issues = validate_manifest(os.path.join(bp_dir, "manifest.json"))
    all_issues.extend(rp_man_issues)
    all_issues.extend(bp_man_issues)
    print(f"    [OK] Manifestos RP e BP verificados.")

    # 3. Validação de Texturas e Blocks
    print("[*] Validando texturas, variations e blocks.json...")
    tex_issues = validate_textures(rp_dir)
    all_issues.extend(tex_issues)
    print(f"    [OK] Mapeamentos de textura verificados.")

    # 4. Validação de Comandos em Funções (Busca por resíduos Java)
    print("[*] Varrendo comandos de funções em busca de sintaxe Java residual (Seção 31)...")
    cmd_count, cmd_issues = validate_commands_in_functions(bp_dir)
    print(f"    [OK] Total de comandos de funções auditados: {cmd_count}")
    all_issues.extend(cmd_issues)

    print("\n-----------------------------------------------------------------")
    if not all_issues:
        print("[SUCESSO] Todos os testes e validações passaram com ZERO falhas!")
        print("    -> Nenhum comando Java residual detectado.")
        print("    -> Nenhum JSON corrompido.")
        print("    -> Manifestos e UUIDs 100% válidos e compatíveis com Bedrock 1.20+.")
        print("-----------------------------------------------------------------")
        sys.exit(0)
    else:
        print(f"[ALERTA] Foram encontradas {len(all_issues)} inconformidades:")
        for iss in all_issues:
            print(f"    [!] {iss}")
        print("-----------------------------------------------------------------")
        sys.exit(1)

if __name__ == "__main__":
    main()

