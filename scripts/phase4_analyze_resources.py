#!/usr/bin/env python3
"""
Fase 4: Análise Aprofundada do Resource Pack Java Edition e Plano de Conversão
Autor: João Lucas Mayrinck
"""

import os
import sys
import json
import struct

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ANALYSIS_DIR = os.path.join(BASE_DIR, "analysis")
RP_DIR = os.path.join(BASE_DIR, "extracted", "java_resource_pack")

def get_png_dimensions(file_path: str):
    try:
        with open(file_path, "rb") as f:
            header = f.read(24)
            if header.startswith(b"\x89PNG\r\n\x1a\n"):
                w, h = struct.unpack(">II", header[16:24])
                return w, h
    except Exception:
        pass
    return None, None

def main():
    print("[*] Analisando estrutura do Resource Pack em:", RP_DIR)
    
    # 1. pack.mcmeta
    mcmeta_path = os.path.join(RP_DIR, "pack.mcmeta")
    mcmeta = {}
    if os.path.exists(mcmeta_path):
        with open(mcmeta_path, "r", encoding="utf-8") as f:
            mcmeta = json.load(f)
    print(f"    [OK] pack.mcmeta: {mcmeta.get('pack', {})}")

    # 2. Texturas
    textures = []
    for root, _, files in os.walk(RP_DIR):
        for f in files:
            if f.endswith(".png"):
                full_p = os.path.join(root, f)
                rel_p = os.path.relpath(full_p, RP_DIR).replace("\\", "/")
                w, h = get_png_dimensions(full_p)
                size = os.path.getsize(full_p)
                textures.append({"path": rel_p, "width": w, "height": h, "size": size})
    print(f"    [OK] Total de texturas PNG: {len(textures)}")

    # 3. Modelos e Blockstates
    blockstates = []
    models = []
    for root, _, files in os.walk(RP_DIR):
        for f in files:
            if f.endswith(".json"):
                full_p = os.path.join(root, f)
                rel_p = os.path.relpath(full_p, RP_DIR).replace("\\", "/")
                if "blockstates" in rel_p:
                    try:
                        with open(full_p, "r", encoding="utf-8") as jf:
                            js = json.load(jf)
                        blockstates.append({"path": rel_p, "variants": list(js.get("variants", {}).keys())})
                    except Exception:
                        pass
                elif "models" in rel_p:
                    try:
                        with open(full_p, "r", encoding="utf-8") as jf:
                            js = json.load(jf)
                        models.append({"path": rel_p, "parent": js.get("parent"), "textures": js.get("textures")})
                    except Exception:
                        pass
    print(f"    [OK] Blockstates: {len(blockstates)} | Modelos JSON: {len(models)}")

    # 4. Sons
    sounds = []
    for root, _, files in os.walk(RP_DIR):
        for f in files:
            if f.endswith((".ogg", ".wav", ".fsb")):
                full_p = os.path.join(root, f)
                rel_p = os.path.relpath(full_p, RP_DIR).replace("\\", "/")
                sounds.append({"path": rel_p, "size": os.path.getsize(full_p)})
    print(f"    [OK] Arquivos de som: {len(sounds)}")

    # 5. Gerar analysis/resources_report.md
    print("[*] Gerando analysis/resources_report.md...")
    rp_lines = [
        "# Relatório de Análise do Resource Pack Java Edition",
        "",
        f"- **Formato do Pacote (pack_format)**: {mcmeta.get('pack', {}).get('pack_format', 'N/A')}",
        f"- **Descrição**: {mcmeta.get('pack', {}).get('description', 'N/A')}",
        f"- **Total de Texturas**: {len(textures)}",
        f"- **Total de Sons**: {len(sounds)}",
        f"- **Total de Modelos/Blockstates**: {len(models) + len(blockstates)}",
        "",
        "## Texturas Identificadas",
        "",
        "| Caminho Java | Resolução | Tamanho | Mapeamento Bedrock |",
        "| :--- | :---: | :---: | :--- |"
    ]
    for tex in textures:
        mapping = "textures/blocks/bedrock" if "bedrock" in tex["path"] else "textures/blocks/..."
        rp_lines.append(f"| `{tex['path']}` | {tex['width']}x{tex['height']} | {tex['size']} B | `{mapping}` |")

    rp_lines.extend([
        "",
        "## Blockstates e Modelos",
        "",
        "| Arquivo | Tipo | Detalhes |",
        "| :--- | :---: | :--- |"
    ])
    for bs in blockstates:
        rp_lines.append(f"| `{bs['path']}` | Blockstate | Variantes: {bs['variants']} |")
    for m in models:
        rp_lines.append(f"| `{m['path']}` | Modelo | Parent: `{m['parent']}` |")

    rp_lines.extend([
        "",
        "## Sons Identificados",
        "",
        "| Arquivo de Áudio | Tamanho | Categoria Java |",
        "| :--- | :---: | :--- |"
    ])
    for s in sounds:
        rp_lines.append(f"| `{s['path']}` | {s['size']} B | Som customizado de ambiente/mob |")

    with open(os.path.join(ANALYSIS_DIR, "resources_report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(rp_lines) + "\n")

    # 6. Gerar analysis/conversion_plan.md
    print("[*] Gerando analysis/conversion_plan.md...")
    plan_lines = [
        "# Plano Estratégico de Conversão Java -> Bedrock (Seção 2 e 42)",
        "",
        "## 1. Estratégia de Recursos (Resource Pack)",
        "- **Texturas de Tijolos Bedrock**: Converter variações de `blockstates/bedrock.json` para entradas ponderadas no `terrain_texture.json` com chave `\"bedrock\"` e gerar `blocks.json` e fallback `bedrock.png`.",
        "- **Sons**: Mapear arquivos `.ogg` para a árvore nativa `sounds/` do Bedrock e registrar entradas em `sound_definitions.json`.",
        "- **Manifest**: Versão do manifesto format_version 2, com `min_engine_version: [1, 20, 0]` e UUIDs RFC4122 v5 estáveis.",
        "",
        "## 2. Estratégia de Comandos e Datapacks (Behavior Pack)",
        "- **Parser AST**: Analisar tokens de comandos Java e gerar nós intermediários.",
        "- **Subcomandos de Execute**: Traduzir sintaxe 1.16.5 para Bedrock 1.20+ (`as`, `at`, `positioned`, `if entity`).",
        "- **Seletores**: Substituir `distance=..X` por `r=X`, `distance=X..Y` por `rm=X,r=Y`, `sort=nearest,limit=1` por `c=1`.",
        "- **Forceload**: Traduzir coordenadas para `tickingarea add/remove` com bounding box calculada.",
        "- **Spawners**: Converter `/data merge block ... {Delay:0}` para `/setblock ... mob_spawner`.",
        "- **Aldeões e Trocas**: Extrair NBT de ofertas e gerar arquivos de trading (`trading/*.json`) e entidades customizadas.",
        "- **Funções e Ciclos**: Organizar funções em `behavior_pack/functions/` e configurar inicialização em `tick.json`.",
        "",
        "## 3. Estratégia do Mundo (LevelDB Injection)",
        "- **Preservação de Command Blocks**: Manter os 641 blocos de comando nas posições originais no mundo Bedrock.",
        "- **Atualização In-Place**: Ler blocos SSTable do LevelDB (`.ldb`), descomprimir formato tipo 4 da Mojang, substituir os comandos pela versão traduzida e recalcular o CRC32C mascarado.",
        "- **Integração de Pacotes**: Inserir referências de pacotes em `world_behavior_packs.json` e `world_resource_packs.json`.",
        "",
        "## 4. Validação e Empacotamento",
        "- **Verificação de Resíduos**: Garantir 0 ocorrências de comandos com sintaxe Java inválida (`distance=`, `predicate=`, etc.).",
        "- **Empacotamento Múltiplo**: Gerar `.mcworld` autônomo, `.mcpack` de recursos, `.mcpack` de comportamento e pacote unificado `.mcaddon`."
    ]
    with open(os.path.join(ANALYSIS_DIR, "conversion_plan.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(plan_lines) + "\n")

    print("[SUCESSO] Relatórios gerados com sucesso na pasta analysis/:")
    print("    - analysis/resources_report.md")
    print("    - analysis/conversion_plan.md")

if __name__ == "__main__":
    main()

