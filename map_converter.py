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
from typing import Optional, List, Tuple, Callable, Dict, Set
from converter.behavior_pack.bp_generator import BehaviorPackGenerator

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


try:
    import crc32c
    def calc_crc32c(data: bytes) -> int:
        return crc32c.crc32c(data)
except ImportError:
    def calc_crc32c(data: bytes) -> int:
        crc = 0xFFFFFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                crc = (crc >> 1) ^ (0x82F63B78 if (crc & 1) else 0)
        return crc ^ 0xFFFFFFFF


def mask_crc(c: int) -> int:
    """Aplica a máscara CRC padrão do LevelDB."""
    return (((c >> 15) | (c << 17)) + 0xa282ead8) & 0xffffffff


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
    """Traduz comandos Java para sintaxe moderna Bedrock 1.20+."""

    COLOR_MAP = {
        "black": "§0", "dark_blue": "§1", "dark_green": "§2", "dark_aqua": "§3",
        "dark_red": "§4", "dark_purple": "§5", "gold": "§6", "gray": "§7",
        "dark_gray": "§8", "blue": "§9", "green": "§a", "aqua": "§b",
        "red": "§c", "light_purple": "§d", "yellow": "§e", "white": "§f",
        "bold": "§l", "italic": "§o", "underlined": "§n", "reset": "§r"
    }

    HEX_COLOR_MAP = {
        "#FFAA00": "§6", "#BB7700": "§6", "#FF5500": "§c", "#AA0000": "§4",
        "#EEEEEE": "§f", "#654321": "§8"
    }

    SOUND_MAP = {
        "entity.player.levelup": "random.levelup",
        "entity.experience_orb.pickup": "random.orb",
        "entity.villager.trade": "mob.villager.yes",
        "entity.villager.no": "mob.villager.no",
        "block.anvil.use": "random.anvil_use",
        "entity.wither.spawn": "mob.wither.spawn",
        "entity.wither.death": "mob.wither.death",
        "entity.ender_dragon.growl": "mob.enderdragon.growl",
        "block.end_portal.spawn": "portal.travel",
        "entity.evoker.prepare_summon": "mob.evoker.prepare_summon",
        "entity.skeleton_horse.death": "mob.skeleton_horse.death",
        "entity.elder_guardian.curse": "mob.elderguardian.curse"
    }

    @classmethod
    def convert_command(cls, line: str, known_npcs: set = None, world_safe_name: str = "custom") -> str:
        s = line.strip()
        if not s or s.startswith("#"):
            return line

        # 1. Remover barra inicial caso exista (normal em command blocks)
        if s.startswith('/'):
            s = s[1:].strip()

        # Suporte recursivo a execute ... run <subcommand>
        if s.startswith("execute ") and " run " in s:
            exec_prefix, run_cmd = s.split(" run ", 1)
            exec_prefix = re.sub(r'distance=\.\.([0-9.]+)', r'r=\1', exec_prefix)
            exec_prefix = re.sub(r'distance=([0-9.]+)\.\.([0-9.]+)', r'rm=\1,r=\2', exec_prefix)
            exec_prefix = re.sub(r'distance=([0-9.]+)', r'r=\1', exec_prefix)
            exec_prefix = exec_prefix.replace("in minecraft:overworld", "in overworld").replace("in minecraft:the_nether", "in nether").replace("in minecraft:the_end", "in the_end")
            exec_prefix = re.sub(r'\bfunction ([a-zA-Z0-9_]+):([a-zA-Z0-9_/-]+)', r'function \1/\2', exec_prefix)
            trans_inner = cls.convert_command(run_cmd, known_npcs, world_safe_name)
            return f"{exec_prefix} run {trans_inner}"

        # 2. forceload -> tickingarea funcional
        if s.startswith("forceload add ") or s.startswith("forceload remove "):
            parts = s.split()
            if len(parts) in (4, 6) and parts[1] == "add":
                x1, z1 = int(parts[2]), int(parts[3])
                x2, z2 = (int(parts[4]), int(parts[5])) if len(parts) == 6 else (x1, z1)
                block_x1, block_z1 = x1 * 16, z1 * 16
                block_x2, block_z2 = x2 * 16 + 15, z2 * 16 + 15
                area_name = f"java_forceload_{x1}_{z1}_{x2}_{z2}".replace("-", "m")
                return f"tickingarea add {block_x1} 0 {block_z1} {block_x2} 319 {block_z2} {area_name}"
            if len(parts) in (4, 6) and parts[1] == "remove":
                x1, z1 = int(parts[2]), int(parts[3])
                x2, z2 = (int(parts[4]), int(parts[5])) if len(parts) == 6 else (x1, z1)
                area_name = f"java_forceload_{x1}_{z1}_{x2}_{z2}".replace("-", "m")
                return f"tickingarea remove {area_name}"
            return f"# [Bedrock Conversion] unsupported forceload syntax: {s}"

        # 3. data merge block {Delay:0}
        if s.startswith("data merge block ") and "Delay:0" in s:
            match = re.match(r"data merge block (-?\d+) (-?\d+) (-?\d+) .*", s)
            if match:
                x, y, z = match.groups()
                return f"setblock {x} {y} {z} mob_spawner"
            return f"# [Bedrock Conversion] unsupported data merge syntax: {s}"

        # 4. Seletores de distância Java: distance=..X -> r=X, distance=X..Y -> rm=X,r=Y
        s = re.sub(r'distance=\.\.([0-9.]+)', r'r=\1', s)
        s = re.sub(r'distance=([0-9.]+)\.\.([0-9.]+)', r'rm=\1,r=\2', s)
        s = re.sub(r'distance=([0-9.]+)', r'r=\1', s)

        # 5. Sintaxe de dimensões e execute: in minecraft:overworld -> in overworld
        s = s.replace("in minecraft:overworld", "in overworld")
        s = s.replace("in minecraft:the_nether", "in nether")
        s = s.replace("in minecraft:the_end", "in the_end")

        # 6. tp sem alvo dentro de execute: run tp <x> <y> <z> -> run tp @s <x> <y> <z>
        s = re.sub(r'\brun tp (-?[0-9~^.]+) (-?[0-9~^.]+) (-?[0-9~^.]+)', r'run tp @s \1 \2 \3', s)

        # 7. Chamadas de função: function custom:name -> function custom/name
        s = re.sub(r'\bfunction ([a-zA-Z0-9_]+):([a-zA-Z0-9_/-]+)', r'function \1/\2', s)

        # 8. Identificadores de blocos comuns sem namespace
        s = re.sub(r'\bminecraft:(redstone_block|smooth_stone|air|stone|dirt|sand|glass|bedrock)\b', r'\1', s)

        # 9. playsound
        if "playsound" in s:
            s = cls._convert_playsound(s)

        # 10. effect give
        if "effect give" in s or s.startswith("effect "):
            s = cls._convert_effect(s)

        # 11. tellraw com cores e formatação
        if "tellraw" in s and ('"text"' in s or '"translate"' in s or '["' in s):
            s = cls._convert_tellraw(s)

        # 12. title
        if "title " in s and ("{" in s or "[" in s):
            s = cls._convert_title(s)

        # 13. particle
        if "particle " in s:
            s = cls._convert_particle(s)

        # 14. give written_book
        if "give " in s and "written_book{" in s:
            s = re.sub(r'give (@[apser]|[\w]+) written_book.*?( \d+)?$', r'give \1 written_book\2', s)

        # 15. summon conversion
        if "summon " in s:
            s = cls._convert_summon(s, world_safe_name, known_npcs)

        # 16. gamerules
        if s.startswith("gamerule "):
            s = s.replace("doDaylightCycle", "dodaylightcycle")
            s = s.replace("doMobSpawning", "domobspawning")
            s = s.replace("randomTickSpeed", "randomtickspeed")

        return s

    @classmethod
    def _convert_playsound(cls, line: str) -> str:
        for j_snd, b_snd in cls.SOUND_MAP.items():
            line = line.replace(f"minecraft:{j_snd}", b_snd).replace(j_snd, b_snd)
        line = re.sub(r' (master|ambient|voice|record|music|block|neutral|hostile|weather|player) ', ' ', line)
        return line

    @classmethod
    def _convert_effect(cls, line: str) -> str:
        if "minecraft:glowing" in line or " glowing " in line:
            return f"# [Bedrock: glowing effect not supported] {line}"
        effects = [
            "blindness", "speed", "slowness", "haste", "strength", "regeneration",
            "resistance", "fire_resistance", "water_breathing", "invisibility",
            "night_vision", "weakness", "poison", "wither", "absorption",
            "saturation", "levitation", "slow_falling"
        ]
        for eff in effects:
            line = line.replace(f"minecraft:{eff}", eff)
        return line

    @classmethod
    def _convert_particle(cls, line: str) -> str:
        m = re.match(r'^(.*?\bparticle\s+)([a-zA-Z0-9:_.]+)\s+([~^0-9.-]+)\s+([~^0-9.-]+)\s+([~^0-9.-]+).*$', line)
        if m:
            prefix, name, x, y, z = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)
            if "large_smoke" in name:
                name = "minecraft:large_smoke"
            elif "campfire_signal_smoke" in name:
                name = "minecraft:campfire_smoke_particle"
            return f"{prefix}{name} {x} {y} {z}"
        return line

    @classmethod
    def _convert_tellraw(cls, line: str) -> str:
        m = re.match(r'^(.*?\btellraw\s+@[a-zA-Z0-9_]+\s+)(.*)$', line)
        if not m:
            return line
        prefix, raw_json = m.group(1), m.group(2)
        try:
            parsed = json.loads(raw_json)
            rawtext_elements = []

            def process_node(node):
                if isinstance(node, str):
                    if node:
                        rawtext_elements.append({"text": node})
                elif isinstance(node, list):
                    for n in node:
                        process_node(n)
                elif isinstance(node, dict):
                    if "score" in node:
                        sc = dict(node["score"])
                        rawtext_elements.append({"score": sc})
                    else:
                        txt = node.get("text", "")
                        color = node.get("color", "")
                        color_code = cls.COLOR_MAP.get(color) or cls.HEX_COLOR_MAP.get(color, "")
                        bold_code = "§l" if node.get("bold") else ""
                        italic_code = "§o" if node.get("italic") else ""
                        under_code = "§n" if node.get("underlined") else ""
                        formatted = f"{color_code}{bold_code}{italic_code}{under_code}{txt}§r" if (color_code or bold_code or italic_code or under_code) else txt
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

    @classmethod
    def _convert_title(cls, line: str) -> str:
        m = re.match(r'^(.*?\btitle\s+@[a-zA-Z0-9_]+\s+(?:title|subtitle|actionbar)\s+)(.*)$', line)
        if not m:
            return line
        prefix, raw_json = m.group(1), m.group(2)
        try:
            parsed = json.loads(raw_json)
            rawtext_elements = []

            def process_node(node):
                if isinstance(node, str):
                    if node:
                        rawtext_elements.append({"text": node})
                elif isinstance(node, list):
                    for n in node:
                        process_node(n)
                elif isinstance(node, dict):
                    if "score" in node:
                        sc = dict(node["score"])
                        rawtext_elements.append({"score": sc})
                    else:
                        txt = node.get("text", "")
                        color = node.get("color", "")
                        color_code = cls.COLOR_MAP.get(color) or cls.HEX_COLOR_MAP.get(color, "")
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

    @classmethod
    def _convert_summon(cls, line: str, world_safe_name: str = "custom", known_npcs: set = None) -> str:
        # 1. Idempotência em invocações /summon de NPCs customizados já mapeados
        if known_npcs:
            for npc in known_npcs:
                if f":npc_{npc}" in line and not line.startswith("execute unless entity"):
                    entity_type = f"{world_safe_name}:npc_{npc}"
                    line = f"execute unless entity @e[type={entity_type}] run {line}"
                    return line

        m = re.search(r'^(.*?\bsummon\s+)([a-zA-Z0-9:_]+)\s+([~^0-9.-]+)\s+([~^0-9.-]+)\s+([~^0-9.-]+)(\s*\{.*\}|\s*)$', line)
        if not m:
            return line
        prefix, ent, x, y, z, nbt = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5), m.group(6)
        clean_ent = ent.replace("minecraft:", "")

        custom_name = None
        if nbt:
            name_m = re.search(r'CustomName:\s*\'[^\']*?"text":"([^"]+)"', nbt)
            if not name_m:
                name_m = re.search(r'CustomName:[\'"]([^\'"]+)[\'"]', nbt)
            if name_m:
                custom_name = name_m.group(1)

        # Se for um aldeão com nome customizado
        if clean_ent == "villager" and custom_name:
            slug = re.sub(r'[^a-zA-Z0-9_]', '_', custom_name.lower().replace("ö", "o")).strip('_')
            target_ns = world_safe_name or "namespace"
            npc_type = f"{target_ns}:npc_{slug}"
            return f"execute unless entity @e[type={npc_type}] run {prefix}{npc_type} {x} {y} {z}"

        # Se for mob customizado conhecido (Prometheus, Reaper, Ascended Pillager, etc.)
        if custom_name and clean_ent in ("wither_skeleton", "spider", "pillager", "vex"):
            mob_slug = re.sub(r'[^a-zA-Z0-9_]', '_', custom_name.lower()).strip('_')
            if mob_slug in ("prometheus", "reaper", "ascended_pillager"):
                target_ns = world_safe_name or "namespace"
                custom_mob_type = f"{target_ns}:{mob_slug}"
                return f"{prefix}{custom_mob_type} {x} {y} {z}"

        # Invocação vanilla sem tags NBT
        return f"{prefix}{clean_ent} {x} {y} {z}"



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
                                "count": {"min": int(float(count.get("min", 1))), "max": int(float(count.get("max", 1)))}
                            })
                        else:
                            functions.append({"function": "set_count", "count": int(float(count))})
                    elif "looting_enchant" in f_name:
                        c_dict = f.get("count", {"min": 0, "max": 1})
                        if isinstance(c_dict, dict):
                            c_dict = {"min": int(float(c_dict.get("min", 0))), "max": int(float(c_dict.get("max", 1)))}
                        functions.append({
                            "function": "looting_enchant",
                            "count": c_dict
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


class BedrockLevelDBManager:
    """Manipula e atualiza blocos de comando diretamente no banco LevelDB do Bedrock."""

    @staticmethod
    def read_varint(buf: bytes, pos: int) -> tuple:
        res, shift = 0, 0
        while True:
            b = buf[pos]
            pos += 1
            res |= (b & 0x7f) << shift
            shift += 7
            if not (b & 0x80):
                break
        return res, pos

    @staticmethod
    def write_varint(val: int) -> bytes:
        res = bytearray()
        while val >= 0x80:
            res.append((val & 0x7f) | 0x80)
            val >>= 7
        res.append(val)
        return bytes(res)

    @classmethod
    def parse_handle(cls, buf: bytes, pos: int) -> tuple:
        o, pos = cls.read_varint(buf, pos)
        s, pos = cls.read_varint(buf, pos)
        return o, s, pos

    @classmethod
    def parse_block_entries(cls, block_data: bytes) -> list:
        num_restarts = struct.unpack('<I', block_data[-4:])[0]
        restarts_offset = len(block_data) - 4 - num_restarts * 4
        pos = 0
        entries = []
        last_key = b''
        while pos < restarts_offset:
            shared, pos = cls.read_varint(block_data, pos)
            non_shared, pos = cls.read_varint(block_data, pos)
            val_len, pos = cls.read_varint(block_data, pos)
            key_delta = block_data[pos:pos+non_shared]
            pos += non_shared
            full_key = last_key[:shared] + key_delta
            last_key = full_key
            val = block_data[pos:pos+val_len]
            pos += val_len
            entries.append((full_key, val))
        return entries

    @classmethod
    def build_block(cls, entries: list, restart_interval: int = 16) -> bytes:
        data = bytearray()
        restarts = []
        last_key = b''
        for i, (k, v) in enumerate(entries):
            if i % restart_interval == 0:
                shared = 0
                restarts.append(len(data))
            else:
                shared = 0
                while shared < len(last_key) and shared < len(k) and last_key[shared] == k[shared]:
                    shared += 1
            non_shared = len(k) - shared
            key_delta = k[shared:]
            data.extend(cls.write_varint(shared))
            data.extend(cls.write_varint(non_shared))
            data.extend(cls.write_varint(len(v)))
            data.extend(key_delta)
            data.extend(v)
            last_key = k
        for r in restarts:
            data.extend(struct.pack('<I', r))
        data.extend(struct.pack('<I', len(restarts)))
        return bytes(data)

    @staticmethod
    def raw_compress(data: bytes) -> bytes:
        co = zlib.compressobj(level=6, method=zlib.DEFLATED, wbits=-15)
        return co.compress(data) + co.flush()

    @classmethod
    def read_ldb_all_entries(cls, raw: bytes) -> list:
        footer = raw[-48:]
        meta_off, meta_size, pos = cls.parse_handle(footer, 0)
        idx_off, idx_size, pos = cls.parse_handle(footer, pos)
        idx_data = raw[idx_off:idx_off + idx_size]
        comp = raw[idx_off + idx_size]
        if comp in (2, 4):
            idx_data = zlib.decompress(idx_data, -15)

        idx_entries = cls.parse_block_entries(idx_data)
        all_data_blocks = []
        for k, handle in idx_entries:
            b_off, b_size, _ = cls.parse_handle(handle, 0)
            b_raw = raw[b_off:b_off + b_size]
            b_comp = raw[b_off + b_size]
            if b_comp in (2, 4):
                b_raw = zlib.decompress(b_raw, -15)
            all_data_blocks.append(cls.parse_block_entries(b_raw))
        return all_data_blocks

    @classmethod
    def build_ldb(cls, all_data_blocks: list) -> bytes:
        out = bytearray()
        idx_entries = []
        for entries in all_data_blocks:
            if not entries:
                continue
            uncomp = cls.build_block(entries)
            comp = cls.raw_compress(uncomp)
            b_off = len(out)
            b_size = len(comp)
            out.extend(comp)
            out.append(4)  # Mojang raw deflate
            crc = mask_crc(calc_crc32c(comp + b'\x04'))
            out.extend(struct.pack('<I', crc))

            last_key = entries[-1][0]
            handle = cls.write_varint(b_off) + cls.write_varint(b_size)
            idx_entries.append((last_key, bytes(handle)))

        meta_block = cls.build_block([])
        meta_off = len(out)
        meta_size = len(meta_block)
        out.extend(meta_block)
        out.append(0)
        crc_meta = mask_crc(calc_crc32c(meta_block + b'\x00'))
        out.extend(struct.pack('<I', crc_meta))

        idx_uncomp = cls.build_block(idx_entries)
        idx_comp = cls.raw_compress(idx_uncomp)
        idx_off = len(out)
        idx_size = len(idx_comp)
        out.extend(idx_comp)
        out.append(4)
        crc_idx = mask_crc(calc_crc32c(idx_comp + b'\x04'))
        out.extend(struct.pack('<I', crc_idx))

        # Footer 48 bytes
        footer = bytearray()
        footer.extend(cls.write_varint(meta_off))
        footer.extend(cls.write_varint(meta_size))
        footer.extend(cls.write_varint(idx_off))
        footer.extend(cls.write_varint(idx_size))
        footer.extend(b'\x00' * (40 - len(footer)))
        footer.extend(b'\x57\xfb\x80\x8b\x24\x75\x47\xdb')
        out.extend(footer)
        return bytes(out)

    @classmethod
    def update_command_blocks(cls, db_dir: str, convert_func, safe_name: Optional[str] = None) -> int:
        """Percorre todos os arquivos .ldb do banco LevelDB e atualiza blocos de comando."""
        if not os.path.exists(db_dir):
            return 0

        ldb_files = [os.path.join(db_dir, f) for f in os.listdir(db_dir) if f.endswith(".ldb")]
        total_modified = 0

        for ldb_path in ldb_files:
            try:
                with open(ldb_path, "rb") as f:
                    raw = f.read()

                data_blocks = cls.read_ldb_all_entries(raw)
                file_modified = False

                new_data_blocks = []
                for block_entries in data_blocks:
                    new_entries = []
                    for k, v in block_entries:
                        if b"CommandBlock" in v:
                            stream = io.BytesIO(v)
                            out_stream = io.BytesIO()
                            entry_modified = False

                            while stream.tell() < len(v):
                                try:
                                    tag = nbtlib.File.from_fileobj(stream, byteorder="little")
                                    if str(tag.get("id", "")) == "CommandBlock":
                                        cmd = str(tag.get("Command", ""))
                                        coord = (int(tag.get("x", 0)), int(tag.get("y", 0)), int(tag.get("z", 0)))
                                        if safe_name and coord == (276, 1, -2191):
                                            new_cmd = f"function {safe_name}/morning_gate"
                                        elif safe_name and coord == (279, 1, -2191):
                                            new_cmd = f"function {safe_name}/generates_npc"
                                        elif safe_name and coord == (280, 1, -2192):
                                            new_cmd = f"function {safe_name}/day_display"
                                        elif safe_name and coord == (279, 1, -2192):
                                            new_cmd = f"function {safe_name}/day_title"
                                        elif safe_name and coord == (271, 1, -2201):
                                            new_cmd = f"function {safe_name}/cycle_night"
                                        elif safe_name and coord == (306, 2, -2102):
                                            new_cmd = "scoreboard players set DAY_COUNTER dayCounter 1"
                                        elif safe_name and coord in ((377, 6, -2117), (273, 1, -2200)):
                                            new_cmd = "scoreboard players set DAY_COUNTER dayCounter 1"
                                        else:
                                            new_cmd = convert_func(cmd)
                                        if new_cmd != cmd:
                                            tag["Command"] = nbtlib.String(new_cmd)
                                            entry_modified = True
                                            total_modified += 1
                                    tag.write(out_stream, byteorder="little")
                                except Exception:
                                    remaining = stream.read()
                                    out_stream.write(remaining)
                                    break

                            if entry_modified:
                                file_modified = True
                                new_entries.append((k, out_stream.getvalue()))
                            else:
                                new_entries.append((k, v))
                        else:
                            new_entries.append((k, v))
                    new_data_blocks.append(new_entries)

                if file_modified:
                    rebuilt_raw = cls.build_ldb(new_data_blocks)
                    with open(ldb_path, "wb") as f:
                        f.write(rebuilt_raw)
            except Exception as e:
                print(f"    [!] Aviso ao processar {os.path.basename(ldb_path)}: {e}")

        return total_modified

    @classmethod
    def inject_ticking_areas(cls, db_dir: str) -> int:
        """Injeta ticking areas permanentes estrategicas diretamente no banco LevelDB Bedrock."""
        if not os.path.exists(db_dir):
            return 0

        areas = [
            {
                "uuid": "00000000-0000-0000-0000-000000000001",
                "name": "maze_glade_center",
                "min_x": 160,
                "max_x": 287,
                "min_z": -2208,
                "max_z": -2081,
            },
            {
                "uuid": "00000000-0000-0000-0000-000000000002",
                "name": "maze_templates_clock",
                "min_x": 272,
                "max_x": 319,
                "min_z": -2208,
                "max_z": -2049,
            },
            {
                "uuid": "00000000-0000-0000-0000-000000000003",
                "name": "maze_station",
                "min_x": 208,
                "max_x": 239,
                "min_z": -2224,
                "max_z": -2208,
            },
        ]

        try:
            import leveldb
            db = leveldb.LevelDB(db_dir)
            injected = 0
            for a in areas:
                key = f"tickingarea_{a['uuid']}".encode("ascii")
                tag = nbtlib.Compound({
                    "Dimension": nbtlib.Int(0),
                    "Name": nbtlib.String(a["name"]),
                    "IsCircle": nbtlib.Byte(0),
                    "MinX": nbtlib.Int(a["min_x"]),
                    "MaxX": nbtlib.Int(a["max_x"]),
                    "MinZ": nbtlib.Int(a["min_z"]),
                    "MaxZ": nbtlib.Int(a["max_z"]),
                    "Preload": nbtlib.Byte(1),
                })
                buf = io.BytesIO()
                nbtlib.File(tag).write(buf, byteorder="little")
                db.put(key, buf.getvalue())
                injected += 1
            db.close()
            return injected
        except Exception:
            return 0


class MapConverterApp:

    """Orquestrador do processo completo de conversão e empacotamento para qualquer mapa."""

    def __init__(self, java_zip: str, bedrock_world: str, output_dir: str = "output", packs_dir: str = "packs", world_name: str = None, keep_temp: bool = False):
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
        # Rebuild packs from a clean directory. Otherwise files removed or
        # relocated by a converter update (such as the old root tick.json)
        # remain in the .mcpack and can shadow the corrected structure.
        if os.path.exists(self.bp_dir):
            shutil.rmtree(self.bp_dir)
        if os.path.exists(self.rp_dir):
            shutil.rmtree(self.rp_dir)
        os.makedirs(self.bp_dir, exist_ok=True)
        os.makedirs(self.rp_dir, exist_ok=True)

        # 3. Descompactar mundo Bedrock para pasta de trabalho
        print("[*] Extraindo mundo Bedrock de trabalho...")
        if os.path.exists(self.work_bedrock):
            shutil.rmtree(self.work_bedrock)
        with zipfile.ZipFile(self.bedrock_world, "r") as z:
            z.extractall(self.work_bedrock)

        # Chunker worlds can retain commands disabled even when the source
        # Java world relies on command blocks and functions.
        self._enable_commands_in_world()

        # 4. Gerar Manifestos BP e RP com UUIDs estáveis
        bp_header_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{self.safe_name}.bp.header.1.20.0"))
        bp_module_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{self.safe_name}.bp.module.1.20.0"))
        rp_header_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{self.safe_name}.rp.header.1.20.0"))
        rp_module_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{self.safe_name}.rp.module.1.20.0"))

        self._build_manifests(bp_header_uuid, bp_module_uuid, rp_header_uuid, rp_module_uuid)

        # 5. Extrair e converter recursos do Java (Loot tables, Funções, Texturas, NPCs)
        self._convert_datapack_assets(auditor)

        # 6. Atualizar e converter blocos de comando no banco LevelDB Bedrock
        print("[*] Atualizando e convertendo blocos de comando no banco LevelDB Bedrock...")
        db_path = os.path.join(self.work_bedrock, "db")
        conv_cbs = BedrockLevelDBManager.update_command_blocks(
            db_path,
            lambda cmd: DatapackConverter.convert_command(cmd, self.known_npcs, self.safe_name),
            safe_name=self.safe_name
        )
        print(f"    [OK] Total de blocos de comando convertidos no mundo: {conv_cbs}")

        # Injeção de ticking areas estratégicas permanentes no LevelDB
        injected_ta = BedrockLevelDBManager.inject_ticking_areas(db_path)
        if injected_ta > 0:
            print(f"    [OK] Ticking areas estratégicas injetadas diretamente no LevelDB: {injected_ta}")

        # Sincronização de inventário do jogador e auditoria de contêineres/baús
        try:
            from converter.world.inventory_manager import PlayerInventoryManager
            injected_items = PlayerInventoryManager.sync_player_inventory(self.java_zip, db_path)
            total_cont, cont_with_items = PlayerInventoryManager.audit_leveldb_containers(db_path)
            if injected_items > 0:
                print(f"    [OK] Inventário do jogador: {injected_items} itens sincronizados para ~local_player")
            if total_cont > 0:
                print(f"    [OK] Contêineres e baús preservados: {total_cont} total ({cont_with_items} com itens mantidos)")
        except Exception:
            pass

        # 7. Gerar Funções Utilitárias de Inicialização
        self._generate_utility_functions()

        # 8. Integrar Pacotes no mundo Bedrock
        self._integrate_packs(bp_header_uuid, rp_header_uuid)

        # 9. Empacotar .mcworld, .mcaddon e .mcpack finais
        final_mcworld = os.path.join(self.output_dir, f"{self.safe_name}-bedrock.mcworld")
        final_bp = os.path.join(self.output_dir, f"{self.safe_name}-behavior-pack.mcpack")
        final_rp = os.path.join(self.output_dir, f"{self.safe_name}-resource-pack.mcpack")
        final_addon = os.path.join(self.output_dir, f"{self.safe_name}.mcaddon")

        self._package_zip(self.work_bedrock, final_mcworld)
        self._package_zip(self.bp_dir, final_bp)
        self._package_zip(self.rp_dir, final_rp)
        self._package_mcaddon(self.bp_dir, self.rp_dir, final_addon)

        # 10. Atualizar SHA256SUMS.txt
        sha_file = os.path.join(self.output_dir, "SHA256SUMS.txt")
        with open(sha_file, "w", encoding="utf-8") as f:
            f.write(f"# Checksums SHA-256 dos entregaveis finais ({self.world_name} Bedrock 1.20+)\n")
            f.write(f"{sha256_file(final_mcworld)} *{os.path.basename(final_mcworld)}\n")
            f.write(f"{sha256_file(final_addon)} *{os.path.basename(final_addon)}\n")
            f.write(f"{sha256_file(final_bp)} *{os.path.basename(final_bp)}\n")
            f.write(f"{sha256_file(final_rp)} *{os.path.basename(final_rp)}\n")

        # 11. Limpar pasta temporária de trabalho
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
                "description": f"Behavior Pack for {self.world_name} (Bedrock 1.20+)",
                "uuid": bp_h,
                "version": [1, 0, 0],
                "min_engine_version": [1, 20, 0]
            },
            "modules": [{"type": "data", "description": f"{self.world_name} BP Logic", "uuid": bp_m, "version": [1, 0, 0]}],
            "dependencies": [{"uuid": rp_h, "version": [1, 0, 0]}]
        }
        rp_man = {
            "format_version": 2,
            "header": {
                "name": f"{self.world_name} Resource Pack",
                "description": f"Resource Pack for {self.world_name} (Bedrock 1.20+)",
                "uuid": rp_h,
                "version": [1, 0, 0],
                "min_engine_version": [1, 20, 0]
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

                # Tratamento para variações de textura de blocos vanilla (ex: bedrock)
                # Bedrock's terrain atlas does not support Java's weighted
                # blockstate-variation object. Use one valid atlas alias and
                # the canonical vanilla texture path instead. The supplied
                # map's brick face is bedrock_3; names containing "brick"
                # take precedence for future maps.
                texture_keys = {os.path.splitext(os.path.basename(p))[0] for p in tex_files}
                brick_key = next((k for k in sorted(texture_keys) if "bedrock" in k and "brick" in k), None)
                bedrock_texture_key = brick_key or ("bedrock" if "bedrock" in texture_keys else None)
                if not bedrock_texture_key:
                    bedrock_texture_key = "bedrock_3" if "bedrock_3" in texture_keys else None
                if not bedrock_texture_key:
                    numbered = sorted(k for k in texture_keys if re.fullmatch(r"bedrock_\d+", k))
                    bedrock_texture_key = numbered[0] if numbered else None

                if bedrock_texture_key:
                    source_texture = os.path.join(tex_block_dir, f"{bedrock_texture_key}.png")
                    canonical_texture = os.path.join(tex_block_dir, "bedrock.png")
                    if os.path.abspath(source_texture) != os.path.abspath(canonical_texture):
                        shutil.copyfile(source_texture, canonical_texture)
                    texture_data["bedrock"] = {"textures": "textures/blocks/bedrock"}

                    blocks_def = {
                        "format_version": "1.19.30",
                        "minecraft:bedrock": {
                            "sound": "stone",
                            "textures": "bedrock"
                        }
                    }
                    with open(os.path.join(self.rp_dir, "blocks.json"), "w", encoding="utf-8") as f:
                        json.dump(blocks_def, f, indent=2)
                    print(f"    [OK] Textura de tijolos aplicada ao bedrock: {bedrock_texture_key}.png")

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

            # Sons e sound_definitions.json
            sound_files = [n for n in namelist if "/sounds/" in n and n.endswith(".ogg")]
            if sound_files:
                sound_dir = os.path.join(self.rp_dir, "sounds")
                os.makedirs(sound_dir, exist_ok=True)
                for sf in sound_files:
                    rel_s = sf.split("/sounds/")[-1]
                    s_dest = os.path.join(sound_dir, rel_s)
                    os.makedirs(os.path.dirname(s_dest), exist_ok=True)
                    with open(s_dest, "wb") as f:
                        f.write(z.read(sf))

                sound_defs = {
                    "format_version": "1.14.0",
                    "sound_definitions": {
                        "entity.illusioner.mirror_move": {
                            "category": "neutral",
                            "sounds": ["sounds/mob/illusion_illager/mirror_move1", "sounds/mob/illusion_illager/mirror_move2"]
                        },
                        "minecraft:entity.illusioner.mirror_move": {
                            "category": "neutral",
                            "sounds": ["sounds/mob/illusion_illager/mirror_move1", "sounds/mob/illusion_illager/mirror_move2"]
                        },
                        "mob.illusion_illager.mirror_move": {
                            "category": "neutral",
                            "sounds": ["sounds/mob/illusion_illager/mirror_move1", "sounds/mob/illusion_illager/mirror_move2"]
                        },
                        "entity.illusioner.prepare_mirror": {
                            "category": "neutral",
                            "sounds": ["sounds/mob/illusion_illager/prepare_mirror"]
                        },
                        "minecraft:entity.illusioner.prepare_mirror": {
                            "category": "neutral",
                            "sounds": ["sounds/mob/illusion_illager/prepare_mirror"]
                        },
                        "mob.illusion_illager.prepare_mirror": {
                            "category": "neutral",
                            "sounds": ["sounds/mob/illusion_illager/prepare_mirror"]
                        },
                        "entity.illusioner.prepare_blind": {
                            "category": "neutral",
                            "sounds": ["sounds/mob/illusion_illager/prepare_blind"]
                        },
                        "minecraft:entity.illusioner.prepare_blind": {
                            "category": "neutral",
                            "sounds": ["sounds/mob/illusion_illager/prepare_blind"]
                        },
                        "mob.illusion_illager.prepare_blind": {
                            "category": "neutral",
                            "sounds": ["sounds/mob/illusion_illager/prepare_blind"]
                        },
                        "entity.skeleton_horse.death": {
                            "category": "neutral",
                            "sounds": ["sounds/mob/horse/zombie/death"]
                        },
                        "mob.horse.skeleton.death": {
                            "category": "neutral",
                            "sounds": ["sounds/mob/horse/zombie/death"]
                        },
                        "entity.ghast.scream": {
                            "category": "hostile",
                            "sounds": ["sounds/mob/ghast/scream1", "sounds/mob/ghast/scream2", "sounds/mob/ghast/scream3", "sounds/mob/ghast/scream4", "sounds/mob/ghast/scream5"]
                        },
                        "mob.ghast.scream": {
                            "category": "hostile",
                            "sounds": ["sounds/mob/ghast/scream1", "sounds/mob/ghast/scream2", "sounds/mob/ghast/scream3", "sounds/mob/ghast/scream4", "sounds/mob/ghast/scream5"]
                        },
                        "entity.wither_skeleton.death": {
                            "category": "hostile",
                            "sounds": ["sounds/mob/wither_skeleton/death1", "sounds/mob/wither_skeleton/death2"]
                        },
                        "mob.wither_skeleton.death": {
                            "category": "hostile",
                            "sounds": ["sounds/mob/wither_skeleton/death1", "sounds/mob/wither_skeleton/death2"]
                        },
                        "block.end_portal.spawn": {
                            "category": "block",
                            "sounds": ["sounds/block/end_portal/endportal"]
                        },
                        "block.end_portal_frame.fill": {
                            "category": "block",
                            "sounds": ["sounds/block/end_portal/eyeplace1", "sounds/block/end_portal/eyeplace2", "sounds/block/end_portal/eyeplace3"]
                        }
                    }
                }
                with open(os.path.join(sound_dir, "sound_definitions.json"), "w", encoding="utf-8") as sf:
                    json.dump(sound_defs, sf, indent=2)
                with open(os.path.join(sound_dir, "sounds.json"), "w", encoding="utf-8") as sf:
                    json.dump(sound_defs, sf, indent=2)

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

                    conv_lines = [DatapackConverter.convert_command(l, self.known_npcs, self.safe_name) for l in raw_lines]
                    if "a_tp_spawn" in fn:
                        conv_lines.insert(0, f"execute if score #world world_init matches 0 run function {self.safe_name}/init_world")
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

            # Gera a definição nativa de minecraft:villager_v2 com component groups e eventos dos NPCs
            BehaviorPackGenerator.generate_villager_v2(self.bp_dir, self.safe_name)

    def _create_npc_files(self, key: str, display_name: str, profession: str, biome: str, trades: list):
        trade_dir = os.path.join(self.bp_dir, "trading")
        entity_dir = os.path.join(self.bp_dir, "entities")
        rp_entity_dir = os.path.join(self.rp_dir, "entity")
        os.makedirs(trade_dir, exist_ok=True)
        os.makedirs(entity_dir, exist_ok=True)
        os.makedirs(rp_entity_dir, exist_ok=True)

        # 1. Trade Table JSON
        tt_json = {
            "tiers": [
                {
                    "total_exp_required": 0,
                    "groups": [
                        {
                            "num_to_select": len(trades),
                            "trades": []
                        }
                    ],
                    "trades": []
                }
            ]
        }
        for t in trades:
            buy_item = f"minecraft:{t['buy']}" if not t['buy'].startswith("minecraft:") else t['buy']
            sell_item = f"minecraft:{t['sell']}" if not t['sell'].startswith("minecraft:") else t['sell']
            trade_obj = {
                "wants": [{"item": buy_item, "quantity": t["buy_count"]}],
                "gives": [{"item": sell_item, "quantity": t["sell_count"]}],
                "max_uses": 999999
            }
            if "buyB" in t:
                buyb_item = f"minecraft:{t['buyB']}" if not t['buyB'].startswith("minecraft:") else t['buyB']
                trade_obj["wants"].append({"item": buyb_item, "quantity": t.get("buyB_count", 1)})
            tt_json["tiers"][0]["trades"].append(trade_obj)
            tt_json["tiers"][0]["groups"][0]["trades"].append(trade_obj)

        with open(os.path.join(trade_dir, f"{key}_trades.json"), "w", encoding="utf-8") as f:
            json.dump(tt_json, f, indent=2)

        # 2. BP Entity JSON
        ent_id = f"{self.safe_name}:npc_{key}"
        ent_bp = {
            "format_version": "1.16.0",
            "minecraft:entity": {
                "description": {"identifier": ent_id, "runtime_identifier": "minecraft:villager_v2", "is_spawnable": True, "is_summonable": True, "is_experimental": False},
                "components": {
                    "minecraft:type_family": {"family": ["villager", "npc", "mob"]},
                    "minecraft:breathable": {"total_supply": 15, "suffocate_time": 0},
                    "minecraft:health": {"value": 100, "max": 100},
                    "minecraft:damage_sensor": {"triggers": [{"cause": "all", "deals_damage": False}]},
                    "minecraft:collision_box": {"width": 0.6, "height": 1.9},
                    "minecraft:nameable": {"always_show": True, "default_trigger": {"event": "minecraft:entity_born"}},
                    "minecraft:trade_table": {
                        "display_name": display_name,
                        "table": f"trading/{key}_trades.json"
                    },
                    "minecraft:economy_trade_table": {
                        "display_name": display_name,
                        "table": f"trading/{key}_trades.json",
                        "convert_trades_economy": False
                    },
                    "minecraft:interact": {
                        "interactions": [{
                            "on_interact": {"filters": {"test": "is_family", "subject": "other", "value": "player"}},
                            "open_trading": True
                        }]
                    },
                    "minecraft:movement": {"value": 0.0},
                    "minecraft:movement.basic": {},
                    "minecraft:physics": {}
                }
            }
        }
        with open(os.path.join(entity_dir, f"npc_{key}.json"), "w", encoding="utf-8") as f:
            json.dump(ent_bp, f, indent=2)

        # 3. RP Client Entity JSON
        prof_tex = "stonemason" if profession == "mason" else profession
        ent_rp = {
            "format_version": "1.10.0",
            "minecraft:client_entity": {
                "description": {
                    "identifier": ent_id,
                    "materials": {
                        "default": "villager_v2",
                        "masked": "villager_v2_masked"
                    },
                    "textures": {
                        "default": "textures/entity/villager2/villager",
                        "base": "textures/entity/villager2/villager",
                        "profession": f"textures/entity/villager2/professions/{prof_tex}",
                        "biome": f"textures/entity/villager2/biomes/biome_{biome}"
                    },
                    "geometry": {"default": "geometry.villager_v2"},
                    "scripts": {
                        "pre_animation": ["variable.profession_index = 1;"]
                    },
                    "animations": {
                        "general": "animation.villager.general",
                        "look_at_target": "animation.common.look_at_target",
                        "move": "animation.villager.move",
                        "raise_arms": "animation.villager.raise_arms"
                    },
                    "animation_controllers": [
                        {"general": "controller.animation.villager_v2.general"},
                        {"move": "controller.animation.villager_v2.move"},
                        {"raise_arms": "controller.animation.villager_v2.raise_arms"}
                    ],
                    "render_controllers": [
                        "controller.render.npc_villager_base",
                        "controller.render.npc_villager_masked"
                    ],
                    "spawn_egg": {"texture": "spawn_egg", "texture_index": 15}
                }
            }
        }
        with open(os.path.join(rp_entity_dir, f"npc_{key}.entity.json"), "w", encoding="utf-8") as f:
            json.dump(ent_rp, f, indent=2)

        # 4. RP Render Controller
        rc_dir = os.path.join(self.rp_dir, "render_controllers")
        os.makedirs(rc_dir, exist_ok=True)
        rc_file = os.path.join(rc_dir, "npc_villager.render_controllers.json")
        rc_data = {
            "format_version": "1.8.0",
            "render_controllers": {
                "controller.render.npc_villager_base": {
                    "geometry": "Geometry.default",
                    "materials": [
                        {"*": "Material.default"}
                    ],
                    "textures": [
                        "Texture.default"
                    ]
                },
                "controller.render.npc_villager_masked": {
                    "geometry": "Geometry.default",
                    "materials": [
                        {"*": "Material.masked"}
                    ],
                    "textures": [
                        "Texture.biome",
                        "Texture.profession"
                    ]
                },
                "controller.render.villager_v2": {
                    "geometry": "Geometry.default",
                    "materials": [
                        {"*": "Material.default"}
                    ],
                    "textures": [
                        "Texture.default"
                    ]
                }
            }
        }
        with open(rc_file, "w", encoding="utf-8") as f:
            json.dump(rc_data, f, indent=2)

    def _generate_utility_functions(self):
        func_dir = os.path.join(self.bp_dir, "functions", self.safe_name)
        os.makedirs(func_dir, exist_ok=True)
        root_func_dir = os.path.join(self.bp_dir, "functions")
        custom_func_dir = os.path.join(self.bp_dir, "functions", "custom")
        os.makedirs(custom_func_dir, exist_ok=True)

        # 1. Ciclo da Manhã (Abertura de portões, áudio, exibição do dia, aldeões e suprimentos)
        morning_lines = [
            f"# {self.world_name} Morning Cycle - Gate opening, day display, NPCs & chests",
            "scoreboard objectives add dayCounter dummy",
            "scoreboard objectives add DAY_COUNTER dummy",
            "scoreboard players add DAY_COUNTER dayCounter 0",
            "execute if score DAY_COUNTER dayCounter matches ..0 run scoreboard players set DAY_COUNTER dayCounter 1",
            "scoreboard players operation @a dayCounter = DAY_COUNTER dayCounter",
            "execute as @a run scoreboard players operation @s dayCounter = DAY_COUNTER dayCounter",
            f'tellraw @a {{"rawtext":[{{"text":"The gates are "}},{{"text":"§e§lopening"}},{{"text":"..."}}]}}',
            "setblock 286 1 -2168 redstone_block",
            "playsound entity.illusioner.prepare_mirror @a 173 64 -2148 0.7 1 0.03",
            "playsound entity.illusioner.prepare_mirror @a 220 64 -2195 0.7 1 0.03",
            "playsound entity.illusioner.prepare_mirror @a 220 64 -2100 0.7 1 0.03",
            "playsound entity.illusioner.prepare_mirror @a 268 64 -2148 0.7 1 0.03",
            "playsound entity.illusioner.prepare_mirror @a 173 64 -2148 10.0 1 0.03",
            "playsound entity.illusioner.prepare_mirror @a 220 64 -2195 10.0 1 0.03",
            "playsound entity.illusioner.prepare_mirror @a 220 64 -2100 10.0 1 0.03",
            "playsound entity.illusioner.prepare_mirror @a 268 64 -2148 10.0 1 0.03",
            "playsound mob.evocation_illager.prepare_summon @a ~ ~ ~ 1.0 1 0.03",
            "playsound mob.ghast.scream @a ~ ~ ~ 10000",
            'titleraw @a title {"rawtext":[{"text":"§7Day "},{"score":{"name":"DAY_COUNTER","objective":"dayCounter"}}]}',
            'tellraw @a {"rawtext":[{"text":"§7Day "},{"score":{"name":"DAY_COUNTER","objective":"dayCounter"}}]}',
            "function custom/generates_npc",
            "function custom/generates_chest",
            "kill @e[type=villager,tag=!Vil]",
            "kill @e[type=villager_v2,tag=!Vil]"
        ]
        morning_content = "\n".join(morning_lines) + "\n"
        for d in (func_dir, root_func_dir, custom_func_dir):
            with open(os.path.join(d, "cycle_morning.mcfunction"), "w", encoding="utf-8") as f:
                f.write(morning_content)

        # 1b. Função de Abertura do Portão e Inicialização do Contador Matinal (acoplada ao bloco em 276 1 -2191)
        morning_gate_lines = [
            f"# {self.world_name} Morning Gate Opening & Day Counter Initialization",
            'scoreboard objectives add dayCounter dummy "Dias"',
            "scoreboard objectives add DAY_COUNTER dummy",
            "scoreboard players add DAY_COUNTER dayCounter 0",
            "execute unless score DAY_COUNTER dayCounter matches 1.. run scoreboard players set DAY_COUNTER dayCounter 1",
            "scoreboard players operation @a dayCounter = DAY_COUNTER dayCounter",
            "execute as @a run scoreboard players operation @s dayCounter = DAY_COUNTER dayCounter",
            f'tellraw @a {{"rawtext":[{{"text":"The gates are "}},{{"text":"§e§lopening"}},{{"text":"..."}}]}}'
        ]
        morning_gate_content = "\n".join(morning_gate_lines) + "\n"
        for d in (func_dir, root_func_dir, custom_func_dir):
            with open(os.path.join(d, "morning_gate.mcfunction"), "w", encoding="utf-8") as f:
                f.write(morning_gate_content)

        # 1c. Função de Invocação de Aldeões / Newcomers na Área de Carga (acoplada ao bloco em 279 1 -2191)
        generates_npc_lines = [
            f"# {self.world_name} Newcomer Villagers Spawning in Loading Area",
            "",
            "# Cleanup any legacy invisible custom entities",
            f"kill @e[type={self.safe_name}:npc_bruce]",
            f"kill @e[type={self.safe_name}:npc_boris]",
            f"kill @e[type={self.safe_name}:npc_joe]",
            f"kill @e[type={self.safe_name}:npc_tobias]",
            f"kill @e[type={self.safe_name}:npc_george]",
            f"kill @e[type={self.safe_name}:npc_erik]",
            f"kill @e[type={self.safe_name}:npc_adam]",
            f"kill @e[type={self.safe_name}:npc_joakim]",
            f"kill @e[type={self.safe_name}:npc_seth]",
            f"kill @e[type={self.safe_name}:npc_jorn]",
            "",
            "# Day 4: Bruce (Farmer)",
            f'execute if score DAY_COUNTER dayCounter matches 4.. unless entity @e[name=Bruce] run tellraw @a {{"rawtext":[{{"text":"A"}},{{"text":"§a§l newcomer"}},{{"text":" has arrived in the"}},{{"text":"§6§l§o loading area"}},{{"text":"!"}}]}}',
            f'execute if score DAY_COUNTER dayCounter matches 4.. unless entity @e[name=Bruce] run summon villager_v2 264 59 -2184 0 0 {self.safe_name}:spawn_bruce "Bruce"',
            'tag @e[name=Bruce] add Vil',
            'tag @e[type=villager,x=264,y=59,z=-2184,r=3] add Vil',
            'tag @e[type=villager_v2,x=264,y=59,z=-2184,r=3] add Vil',
            'tag @e[x=264,y=59,z=-2184,r=3] add Vil',
            "",
            "# Day 9: Boris (Shepherd)",
            f'execute if score DAY_COUNTER dayCounter matches 9.. unless entity @e[name=Boris] run tellraw @a {{"rawtext":[{{"text":"A"}},{{"text":"§a§l newcomer"}},{{"text":" has arrived in the"}},{{"text":"§6§l§o loading area"}},{{"text":"!"}}]}}',
            f'execute if score DAY_COUNTER dayCounter matches 9.. unless entity @e[name=Boris] run summon villager_v2 264 59 -2184 0 0 {self.safe_name}:spawn_boris "Boris"',
            'tag @e[name=Boris] add Vil',
            'tag @e[type=villager,x=264,y=59,z=-2184,r=3] add Vil',
            'tag @e[type=villager_v2,x=264,y=59,z=-2184,r=3] add Vil',
            'tag @e[x=264,y=59,z=-2184,r=3] add Vil',
            "",
            "# Day 13: Joe (Fletcher)",
            f'execute if score DAY_COUNTER dayCounter matches 13.. unless entity @e[name=Joe] run tellraw @a {{"rawtext":[{{"text":"A"}},{{"text":"§a§l newcomer"}},{{"text":" has arrived in the"}},{{"text":"§6§l§o loading area"}},{{"text":"!"}}]}}',
            f'execute if score DAY_COUNTER dayCounter matches 13.. unless entity @e[name=Joe] run summon villager_v2 264 59 -2184 0 0 {self.safe_name}:spawn_joe "Joe"',
            'tag @e[name=Joe] add Vil',
            'tag @e[type=villager,x=264,y=59,z=-2184,r=3] add Vil',
            'tag @e[type=villager_v2,x=264,y=59,z=-2184,r=3] add Vil',
            'tag @e[x=264,y=59,z=-2184,r=3] add Vil',
            "",
            "# Day 17: Tobias (Weaponsmith)",
            f'execute if score DAY_COUNTER dayCounter matches 17.. unless entity @e[name=Tobias] run tellraw @a {{"rawtext":[{{"text":"A"}},{{"text":"§a§l newcomer"}},{{"text":" has arrived in the"}},{{"text":"§6§l§o loading area"}},{{"text":"!"}}]}}',
            f'execute if score DAY_COUNTER dayCounter matches 17.. unless entity @e[name=Tobias] run summon villager_v2 264 59 -2184 0 0 {self.safe_name}:spawn_tobias "Tobias"',
            'tag @e[name=Tobias] add Vil',
            'tag @e[type=villager,x=264,y=59,z=-2184,r=3] add Vil',
            'tag @e[type=villager_v2,x=264,y=59,z=-2184,r=3] add Vil',
            'tag @e[x=264,y=59,z=-2184,r=3] add Vil',
            "",
            "# Day 21: George (Butcher)",
            f'execute if score DAY_COUNTER dayCounter matches 21.. unless entity @e[name=George] run tellraw @a {{"rawtext":[{{"text":"A"}},{{"text":"§a§l newcomer"}},{{"text":" has arrived in the"}},{{"text":"§6§l§o loading area"}},{{"text":"!"}}]}}',
            f'execute if score DAY_COUNTER dayCounter matches 21.. unless entity @e[name=George] run summon villager_v2 264 59 -2184 0 0 {self.safe_name}:spawn_george "George"',
            'tag @e[name=George] add Vil',
            'tag @e[type=villager,x=264,y=59,z=-2184,r=3] add Vil',
            'tag @e[type=villager_v2,x=264,y=59,z=-2184,r=3] add Vil',
            'tag @e[x=264,y=59,z=-2184,r=3] add Vil',
            "",
            "# Day 26: Erik (Cleric)",
            f'execute if score DAY_COUNTER dayCounter matches 26.. unless entity @e[name=Erik] run tellraw @a {{"rawtext":[{{"text":"A"}},{{"text":"§a§l newcomer"}},{{"text":" has arrived in the"}},{{"text":"§6§l§o loading area"}},{{"text":"!"}}]}}',
            f'execute if score DAY_COUNTER dayCounter matches 26.. unless entity @e[name=Erik] run summon villager_v2 264 59 -2184 0 0 {self.safe_name}:spawn_erik "Erik"',
            'tag @e[name=Erik] add Vil',
            'tag @e[type=villager,x=264,y=59,z=-2184,r=3] add Vil',
            'tag @e[type=villager_v2,x=264,y=59,z=-2184,r=3] add Vil',
            'tag @e[x=264,y=59,z=-2184,r=3] add Vil',
            "",
            "# Day 31: Adam (Mason)",
            f'execute if score DAY_COUNTER dayCounter matches 31.. unless entity @e[name=Adam] run tellraw @a {{"rawtext":[{{"text":"A"}},{{"text":"§a§l newcomer"}},{{"text":" has arrived in the"}},{{"text":"§6§l§o loading area"}},{{"text":"!"}}]}}',
            f'execute if score DAY_COUNTER dayCounter matches 31.. unless entity @e[name=Adam] run summon villager_v2 264 59 -2184 0 0 {self.safe_name}:spawn_adam "Adam"',
            'tag @e[name=Adam] add Vil',
            'tag @e[type=villager,x=264,y=59,z=-2184,r=3] add Vil',
            'tag @e[type=villager_v2,x=264,y=59,z=-2184,r=3] add Vil',
            'tag @e[x=264,y=59,z=-2184,r=3] add Vil',
            "",
            "# Day 38: Joakim (Armorer)",
            f'execute if score DAY_COUNTER dayCounter matches 38.. unless entity @e[name=Joakim] run tellraw @a {{"rawtext":[{{"text":"A"}},{{"text":"§a§l newcomer"}},{{"text":" has arrived in the"}},{{"text":"§6§l§o loading area"}},{{"text":"!"}}]}}',
            f'execute if score DAY_COUNTER dayCounter matches 38.. unless entity @e[name=Joakim] run summon villager_v2 264 59 -2184 0 0 {self.safe_name}:spawn_joakim "Joakim"',
            'tag @e[name=Joakim] add Vil',
            'tag @e[type=villager,x=264,y=59,z=-2184,r=3] add Vil',
            'tag @e[type=villager_v2,x=264,y=59,z=-2184,r=3] add Vil',
            'tag @e[x=264,y=59,z=-2184,r=3] add Vil',
            "",
            "# Day 47: Seth (Librarian)",
            f'execute if score DAY_COUNTER dayCounter matches 47.. unless entity @e[name=Seth] run tellraw @a {{"rawtext":[{{"text":"A"}},{{"text":"§a§l newcomer"}},{{"text":" has arrived in the"}},{{"text":"§6§l§o loading area"}},{{"text":"!"}}]}}',
            f'execute if score DAY_COUNTER dayCounter matches 47.. unless entity @e[name=Seth] run summon villager_v2 264 59 -2184 0 0 {self.safe_name}:spawn_seth "Seth"',
            'tag @e[name=Seth] add Vil',
            'tag @e[type=villager,x=264,y=59,z=-2184,r=3] add Vil',
            'tag @e[type=villager_v2,x=264,y=59,z=-2184,r=3] add Vil',
            'tag @e[x=264,y=59,z=-2184,r=3] add Vil',
            "",
            "# Day 55: Jorn (Cartographer) & Redstone Trigger",
            f'execute if score DAY_COUNTER dayCounter matches 55.. unless entity @e[name=Jorn] run tellraw @a {{"rawtext":[{{"text":"A"}},{{"text":"§a§l newcomer"}},{{"text":" has arrived in the"}},{{"text":"§6§l§o loading area"}},{{"text":"!"}}]}}',
            'execute if score DAY_COUNTER dayCounter matches 55.. unless entity @e[name=Jorn] run setblock 279 1 -2177 redstone_block',
            f'execute if score DAY_COUNTER dayCounter matches 55.. unless entity @e[name=Jorn] run summon villager_v2 264 59 -2184 0 0 {self.safe_name}:spawn_jorn "Jorn"',
            'tag @e[name=Jorn] add Vil',
            'tag @e[type=villager,x=264,y=59,z=-2184,r=3] add Vil',
            'tag @e[type=villager_v2,x=264,y=59,z=-2184,r=3] add Vil',
            'tag @e[x=264,y=59,z=-2184,r=3] add Vil'
        ]
        generates_npc_content = "\n".join(generates_npc_lines) + "\n"
        for d in (func_dir, root_func_dir, custom_func_dir):
            with open(os.path.join(d, "generates_npc.mcfunction"), "w", encoding="utf-8") as f:
                f.write(generates_npc_content)

        # 1d. Funções de Exibição de Dia no Chat e Título (acopladas a 280 1 -2192 e 279 1 -2192)
        day_display_lines = [
            f"# {self.world_name} Day Counter Chat Announcement",
            'scoreboard objectives add dayCounter dummy "Dias"',
            "scoreboard objectives add DAY_COUNTER dummy",
            "scoreboard players add DAY_COUNTER dayCounter 0",
            "execute unless score DAY_COUNTER dayCounter matches 1.. run scoreboard players set DAY_COUNTER dayCounter 1",
            "scoreboard players operation @a dayCounter = DAY_COUNTER dayCounter",
            "execute as @a run scoreboard players operation @s dayCounter = DAY_COUNTER dayCounter",
            'tellraw @a {"rawtext":[{"text":"§7Day "},{"score":{"name":"DAY_COUNTER","objective":"dayCounter"}}]}'
        ]
        day_display_content = "\n".join(day_display_lines) + "\n"
        for d in (func_dir, root_func_dir, custom_func_dir):
            with open(os.path.join(d, "day_display.mcfunction"), "w", encoding="utf-8") as f:
                f.write(day_display_content)

        day_title_lines = [
            f"# {self.world_name} Day Counter Title Announcement",
            'scoreboard objectives add dayCounter dummy "Dias"',
            "scoreboard objectives add DAY_COUNTER dummy",
            "scoreboard players add DAY_COUNTER dayCounter 0",
            "execute unless score DAY_COUNTER dayCounter matches 1.. run scoreboard players set DAY_COUNTER dayCounter 1",
            "scoreboard players operation @a dayCounter = DAY_COUNTER dayCounter",
            "execute as @a run scoreboard players operation @s dayCounter = DAY_COUNTER dayCounter",
            'titleraw @a title {"rawtext":[{"text":"§7Day "},{"score":{"name":"DAY_COUNTER","objective":"dayCounter"}}]}'
        ]
        day_title_content = "\n".join(day_title_lines) + "\n"
        for d in (func_dir, root_func_dir, custom_func_dir):
            with open(os.path.join(d, "day_title.mcfunction"), "w", encoding="utf-8") as f:
                f.write(day_title_content)

        # 2. Ciclo da Noite (Fechamento de portões, áudio e avanço do contador de dias)
        night_lines = [
            f"# {self.world_name} Night Cycle - Gate closing & day counter increment",
            'scoreboard objectives add dayCounter dummy "Dias"',
            "scoreboard objectives add DAY_COUNTER dummy",
            "scoreboard players add DAY_COUNTER dayCounter 0",
            "execute unless score DAY_COUNTER dayCounter matches 1.. run scoreboard players set DAY_COUNTER dayCounter 1",
            "scoreboard players add DAY_COUNTER dayCounter 1",
            "scoreboard players operation @a dayCounter = DAY_COUNTER dayCounter",
            "execute as @a run scoreboard players operation @s dayCounter = DAY_COUNTER dayCounter",
            "setblock 287 1 -2168 redstone_block",
            "setblock 164 44 -2210 redstone_block",
            "playsound entity.illusioner.prepare_mirror @a 173 64 -2148 0.7 1 0.03",
            "playsound entity.illusioner.prepare_mirror @a 220 64 -2195 0.7 1 0.03",
            "playsound entity.illusioner.prepare_mirror @a 220 64 -2100 0.7 1 0.03",
            "playsound entity.illusioner.prepare_mirror @a 268 64 -2148 0.7 1 0.03",
            "playsound entity.illusioner.prepare_mirror @a 173 64 -2148 10.0 1 0.03",
            "playsound entity.illusioner.prepare_mirror @a 220 64 -2195 10.0 1 0.03",
            "playsound entity.illusioner.prepare_mirror @a 220 64 -2100 10.0 1 0.03",
            "playsound entity.illusioner.prepare_mirror @a 268 64 -2148 10.0 1 0.03",
            "playsound mob.evocation_illager.prepare_summon @a ~ ~ ~ 1.0 1 0.03",
            "playsound mob.ghast.scream @a ~ ~ ~ 10000"
        ]
        night_content = "\n".join(night_lines) + "\n"
        for d in (func_dir, root_func_dir, custom_func_dir):
            with open(os.path.join(d, "cycle_night.mcfunction"), "w", encoding="utf-8") as f:
                f.write(night_content)

        # 3. Função de inicialização e Ticking Areas permanentes (<100 chunks)
        init_lines = [
            f"# {self.world_name} Initialization for Bedrock 1.21+",
            "gamerule commandblockoutput false",
            "gamerule sendcommandfeedback false",
            "gamerule doimmediaterespawn true",
            "gamerule domobspawning false",
            "gamerule dodaylightcycle true",
            "# Ticking areas permanentes cobrindo centro, portoes, clareira, templates, relogio e estacao de trem (98 chunks)",
            "tickingarea add 170 50 -2205 275 110 -2095 maze_glade_center",
            "tickingarea add 276 0 -2205 310 50 -2060 maze_templates_clock",
            "tickingarea add 208 40 -2218 224 60 -2206 maze_station",
            'scoreboard objectives add dayCounter dummy "Dias"',
            "scoreboard objectives add DAY_COUNTER dummy",
            "scoreboard objectives add day_timer dummy",
            "scoreboard objectives add is_night dummy",
            "scoreboard objectives add cycle_ran dummy",
            "scoreboard objectives add world_init dummy",
            "scoreboard players add DAY_COUNTER dayCounter 0",
            "scoreboard players add #world dayCounter 0",
            "execute unless score DAY_COUNTER dayCounter matches 1.. run scoreboard players set DAY_COUNTER dayCounter 1",
            "scoreboard players set DAY_COUNTER dayCounter 1",
            "scoreboard players add @a dayCounter 0",
            "scoreboard players operation @a dayCounter = DAY_COUNTER dayCounter",
            "execute as @a run scoreboard players operation @s dayCounter = DAY_COUNTER dayCounter",
            "time set 0",
            "scoreboard players set #world is_night 0",
            "scoreboard players set #world cycle_ran 0",
            "scoreboard players set #timer day_timer 0",
            "setblock 286 99 -2168 bedrock",
            "setblock 287 99 -2168 bedrock",
            "setblock 286 100 -2168 daylight_detector",
            "setblock 287 100 -2168 daylight_detector_inverted",
            "setblock 286 1 -2168 redstone_block",
            "scoreboard players set #world world_init 1",
            f'tellraw @a {{"rawtext":[{{"text":"§a[{self.world_name}]§r World successfully initialized for Bedrock 1.21+!"}}]}}'
        ]
        init_content = "\n".join(init_lines) + "\n"
        for d in (func_dir, root_func_dir, custom_func_dir):
            with open(os.path.join(d, "init_world.mcfunction"), "w", encoding="utf-8") as f:
                f.write(init_content)

        # Manipulador de entrada do jogador
        player_join_lines = [
            f"# {self.world_name} Player Join Handler",
            "tag @s add joined",
            'scoreboard objectives add dayCounter dummy "Dias"',
            "scoreboard objectives add DAY_COUNTER dummy",
            "scoreboard objectives add world_init dummy",
            "scoreboard players add #world world_init 0",
            "scoreboard players add DAY_COUNTER dayCounter 0",
            "execute unless score DAY_COUNTER dayCounter matches 1.. run scoreboard players set DAY_COUNTER dayCounter 1",
            "scoreboard players add @s dayCounter 0",
            "scoreboard players operation @s dayCounter = DAY_COUNTER dayCounter",
            f"execute if score #world world_init matches 0 run function {self.safe_name}/init_world",
            f'tellraw @s {{"rawtext":[{{"text":"§a[{self.world_name}]§r Welcome to the Maze! Day counter and world mechanics are active."}}]}}'
        ]
        player_join_content = "\n".join(player_join_lines) + "\n"
        for d in (func_dir, root_func_dir, custom_func_dir):
            with open(os.path.join(d, "player_join.mcfunction"), "w", encoding="utf-8") as f:
                f.write(player_join_content)

        # 4. Tick hook com máquina de estados Daylight Detector + sincronização
        tick_lines = [
            f"# 1. Ticking areas permanentes (98 chunks no total, limite Bedrock 100 chunks)",
            f"scoreboard objectives add areas_added dummy",
            f"scoreboard players add #world areas_added 0",
            f"execute if score #world areas_added matches 0 run tickingarea add 170 50 -2205 275 110 -2095 maze_glade_center",
            f"execute if score #world areas_added matches 0 run tickingarea add 276 0 -2205 310 50 -2060 maze_templates_clock",
            f"execute if score #world areas_added matches 0 run tickingarea add 208 40 -2218 224 60 -2206 maze_station",
            f"scoreboard players set #world areas_added 1",
            f"# Garantia retroativa da estacao de trem para saves existentes",
            f"scoreboard objectives add station_ticked dummy",
            f"scoreboard players add #world station_ticked 0",
            f"execute if score #world station_ticked matches 0 run tickingarea add 208 40 -2218 224 60 -2206 maze_station",
            f"scoreboard players set #world station_ticked 1",
            f"# 2. Inicializacao automatica do mundo e do contador ao entrar o primeiro jogador",
            f"scoreboard objectives add world_init dummy",
            f"scoreboard players add #world world_init 0",
            f"execute unless score #world world_init matches 0.. run scoreboard players set #world world_init 0",
            f"execute if entity @a if score #world world_init matches 0 run function {self.safe_name}/init_world",
            f"execute if entity @a if score #world world_init matches 0 run function init_world",
            f"# 3. Sincronizacao continua do contador de dias e garantia de DAY_COUNTER >= 1",
            'scoreboard objectives add dayCounter dummy "Dias"',
            "scoreboard objectives add DAY_COUNTER dummy",
            "scoreboard players add DAY_COUNTER dayCounter 0",
            "execute unless score DAY_COUNTER dayCounter matches 1.. run scoreboard players set DAY_COUNTER dayCounter 1",
            "scoreboard players add @a dayCounter 0",
            "scoreboard players operation @a dayCounter = DAY_COUNTER dayCounter",
            "execute as @a run scoreboard players operation @s dayCounter = DAY_COUNTER dayCounter",
            f"execute as @a[tag=!joined] run function {self.safe_name}/player_join",
            f"# 4. Manutencao dos detectores de ciclo dia/noite",
            "execute if score #world world_init matches 1 unless block 286 100 -2168 daylight_detector run setblock 286 100 -2168 daylight_detector",
            "execute if score #world world_init matches 1 unless block 287 100 -2168 daylight_detector_inverted run setblock 287 100 -2168 daylight_detector_inverted",
            f"# 5. Detector de noite (pôr do sol / /time set 13000+ / celestial darkness)",
            'execute if score #world is_night matches 0 if block 286 100 -2168 daylight_detector ["redstone_signal"=0] run scoreboard players set #world is_night 1',
            f'execute if score #world is_night matches 1 if score #world cycle_ran matches 0 run function {self.safe_name}/cycle_night',
            'execute if score #world is_night matches 1 if score #world cycle_ran matches 0 run scoreboard players set #world cycle_ran 1',
            f"# 6. Detector de dia (amanhecer / sono / /time set 1000 / celestial light)",
            'execute if score #world is_night matches 1 unless block 286 100 -2168 daylight_detector ["redstone_signal"=0] run scoreboard players set #world is_night 0',
            f'execute if score #world is_night matches 0 if score #world cycle_ran matches 1 run function {self.safe_name}/cycle_morning',
            'execute if score #world is_night matches 0 if score #world cycle_ran matches 1 run scoreboard players set #world cycle_ran 0'
        ]
        tick_content = "\n".join(tick_lines) + "\n"
        for d in (root_func_dir, func_dir, custom_func_dir):
            with open(os.path.join(d, "tick.mcfunction"), "w", encoding="utf-8") as f:
                f.write(tick_content)

        # Garante que tick.json legado na raiz do BP seja removido
        stale_tick = os.path.join(self.bp_dir, "tick.json")
        if os.path.exists(stale_tick):
            os.remove(stale_tick)

        # tick.json configurado na pasta functions/ (e subpastas de funcoes)
        tick_json_data = {"values": ["tick"]}
        for d in (root_func_dir, func_dir, custom_func_dir):
            with open(os.path.join(d, "tick.json"), "w", encoding="utf-8") as f:
                json.dump(tick_json_data, f, indent=2)

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

    def _enable_commands_in_world(self):
        """Enable Bedrock commands while preserving level.dat's header and NBT."""
        level_path = os.path.join(self.work_bedrock, "level.dat")
        if not os.path.exists(level_path):
            return
        try:
            with open(level_path, "rb") as f:
                raw = f.read()
            # Bedrock level.dat has an 8-byte storage-version header before NBT.
            if len(raw) < 8:
                raise ValueError("level.dat is smaller than its Bedrock header")
            tag = nbtlib.File.parse(io.BytesIO(raw[8:]), byteorder="little")
            tag["commandsEnabled"] = nbtlib.Byte(1)
            tag["cheatsEnabled"] = nbtlib.Byte(1)
            payload = io.BytesIO()
            tag.write(payload, byteorder="little")
            with open(level_path, "wb") as f:
                f.write(raw[:8])
                f.write(payload.getvalue())
            print("    [OK] Comandos e command blocks habilitados no level.dat")
        except Exception as e:
            # Synthetic/minimal worlds may have a placeholder level.dat. Do
            # not abort export in that case; a real world still gets updated.
            print(f"    [!] Aviso ao habilitar comandos em level.dat: {e}")

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

    def _package_mcaddon(self, bp_dir: str, rp_dir: str, target_addon: str):
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


def auto_discover_file(arg_val: str, extensions: tuple, search_dirs=("inputs", "expected", ".")) -> str:
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
    parser.add_argument("--output", default="output", help="Diretório de saída dos artefatos (.mcworld, .mcpack, .mcaddon) [padrão: output]")
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
