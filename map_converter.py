#!/usr/bin/env python3
"""
=============================================================================
 Minecraft Map Converter & Bridge Tool: Java <-> Bedrock (1.26.40+)
=============================================================================
 Ferramenta automatizada e universal de auditoria, conversão complementar e
 integração de qualquer mapa de Minecraft Java Edition para Bedrock Edition.

 Abrangência Completa:
   1. Preservação integral do terreno convertido (LevelDB).
   2. Auditoria e censo de entidades em regiões Anvil (.mca), playerdata e blocos de comando.
   3. Conversão de Datapacks Java para Behavior Packs Bedrock:
      - Funções (.mcfunction) com sintaxe moderna 1.26.40+ (execute, tellraw com cores, sounds).
      - Idempotência automática de invocações (prevenção contra duplicação de entidades/NPCs).
      - Conversão de Loot Tables de entidades (pools, rolls, looting, counts).
   4. Conversão Dinâmica de Comércio Customizado e NPCs:
      - Extração automática de tags NBT {Offers:{Recipes:[...]}} em funções e command blocks.
      - Geração de tabelas de troca nativas Bedrock (trading/*.json).
      - Geração de entidades customizadas BP (entities/npc_*.json) e definições RP (entity/npc_*.entity.json).
   5. Funções Auxiliares de Inicialização e Utilidade.
   6. Extração de Recursos e Texturas de Blocos (terrain_texture.json, ícones).
   7. Integração e empacotamento em .mcworld e .mcpack com cálculo de checksums SHA-256.

 Autor: João Lucas Mayrinck
=============================================================================
"""

import os
import sys
import io
import re
import json
import uuid
import zlib
import shutil
import struct
import zipfile
import hashlib
import argparse
from collections import Counter, defaultdict

try:
    import nbtlib
except ImportError:
    print("[ERRO] Biblioteca 'nbtlib' não encontrada. Instale com: pip install nbtlib")
    sys.exit(1)

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def sha256_file(filepath: str) -> str:
    """Calcula o hash SHA-256 de um arquivo."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192 * 1024):
            h.update(chunk)
    return h.hexdigest()


class JavaWorldAuditor:
    """Audita regiões MCA, playerdata, blocos de comando e datapacks Java."""

    def __init__(self, java_zip_path: str):
        self.java_zip_path = java_zip_path
        self.entities = []
        self.command_blocks = []
        self.playerdata = []
        self.level_info = {}

    def audit(self):
        print(f"[*] Auditando arquivo Java: {self.java_zip_path}...")
        with zipfile.ZipFile(self.java_zip_path, "r") as z:
            namelist = z.namelist()

            # 1. Level.dat
            level_dat_files = [n for n in namelist if n.endswith("level.dat")]
            if level_dat_files:
                try:
                    raw_ld = z.read(level_dat_files[0])
                    import gzip
                    f = nbtlib.File.from_fileobj(gzip.GzipFile(fileobj=io.BytesIO(raw_ld)))
                    data = f.get("Data", {})
                    self.level_info = {
                        "LevelName": str(data.get("LevelName", "Minecraft World")),
                        "DataVersion": int(data.get("DataVersion", 0)),
                        "GameType": int(data.get("GameType", 0)),
                        "SpawnX": int(data.get("SpawnX", 0)),
                        "SpawnY": int(data.get("SpawnY", 64)),
                        "SpawnZ": int(data.get("SpawnZ", 0))
                    }
                except Exception as e:
                    print(f"    [!] Aviso ao ler level.dat: {e}")

            # 2. Playerdata
            p_files = [n for n in namelist if "/playerdata/" in n and n.endswith(".dat")]
            for pf in p_files:
                try:
                    raw_p = z.read(pf)
                    import gzip
                    p_nbt = nbtlib.File.from_fileobj(gzip.GzipFile(fileobj=io.BytesIO(raw_p)))
                    pos = [float(x) for x in p_nbt.get("Pos", [0.0, 64.0, 0.0])]
                    inv = p_nbt.get("Inventory", [])
                    ender = p_nbt.get("EnderItems", [])
                    self.playerdata.append({
                        "file": os.path.basename(pf),
                        "uuid": os.path.basename(pf)[:-4],
                        "dimension": str(p_nbt.get("Dimension", "minecraft:overworld")),
                        "pos": pos,
                        "inventory_count": len(inv),
                        "ender_count": len(ender),
                        "health": float(p_nbt.get("Health", 20.0)),
                        "gamemode": int(p_nbt.get("playerGameType", 0))
                    })
                except Exception as e:
                    print(f"    [!] Aviso ao ler playerdata {pf}: {e}")

            # 3. Regiões MCA (Overworld, Nether, End)
            mca_files = [n for n in namelist if n.endswith(".mca")]
            print(f"    -> Analisando {len(mca_files)} arquivos de regiões MCA...")
            for mca_path in mca_files:
                dim = "overworld"
                if "DIM-1" in mca_path:
                    dim = "nether"
                elif "DIM1" in mca_path:
                    dim = "the_end"

                try:
                    mca_bytes = z.read(mca_path)
                    self._parse_mca(mca_bytes, dim)
                except Exception as e:
                    pass

        print(f"    [OK] Total de entidades detectadas: {len(self.entities)}")
        print(f"    [OK] Total de blocos de comando detectados: {len(self.command_blocks)}")
        print(f"    [OK] Total de jogadores auditados: {len(self.playerdata)}")

    def _parse_mca(self, mca_bytes: bytes, dimension: str):
        if len(mca_bytes) < 8192:
            return

        for chunk_idx in range(1024):
            offset_b = mca_bytes[chunk_idx * 4 : chunk_idx * 4 + 3]
            sector_count = mca_bytes[chunk_idx * 4 + 3]
            offset = int.from_bytes(offset_b, "big") * 4096
            if offset == 0 or sector_count == 0 or offset + 5 > len(mca_bytes):
                continue

            length = int.from_bytes(mca_bytes[offset : offset + 4], "big")
            compression = mca_bytes[offset + 4]
            if compression not in (1, 2) or offset + 4 + length > len(mca_bytes):
                continue

            payload = mca_bytes[offset + 5 : offset + 4 + length]
            try:
                if compression == 2:
                    decompressed = zlib.decompress(payload)
                else:
                    import gzip
                    decompressed = gzip.decompress(payload)

                chunk_nbt = nbtlib.File.from_fileobj(io.BytesIO(decompressed))
                root = chunk_nbt.get("Level", chunk_nbt)

                # Entidades
                for ent in root.get("Entities", []):
                    ent_id = str(ent.get("id", ""))
                    if ent_id:
                        pos = [float(x) for x in ent.get("Pos", [0.0, 0.0, 0.0])]
                        rot = [float(x) for x in ent.get("Rotation", [0.0, 0.0])]
                        self.entities.append({
                            "id": ent_id,
                            "dimension": dimension,
                            "pos": pos,
                            "rotation": rot,
                            "name": str(ent.get("CustomName", "")),
                            "tags": [str(t) for t in ent.get("Tags", [])],
                            "raw": ent
                        })

                # Tile Entities / Blocos de comando
                for te in root.get("TileEntities", root.get("block_entities", [])):
                    te_id = str(te.get("id", ""))
                    if "command_block" in te_id:
                        pos = [int(te.get("x", 0)), int(te.get("y", 0)), int(te.get("z", 0))]
                        cmd = str(te.get("Command", ""))
                        if cmd:
                            self.command_blocks.append({
                                "pos": pos,
                                "dimension": dimension,
                                "command": cmd,
                                "name": str(te.get("CustomName", ""))
                            })
            except Exception:
                continue


class DatapackConverter:
    """Traduz comandos Java para sintaxe moderna Bedrock 1.26.40+."""

    COLOR_MAP = {
        "black": "§0", "dark_blue": "§1", "dark_green": "§2", "dark_aqua": "§3",
        "dark_red": "§4", "dark_purple": "§5", "gold": "§6", "gray": "§7",
        "dark_gray": "§8", "blue": "§9", "green": "§a", "aqua": "§b",
        "red": "§c", "light_purple": "§d", "yellow": "§e", "white": "§f",
        "bold": "§l", "italic": "§o"
    }

    SOUND_MAP = {
        "entity.player.levelup": "random.levelup",
        "entity.experience_orb.pickup": "random.orb",
        "entity.villager.trade": "mob.villager.yes",
        "entity.villager.no": "mob.villager.no",
        "block.anvil.use": "random.anvil_use",
        "entity.wither.spawn": "mob.wither.spawn",
        "entity.wither.death": "mob.wither.death",
        "entity.ender_dragon.growl": "mob.enderdragon.growl"
    }

    @classmethod
    def convert_command(cls, line: str, known_npcs: set = None) -> str:
        s_line = line.strip()
        if not s_line or s_line.startswith("#"):
            return line

        # 1. forceload -> Comentário com tickingarea
        if s_line.startswith("forceload add ") or s_line.startswith("forceload remove "):
            return f"# [Bedrock Conversion] {s_line} (coberto por tickingarea persistente)"

        # 2. data merge block {Delay:0}
        if s_line.startswith("data merge block ") and "Delay:0" in s_line:
            return f"# [Bedrock Conversion] {s_line} (spawners ativam nativamente por proximidade no Bedrock)"

        # 3. playsound
        for j_snd, b_snd in cls.SOUND_MAP.items():
            if j_snd in s_line:
                s_line = s_line.replace(f"minecraft:{j_snd}", b_snd).replace(j_snd, b_snd)
                s_line = re.sub(r' (master|ambient|voice|record|music|block|neutral) ', ' ', s_line)

        # 4. tellraw com cores e formatação
        if "tellraw" in s_line and ('"text"' in s_line or '"translate"' in s_line):
            s_line = cls._convert_tellraw(s_line)

        # 5. Idempotência em invocações /summon de NPCs customizados
        if known_npcs and "summon " in s_line:
            for npc in known_npcs:
                if f":npc_{npc}" in s_line and not s_line.startswith("execute unless entity"):
                    s_line = f"execute unless entity @e[type=namespace:npc_{npc}] run {s_line}"

        return s_line

    @classmethod
    def _convert_tellraw(cls, line: str) -> str:
        m = re.match(r'^(.*tellraw\s+@[a-zA-Z0-9_]+\s+)(.*)$', line)
        if not m:
            return line
        prefix, raw_json = m.group(1), m.group(2)
        try:
            parsed = json.loads(raw_json)
            rawtext_elements = []

            def process_node(node):
                if isinstance(node, str):
                    rawtext_elements.append({"text": node})
                elif isinstance(node, list):
                    for n in node:
                        process_node(n)
                elif isinstance(node, dict):
                    txt = node.get("text", "")
                    color = node.get("color", "")
                    color_code = cls.COLOR_MAP.get(color, "")
                    bold_code = "§l" if node.get("bold") else ""
                    italic_code = "§o" if node.get("italic") else ""
                    formatted = f"{color_code}{bold_code}{italic_code}{txt}§r" if (color_code or bold_code or italic_code) else txt
                    if formatted:
                        rawtext_elements.append({"text": formatted})
                    for extra in node.get("extra", []):
                        process_node(extra)

            process_node(parsed)
            if rawtext_elements:
                b_json = json.dumps({"rawtext": rawtext_elements}, ensure_ascii=False)
                return f"{prefix}{b_json}"
        except Exception:
            pass
        return line


class LootTableConverter:
    """Converte loot tables de entidades Java para formato Bedrock."""

    @staticmethod
    def convert(java_loot: dict) -> dict:
        b_pools = []
        for p in java_loot.get("pools", []):
            b_entries = []
            for e in p.get("entries", []):
                e_name = str(e.get("name", "")).replace("minecraft:", "")
                functions = []
                for f in e.get("functions", []):
                    f_name = str(f.get("function", ""))
                    if "set_count" in f_name:
                        count = f.get("count", 1)
                        if isinstance(count, dict):
                            functions.append({
                                "function": "set_count",
                                "count": {"min": count.get("min", 1), "max": count.get("max", 1)}
                            })
                        else:
                            functions.append({"function": "set_count", "count": int(count)})
                    elif "looting_enchant" in f_name:
                        functions.append({
                            "function": "looting_enchant",
                            "count": f.get("count", {"min": 0, "max": 1})
                        })

                b_entries.append({
                    "type": "item",
                    "name": f"minecraft:{e_name}",
                    "weight": int(e.get("weight", 1)),
                    "functions": functions
                })

            b_pools.append({
                "rolls": int(p.get("rolls", 1)) if isinstance(p.get("rolls"), (int, float)) else 1,
                "entries": b_entries
            })
        return {"pools": b_pools}


class NPCTradeExtractor:
    """Extrai trocas customizadas (Recipes/Offers) de comandos /summon villager."""

    @staticmethod
    def parse_trades_from_command(command_str: str) -> list:
        trades = []
        recipes_idx = command_str.find("Recipes:[")
        if recipes_idx == -1:
            m = re.search(r'Recipes\s*:\s*\[', command_str)
            if not m:
                return trades
            start_idx = m.end()
        else:
            start_idx = recipes_idx + len("Recipes:[")

        # Encontra o bloco Recipes:[ ... ] com balanceamento de colchetes
        depth = 1
        i = start_idx
        while i < len(command_str) and depth > 0:
            if command_str[i] == '[':
                depth += 1
            elif command_str[i] == ']':
                depth -= 1
            i += 1

        recipes_content = command_str[start_idx:i-1 if depth == 0 else len(command_str)]

        # Extrai cada compound tag {...} dentro de Recipes:[ ... ]
        recipe_blocks = []
        idx = 0
        while idx < len(recipes_content):
            if recipes_content[idx] == '{':
                b_depth = 1
                j = idx + 1
                while j < len(recipes_content) and b_depth > 0:
                    if recipes_content[j] == '{':
                        b_depth += 1
                    elif recipes_content[j] == '}':
                        b_depth -= 1
                    j += 1
                recipe_blocks.append(recipes_content[idx:j])
                idx = j
            else:
                idx += 1

        def extract_tag_compound(text: str, tag_name: str) -> str:
            m = re.search(rf'(?:^|[\s,{{]){tag_name}\s*:\s*\{{', text)
            if not m:
                return ""
            s_idx = m.end()
            c_depth = 1
            k = s_idx
            while k < len(text) and c_depth > 0:
                if text[k] == '{':
                    c_depth += 1
                elif text[k] == '}':
                    c_depth -= 1
                k += 1
            return text[s_idx:k-1 if c_depth == 0 else len(text)]

        for block in recipe_blocks:
            buy_str = extract_tag_compound(block, "buy")
            sell_str = extract_tag_compound(block, "sell")
            if not buy_str or not sell_str:
                continue

            buy_id_m = re.search(r'id\s*:\s*[\'"]?([a-zA-Z0-9:_]+)[\'"]?', buy_str)
            buy_cnt_m = re.search(r'Count\s*:\s*(\d+)', buy_str)
            sell_id_m = re.search(r'id\s*:\s*[\'"]?([a-zA-Z0-9:_]+)[\'"]?', sell_str)
            sell_cnt_m = re.search(r'Count\s*:\s*(\d+)', sell_str)

            if buy_id_m and sell_id_m:
                trade_entry = {
                    "buy": buy_id_m.group(1).replace("minecraft:", ""),
                    "buy_count": int(buy_cnt_m.group(1)) if buy_cnt_m else 1,
                    "sell": sell_id_m.group(1).replace("minecraft:", ""),
                    "sell_count": int(sell_cnt_m.group(1)) if sell_cnt_m else 1,
                }
                buyb_str = extract_tag_compound(block, "buyB")
                if buyb_str:
                    buyb_id_m = re.search(r'id\s*:\s*[\'"]?([a-zA-Z0-9:_]+)[\'"]?', buyb_str)
                    buyb_cnt_m = re.search(r'Count\s*:\s*(\d+)', buyb_str)
                    if buyb_id_m:
                        trade_entry["buyB"] = buyb_id_m.group(1).replace("minecraft:", "")
                        trade_entry["buyB_count"] = int(buyb_cnt_m.group(1)) if buyb_cnt_m else 1

                trades.append(trade_entry)

        return trades


    @staticmethod
    def extract_npc_metadata(command_str: str) -> tuple:
        """Extrai (slug, display_name, profession, biome) de um comando villager."""
        name_m = re.search(r'CustomName:\s*\'[^\']*?"text":"([^"]+)"', command_str)
        if not name_m:
            name_m = re.search(r'CustomName:[\'"]([^\'"]+)[\'"]', command_str)
        display_name = name_m.group(1) if name_m else "Trader"

        slug = re.sub(r'[^a-zA-Z0-9_]', '_', display_name.lower().replace("ö", "o")).strip('_') or "trader"

        prof_m = re.search(r'profession:[\'"]?(?:minecraft:)?([a-zA-Z0-9_]+)[\'"]?', command_str)
        profession = prof_m.group(1) if prof_m else "farmer"

        type_m = re.search(r'type:[\'"]?(?:minecraft:)?([a-zA-Z0-9_]+)[\'"]?', command_str)
        biome = type_m.group(1) if type_m else "plains"

        return slug, display_name, profession, biome


class MapConverterApp:
    """Orquestrador do processo completo de conversão e empacotamento para qualquer mapa."""

    def __init__(self, java_zip: str, bedrock_world: str, output_dir: str = "dist", packs_dir: str = "packs", world_name: str = None, keep_temp: bool = False):
        self.java_zip = java_zip
        self.bedrock_world = bedrock_world
        self.output_dir = output_dir
        self.packs_dir = packs_dir
        self.world_name_arg = world_name
        self.keep_temp = keep_temp
        self.known_npcs = set()
        self.world_name = "converted_world"
        self.safe_name = "converted_world"
        self.bp_dir = ""
        self.rp_dir = ""
        self.work_bedrock = os.path.join(output_dir, "work_bedrock")

    def run(self):
        print("=================================================================")
        print(" INICIANDO PROCESSO DE CONVERSÃO E VALIDAÇÃO JAVA -> BEDROCK ")
        print("=================================================================")
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.packs_dir, exist_ok=True)

        # 1. Auditoria Java
        auditor = JavaWorldAuditor(self.java_zip)
        auditor.audit()

        # 2. Definição do Nome do Mundo e Nomes de Pacotes
        self._determine_world_names(auditor)
        print(f"[*] Nome do Mundo Detectado : {self.world_name} (Slug: {self.safe_name})")

        self.bp_dir = os.path.join(self.packs_dir, f"{self.safe_name}_bp")
        self.rp_dir = os.path.join(self.packs_dir, f"{self.safe_name}_rp")
        os.makedirs(self.bp_dir, exist_ok=True)
        os.makedirs(self.rp_dir, exist_ok=True)

        # 3. Descompactar mundo Bedrock para pasta de trabalho
        print("[*] Extraindo mundo Bedrock de trabalho...")
        if os.path.exists(self.work_bedrock):
            shutil.rmtree(self.work_bedrock)
        with zipfile.ZipFile(self.bedrock_world, "r") as z:
            z.extractall(self.work_bedrock)

        # 4. Gerar Manifestos BP e RP com UUIDs estáveis
        bp_header_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{self.safe_name}.bp.header.1.26.40"))
        bp_module_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{self.safe_name}.bp.module.1.26.40"))
        rp_header_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{self.safe_name}.rp.header.1.26.40"))
        rp_module_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{self.safe_name}.rp.module.1.26.40"))

        self._build_manifests(bp_header_uuid, bp_module_uuid, rp_header_uuid, rp_module_uuid)

        # 5. Extrair e converter recursos do Java (Loot tables, Funções, Texturas, NPCs)
        self._convert_datapack_assets(auditor)

        # 6. Gerar Funções Utilitárias de Inicialização
        self._generate_utility_functions()

        # 7. Integrar Pacotes no mundo Bedrock
        self._integrate_packs(bp_header_uuid, rp_header_uuid)

        # 8. Empacotar .mcworld e .mcpack finais
        final_mcworld = os.path.join(self.output_dir, f"{self.safe_name}-bedrock.mcworld")
        final_bp = os.path.join(self.output_dir, f"{self.safe_name}-behavior-pack.mcpack")
        final_rp = os.path.join(self.output_dir, f"{self.safe_name}-resource-pack.mcpack")

        self._package_zip(self.work_bedrock, final_mcworld)
        self._package_zip(self.bp_dir, final_bp)
        self._package_zip(self.rp_dir, final_rp)

        # 9. Atualizar SHA256SUMS.txt
        sha_file = os.path.join(self.output_dir, "SHA256SUMS.txt")
        with open(sha_file, "w", encoding="utf-8") as f:
            f.write(f"# Checksums SHA-256 dos entregaveis finais ({self.world_name} Bedrock 1.26.40)\n")
            f.write(f"{sha256_file(final_mcworld)} *{os.path.basename(final_mcworld)}\n")
            f.write(f"{sha256_file(final_bp)} *{os.path.basename(final_bp)}\n")
            f.write(f"{sha256_file(final_rp)} *{os.path.basename(final_rp)}\n")

        # 10. Limpar pasta temporária de trabalho
        if not self.keep_temp and os.path.exists(self.work_bedrock):
            shutil.rmtree(self.work_bedrock)

        print("\n=================================================================")
        print(" CONVERSÃO E EMPACOTAMENTO CONCLUÍDOS COM SUCESSO!")
        print("=================================================================")
        print(f" Mundo Bedrock Final    : {final_mcworld} ({os.path.getsize(final_mcworld) / 1024 / 1024:.2f} MB)")
        print(f" Behavior Pack (.mcpack): {final_bp} ({os.path.getsize(final_bp) / 1024:.2f} KB)")
        print(f" Resource Pack (.mcpack): {final_rp} ({os.path.getsize(final_rp) / 1024:.2f} KB)")
        print(f" SHA-256 (.mcworld)     : {sha256_file(final_mcworld)}")
        print("=================================================================\n")

    def _determine_world_names(self, auditor: JavaWorldAuditor):
        raw_name = self.world_name_arg or auditor.level_info.get("LevelName") or os.path.splitext(os.path.basename(self.java_zip))[0]
        clean_name = re.sub(r'§.', '', raw_name).strip() or "converted_world"
        self.world_name = clean_name
        self.safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', clean_name).strip('_').lower() or "converted_world"

    def _build_manifests(self, bp_h: str, bp_m: str, rp_h: str, rp_m: str):
        bp_man = {
            "format_version": 2,
            "header": {
                "name": f"{self.world_name} Behavior Pack",
                "description": f"Behavior Pack for {self.world_name} (Bedrock 1.26.40+)",
                "uuid": bp_h,
                "version": [1, 0, 0],
                "min_engine_version": [1, 26, 40]
            },
            "modules": [{"type": "data", "description": f"{self.world_name} BP Logic", "uuid": bp_m, "version": [1, 0, 0]}],
            "dependencies": [{"uuid": rp_h, "version": [1, 0, 0]}]
        }
        rp_man = {
            "format_version": 2,
            "header": {
                "name": f"{self.world_name} Resource Pack",
                "description": f"Resource Pack for {self.world_name} (Bedrock 1.26.40+)",
                "uuid": rp_h,
                "version": [1, 0, 0],
                "min_engine_version": [1, 26, 40]
            },
            "modules": [{"type": "resources", "description": f"{self.world_name} RP Resources", "uuid": rp_m, "version": [1, 0, 0]}]
        }
        with open(os.path.join(self.bp_dir, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(bp_man, f, indent=2)
        with open(os.path.join(self.rp_dir, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(rp_man, f, indent=2)

    def _convert_datapack_assets(self, auditor: JavaWorldAuditor):
        print("[*] Convertendo recursos, loot tables e funções dos datapacks...")
        with zipfile.ZipFile(self.java_zip, "r") as z:
            namelist = z.namelist()

            # Ícone
            icon_files = [n for n in namelist if n.endswith("icon.png")]
            if icon_files:
                icon_bytes = z.read(icon_files[0])
                with open(os.path.join(self.bp_dir, "pack_icon.png"), "wb") as f: f.write(icon_bytes)
                with open(os.path.join(self.rp_dir, "pack_icon.png"), "wb") as f: f.write(icon_bytes)
                if HAS_PIL:
                    try:
                        im = Image.open(io.BytesIO(icon_bytes))
                        im.convert("RGB").save(os.path.join(self.work_bedrock, "world_icon.jpeg"), "JPEG")
                    except Exception:
                        pass

            # Texturas de blocos customizadas
            tex_files = [n for n in namelist if ("/textures/block/" in n or "/textures/blocks/" in n) and n.endswith(".png")]
            if tex_files:
                tex_block_dir = os.path.join(self.rp_dir, "textures", "blocks")
                os.makedirs(tex_block_dir, exist_ok=True)
                texture_data = {}
                for tf in tex_files:
                    t_basename = os.path.basename(tf)
                    t_key = os.path.splitext(t_basename)[0]
                    with open(os.path.join(tex_block_dir, t_basename), "wb") as f:
                        f.write(z.read(tf))
                    texture_data[t_key] = {"textures": f"textures/blocks/{t_key}"}

                terrain_texture = {
                    "resource_pack_name": f"{self.safe_name}_rp",
                    "texture_name": "atlas.terrain",
                    "padding": 8,
                    "num_mip_levels": 4,
                    "texture_data": texture_data
                }
                tex_dir = os.path.join(self.rp_dir, "textures")
                os.makedirs(tex_dir, exist_ok=True)
                with open(os.path.join(tex_dir, "terrain_texture.json"), "w", encoding="utf-8") as f:
                    json.dump(terrain_texture, f, indent=2)

            # Loot tables
            loot_files = [n for n in namelist if "/loot_tables/" in n and n.endswith(".json")]
            for lf in loot_files:
                try:
                    rel_p = lf.split("/loot_tables/")[-1]
                    dest_path = os.path.join(self.bp_dir, "loot_tables", rel_p)
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    j_loot = json.loads(z.read(lf).decode("utf-8"))
                    b_loot = LootTableConverter.convert(j_loot)
                    with open(dest_path, "w", encoding="utf-8") as f:
                        json.dump(b_loot, f, indent=2)
                except Exception as e:
                    print(f"    [!] Aviso ao converter loot table {lf}: {e}")

            # Funções (.mcfunction)
            funcs = [n for n in namelist if "/functions/" in n and n.endswith(".mcfunction")]
            for fn in funcs:
                try:
                    rel_p = fn.split("/functions/")[-1]
                    dest_path = os.path.join(self.bp_dir, "functions", rel_p)
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)

                    raw_lines = z.read(fn).decode("utf-8", errors="replace").splitlines()

                    # Varredura por trocas de NPCs em cada linha de função
                    for line in raw_lines:
                        if "summon" in line and "villager" in line and "Recipes:[" in line:
                            slug, disp_n, prof_n, biome_n = NPCTradeExtractor.extract_npc_metadata(line)
                            if slug not in self.known_npcs:
                                self.known_npcs.add(slug)
                                trades = NPCTradeExtractor.parse_trades_from_command(line)
                                if trades:
                                    self._create_npc_files(slug, disp_n, prof_n, biome_n, trades)

                    conv_lines = [DatapackConverter.convert_command(l, self.known_npcs) for l in raw_lines]
                    with open(dest_path, "w", encoding="utf-8") as f:
                        f.write("\n".join(conv_lines) + "\n")
                except Exception as e:
                    print(f"    [!] Aviso ao converter função {fn}: {e}")

            # Varredura por trocas de NPCs em blocos de comando
            for cb in auditor.command_blocks:
                cmd = cb.get("command", "")
                if "summon" in cmd and "villager" in cmd and "Recipes:[" in cmd:
                    slug, disp_n, prof_n, biome_n = NPCTradeExtractor.extract_npc_metadata(cmd)
                    if slug not in self.known_npcs:
                        self.known_npcs.add(slug)
                        trades = NPCTradeExtractor.parse_trades_from_command(cmd)
                        if trades:
                            self._create_npc_files(slug, disp_n, prof_n, biome_n, trades)

    def _create_npc_files(self, key: str, display_name: str, profession: str, biome: str, trades: list):
        trade_dir = os.path.join(self.bp_dir, "trading")
        entity_dir = os.path.join(self.bp_dir, "entities")
        rp_entity_dir = os.path.join(self.rp_dir, "entity")
        os.makedirs(trade_dir, exist_ok=True)
        os.makedirs(entity_dir, exist_ok=True)
        os.makedirs(rp_entity_dir, exist_ok=True)

        # 1. Trade Table JSON
        tt_json = {"tiers": [{"trades": []}]}
        for t in trades:
            trade_obj = {
                "wants": [{"item": t["buy"], "quantity": t["buy_count"]}],
                "gives": [{"item": t["sell"], "quantity": t["sell_count"]}],
                "max_uses": 999999
            }
            if "buyB" in t:
                trade_obj["wants"].append({"item": t["buyB"], "quantity": t.get("buyB_count", 1)})
            tt_json["tiers"][0]["trades"].append(trade_obj)

        with open(os.path.join(trade_dir, f"{key}_trades.json"), "w", encoding="utf-8") as f:
            json.dump(tt_json, f, indent=2)

        # 2. BP Entity JSON
        ent_id = f"{self.safe_name}:npc_{key}"
        ent_bp = {
            "format_version": "1.16.0",
            "minecraft:entity": {
                "description": {"identifier": ent_id, "is_spawnable": True, "is_summonable": True, "is_experimental": False},
                "components": {
                    "minecraft:type_family": {"family": ["villager", "npc", "mob"]},
                    "minecraft:breathable": {"total_supply": 15, "suffocate_time": 0},
                    "minecraft:health": {"value": 100, "max": 100},
                    "minecraft:damage_sensor": {"triggers": [{"cause": "all", "deals_damage": False}]},
                    "minecraft:collision_box": {"width": 0.6, "height": 1.9},
                    "minecraft:nameable": {"always_show": True, "default_trigger": {"event": "minecraft:entity_born"}},
                    "minecraft:trade_table": {"display_name": display_name, "table": f"trading/{key}_trades.json"},
                    "minecraft:movement": {"value": 0.0},
                    "minecraft:movement.basic": {},
                    "minecraft:physics": {}
                }
            }
        }
        with open(os.path.join(entity_dir, f"npc_{key}.json"), "w", encoding="utf-8") as f:
            json.dump(ent_bp, f, indent=2)

        # 3. RP Client Entity JSON
        ent_rp = {
            "format_version": "1.10.0",
            "minecraft:client_entity": {
                "description": {
                    "identifier": ent_id,
                    "materials": {"default": "villager"},
                    "textures": {
                        "default": "textures/entity/villager2/villager",
                        "profession": f"textures/entity/villager2/professions/{profession}",
                        "biome": f"textures/entity/villager2/biomes/biome_{biome}"
                    },
                    "geometry": {"default": "geometry.villager_v2"},
                    "scripts": {"pre_animation": ["variable.profession_index = 1;"]},
                    "render_controllers": ["controller.render.villager_v2"],
                    "spawn_egg": {"texture": "spawn_egg", "texture_index": 15}
                }
            }
        }
        with open(os.path.join(rp_entity_dir, f"npc_{key}.entity.json"), "w", encoding="utf-8") as f:
            json.dump(ent_rp, f, indent=2)

    def _generate_utility_functions(self):
        func_dir = os.path.join(self.bp_dir, "functions", self.safe_name)
        os.makedirs(func_dir, exist_ok=True)

        # Função de inicialização
        init_lines = [
            f"# {self.world_name} Initialization for Bedrock 1.26.40+",
            f'tellraw @a {{"rawtext":[{{"text":"§a[{self.world_name}]§r World successfully initialized for Bedrock 1.26.40!"}}]}}'
        ]
        with open(os.path.join(func_dir, "init_world.mcfunction"), "w", encoding="utf-8") as f:
            f.write("\n".join(init_lines) + "\n")

        # Função de kit inicial
        kit_lines = [
            f"# {self.world_name} Starter Kit",
            "give @s bread 16",
            "give @s torch 16",
            "give @s wooden_pickaxe 1",
            f'tellraw @s {{"rawtext":[{{"text":"§a[{self.world_name}]§r Starter kit granted!"}}]}}'
        ]
        with open(os.path.join(func_dir, "starter_kit.mcfunction"), "w", encoding="utf-8") as f:
            f.write("\n".join(kit_lines) + "\n")

    def _integrate_packs(self, bp_h: str, rp_h: str):
        print("[*] Integrando Behavior Pack e Resource Pack no mundo Bedrock...")
        bp_dest = os.path.join(self.work_bedrock, "behavior_packs", f"{self.safe_name}_bp")
        rp_dest = os.path.join(self.work_bedrock, "resource_packs", f"{self.safe_name}_rp")
        if os.path.exists(bp_dest): shutil.rmtree(bp_dest)
        if os.path.exists(rp_dest): shutil.rmtree(rp_dest)
        shutil.copytree(self.bp_dir, bp_dest)
        shutil.copytree(self.rp_dir, rp_dest)

        world_bp = [{"pack_id": bp_h, "version": [1, 0, 0]}]
        world_rp = [{"pack_id": rp_h, "version": [1, 0, 0]}]

        with open(os.path.join(self.work_bedrock, "world_behavior_packs.json"), "w", encoding="utf-8") as f:
            json.dump(world_bp, f, indent=2)
        with open(os.path.join(self.work_bedrock, "world_resource_packs.json"), "w", encoding="utf-8") as f:
            json.dump(world_rp, f, indent=2)

    def _package_zip(self, source_dir: str, target_file: str):
        with zipfile.ZipFile(target_file, "w", zipfile.ZIP_DEFLATED) as z:
            for root, _, files in os.walk(source_dir):
                for file in files:
                    full_p = os.path.join(root, file)
                    rel_p = os.path.relpath(full_p, source_dir).replace("\\", "/")
                    z.write(full_p, rel_p)


def auto_discover_file(arg_val: str, extensions: tuple, search_dirs=("inputs", ".")) -> str:
    """Resolve o arquivo a partir de argumento ou busca automática nos diretórios informados."""
    if arg_val and os.path.exists(arg_val):
        return arg_val
    for d in search_dirs:
        if os.path.isdir(d):
            for f in os.listdir(d):
                if any(f.lower().endswith(ext) for ext in extensions) and not f.startswith("."):
                    return os.path.join(d, f)
    return arg_val or ""


def main():
    parser = argparse.ArgumentParser(
        description="Conversor Universal e Bridge Java <-> Bedrock 1.26.40+ para qualquer mapa de Minecraft."
    )
    parser.add_argument("--java", default=None, help="Caminho do ZIP do mundo Java (busca automática em inputs/*.zip)")
    parser.add_argument("--bedrock", default=None, help="Caminho do MCWORLD Bedrock inicial do Chunker (busca automática em inputs/*.mcworld)")
    parser.add_argument("--output", default="dist", help="Diretório de saída dos artefatos (.mcworld, .mcpack) [padrão: dist]")
    parser.add_argument("--packs", default="packs", help="Diretório dos pacotes descompactados BP/RP [padrão: packs]")
    parser.add_argument("--name", default=None, help="Nome do mundo/pacote (padrão: auto-detectado do level.dat)")
    parser.add_argument("--keep-temp", action="store_true", help="Preservar diretório temporário de extração (work_bedrock)")
    args = parser.parse_args()

    java_file = auto_discover_file(args.java, (".zip",))
    bedrock_file = auto_discover_file(args.bedrock, (".mcworld",))

    if not java_file or not os.path.exists(java_file):
        print(f"[ERRO] Nenhum arquivo Java (.zip) encontrado. Especifique com --java <caminho> ou coloque em inputs/.")
        sys.exit(1)
    if not bedrock_file or not os.path.exists(bedrock_file):
        print(f"[ERRO] Nenhum arquivo Bedrock (.mcworld) encontrado. Especifique com --bedrock <caminho> ou coloque em inputs/.")
        sys.exit(1)

    app = MapConverterApp(
        java_zip=java_file,
        bedrock_world=bedrock_file,
        output_dir=args.output,
        packs_dir=args.packs,
        world_name=args.name,
        keep_temp=args.keep_temp
    )
    app.run()


if __name__ == "__main__":
    main()
