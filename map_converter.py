#!/usr/bin/env python3
"""
=============================================================================
 Minecraft Map Converter & Bridge Tool: Java <-> Bedrock (1.26.40+)
=============================================================================
 Ferramenta automatizada de auditoria, conversão complementar e integração
 de mapas entre Minecraft Java Edition e Minecraft Bedrock Edition.

 Abrangência Completa:
  1. Preservação integral do terreno convertido (LevelDB).
  2. Auditoria e mapeamento de entidades das regiões MCA e playerdata.
  3. Conversão de Datapacks Java para Behavior Packs Bedrock:
     - Funções (.mcfunction) com sintaxe moderna (execute, tellraw com cores, sounds).
     - Idempotência automática de invocações (prevenção contra duplicação de NPCs).
     - Conversão de Loot Tables de entidades (pools, rolls, looting, counts).
  4. Conversão Integral de NPCs e Comércio Customizado:
     - 10 NPCs progressivos de generates_npc.mcfunction.
     - 5 NPCs de exploração encontrados em blocos de comando (Ylva, Jonne, Heri, Kai, Angus).
     - Geração de Bedrock Trade Tables (trading/*.json).
     - Geração de Entidades Customizadas BP (entities/npc_*.json) e RP (entity/npc_*.entity.json).
     - 3 Mobs Bosses (Prometheus, Reaper, Ascended Pillager).
  5. Funções Auxiliares e de Inicialização (mazerunner/init_world, setup_hall_of_fame, starter_kit).
  6. Extração de Recursos e Texturas das Paredes (bedrock_0..4.png, terrain_texture.json, ícones).
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
            if "level.dat" in namelist:
                try:
                    raw_ld = z.read("level.dat")
                    import gzip
                    f = nbtlib.File.from_fileobj(gzip.GzipFile(fileobj=io.BytesIO(raw_ld)))
                    data = f.get("Data", {})
                    self.level_info = {
                        "LevelName": str(data.get("LevelName", "Mundo Java")),
                        "DataVersion": int(data.get("DataVersion", 0)),
                        "GameType": int(data.get("GameType", 0)),
                        "SpawnX": int(data.get("SpawnX", 0)),
                        "SpawnY": int(data.get("SpawnY", 64)),
                        "SpawnZ": int(data.get("SpawnZ", 0))
                    }
                except Exception as e:
                    print(f"    [!] Aviso ao ler level.dat: {e}")

            # 2. Playerdata
            p_files = [n for n in namelist if n.startswith("playerdata/") and n.endswith(".dat")]
            import gzip
            for pf in p_files:
                try:
                    raw = z.read(pf)
                    p_nbt = nbtlib.File.from_fileobj(gzip.GzipFile(fileobj=io.BytesIO(raw)))
                    uuid_str = os.path.basename(pf).replace(".dat", "")
                    pos = [float(x) for x in p_nbt.get("Pos", [])]
                    inv = p_nbt.get("Inventory", [])
                    ender = p_nbt.get("EnderChestInventory", [])
                    self.playerdata.append({
                        "uuid": uuid_str,
                        "pos": pos,
                        "dimension": str(p_nbt.get("Dimension", "minecraft:overworld")),
                        "gamemode": int(p_nbt.get("playerGameType", 0)),
                        "inventory_count": len(inv),
                        "ender_count": len(ender)
                    })
                except Exception as e:
                    print(f"    [!] Erro ao auditar {pf}: {e}")

            # 3. MCA Chunks (Entidades e Command Blocks)
            mca_files = [n for n in namelist if n.endswith(".mca") and ("region/" in n or "DIM-1" in n)]
            print(f"    -> Analisando {len(mca_files)} arquivos de regiões MCA...")
            for mca_name in mca_files:
                dim = "nether" if "DIM-1" in mca_name else "overworld"
                raw_mca = z.read(mca_name)
                self._parse_mca(raw_mca, mca_name, dim)

        print(f"    [OK] Total de entidades detectadas: {len(self.entities)}")
        print(f"    [OK] Total de blocos de comando detectados: {len(self.command_blocks)}")
        print(f"    [OK] Total de jogadores auditados: {len(self.playerdata)}")

    def _parse_mca(self, mca_bytes: bytes, mca_name: str, dim: str):
        if len(mca_bytes) < 8192:
            return
        for i in range(1024):
            offset_data = mca_bytes[i * 4 : i * 4 + 4]
            offset = int.from_bytes(offset_data[:3], "big")
            sector_count = offset_data[3]
            if offset == 0 or sector_count == 0:
                continue
            byte_offset = offset * 4096
            if byte_offset + 5 > len(mca_bytes):
                continue
            length = int.from_bytes(mca_bytes[byte_offset : byte_offset + 4], "big")
            compression = mca_bytes[byte_offset + 4]
            chunk_data = mca_bytes[byte_offset + 5 : byte_offset + 4 + length]
            if compression == 2:  # zlib
                try:
                    decompressed = zlib.decompress(chunk_data)
                    nbt_obj = nbtlib.File.from_fileobj(io.BytesIO(decompressed))
                    level = nbt_obj.get("Level")
                    if level:
                        for e in level.get("Entities", []):
                            self.entities.append({
                                "id": str(e.get("id", "")),
                                "dim": dim,
                                "pos": [float(x) for x in e.get("Pos", [])],
                                "name": str(e.get("CustomName", "")) if "CustomName" in e else None,
                                "tags": [str(t) for t in e.get("Tags", [])] if "Tags" in e else []
                            })
                        for t in level.get("TileEntities", []):
                            tid = str(t.get("id", ""))
                            if "command_block" in tid:
                                self.command_blocks.append({
                                    "id": tid,
                                    "dim": dim,
                                    "x": int(t.get("x", 0)),
                                    "y": int(t.get("y", 0)),
                                    "z": int(t.get("z", 0)),
                                    "command": str(t.get("Command", ""))
                                })
                except Exception:
                    pass


class DatapackConverter:
    """Converte funções .mcfunction e tellraws do Java para o Bedrock Edition."""

    SOUND_MAP = {
        "minecraft:entity.player.levelup": "random.levelup",
        "minecraft:block.end_portal.spawn": "portal.portal",
        "minecraft:entity.evoker.prepare_summon": "mob.evoker.prepare_summon",
        "minecraft:entity.villager.ambient": "mob.villager.idle"
    }

    @classmethod
    def convert_tellraw(cls, raw_payload: str) -> str:
        try:
            data = json.loads(raw_payload)
            parts = []
            if isinstance(data, list):
                for item in data:
                    txt = item.get("text", "")
                    color = item.get("color", "")
                    bold = item.get("bold", False)
                    italic = item.get("italic", False)
                    code = ""
                    if color == "green": code += "§a"
                    elif color == "gold": code += "§6"
                    elif color == "aqua": code += "§b"
                    elif color == "yellow": code += "§e"
                    elif color == "light_purple": code += "§d"
                    elif color == "dark_green": code += "§2"
                    elif color == "dark_blue": code += "§1"
                    elif color == "white": code += "§f"
                    if bold: code += "§l"
                    if italic: code += "§o"
                    parts.append(code + txt + ("§r" if code else ""))
            elif isinstance(data, dict):
                txt = data.get("text", "")
                parts.append(txt)
            formatted_text = "".join(parts)
            return f'{{"rawtext":[{{"text":"{formatted_text}"}}]}}'
        except Exception:
            clean = raw_payload.replace('"', '\\"')
            return f'{{"rawtext":[{{"text":"{clean}"}}]}}'

    @classmethod
    def convert_command(cls, line: str, known_npcs: set) -> str:
        line = line.strip()
        if not line or line.startswith("#"):
            return line

        if line.startswith("/"):
            line = line[1:]

        # Forceload
        if line.startswith("forceload"):
            return f"# [Bedrock Conversion] {line}"

        # Data merge block
        if line.startswith("data merge block"):
            return f"# [Bedrock Conversion] {line}"

        # Sons
        for j_sound, b_sound in cls.SOUND_MAP.items():
            if j_sound in line:
                line = line.replace(j_sound, b_sound)
        if "playsound minecraft:" in line:
            line = line.replace("minecraft:", "")

        # Invocação de NPC com idempotência
        if "summon minecraft:villager" in line or "summon villager" in line:
            m_name = re.search(r'CustomName:\s*\'[^\']*?"text":"([^"]+)"', line)
            if m_name:
                raw_name = m_name.group(1)
                npc_name = raw_name.lower().replace("ö", "o").replace(" ", "_")
                if "j" in npc_name and "rn" in npc_name:
                    npc_name = "jorn"
                if npc_name in known_npcs or npc_name in ["bruce", "boris", "joe", "tobias", "george", "erik", "adam", "joakim", "seth", "jorn", "ylva", "jonne", "heri", "kai", "angus"]:
                    m_score = re.search(r'(execute\s+if\s+score\s+\S+\s+\S+\s+matches\s+\d+)', line)
                    prefix = m_score.group(1) if m_score else "execute"
                    return f"{prefix} unless entity @e[type=mazerunner:npc_{npc_name}] run summon mazerunner:npc_{npc_name} 264 59 -2184"

        # Tellraw
        m_tellraw = re.search(r'(.*?tellraw\s+@[apser](\[[^\]]*\])?\s+)(.*)', line)
        if m_tellraw:
            prefix = m_tellraw.group(1)
            payload = m_tellraw.group(3)
            converted = cls.convert_tellraw(payload)
            return f"{prefix}{converted}"

        # Execute syntax
        if "positioned as @a run playsound" in line:
            line = line.replace("positioned as @a run playsound", "at @a run playsound")
        if "positioned as @a[" in line:
            line = line.replace("positioned as @a[", "at @a[")
        if "execute in minecraft:the_nether" in line:
            line = line.replace("execute in minecraft:the_nether", "in the_nether")

        # Remoção do namespace minecraft: em blocos comuns
        for blk in ["bedrock", "air", "redstone_block", "smooth_stone"]:
            line = line.replace(f"minecraft:{blk}", blk)

        return line


class LootTableConverter:
    """Converte Loot Tables de entidades de Java para Bedrock."""

    @staticmethod
    def convert(java_loot_json: dict) -> dict:
        bedrock_loot = {"pools": []}
        for pool in java_loot_json.get("pools", []):
            rolls = pool.get("rolls", 1)
            if isinstance(rolls, dict):
                rolls = {"min": rolls.get("min", 1), "max": rolls.get("max", 1)}
            new_pool = {"rolls": rolls, "entries": []}

            for entry in pool.get("entries", []):
                etype = entry.get("type", "item").replace("minecraft:", "")
                name = entry.get("name", "")
                if not name and etype == "item":
                    continue
                new_entry = {"type": etype, "weight": entry.get("weight", 1), "name": name}
                
                if "functions" in entry:
                    funcs = []
                    for f in entry["functions"]:
                        fname = f.get("function", "").replace("minecraft:", "")
                        new_f = {"function": fname}
                        for k, v in f.items():
                            if k == "function": continue
                            if isinstance(v, dict):
                                new_f[k] = {ck: cv for ck, cv in v.items() if ck != "type"}
                            else:
                                new_f[k] = v
                        funcs.append(new_f)
                    new_entry["functions"] = funcs
                new_pool["entries"].append(new_entry)
            bedrock_loot["pools"].append(new_pool)
        return bedrock_loot


class NPCTradeExtractor:
    """Extrai trocas NBT de comandos e gera Trade Tables e Entidades Bedrock."""

    @staticmethod
    def parse_trades_from_command(command_str: str) -> list:
        trades = []
        recipes_idx = command_str.find("Recipes:[")
        if recipes_idx == -1:
            return trades
        snippet = command_str[recipes_idx:]
        recipe_blocks = re.findall(r'buy:\{id:[\'"]?([a-zA-Z0-9:_]+)[\'"]?,Count:(\d+)b\},sell:\{id:[\'"]?([a-zA-Z0-9:_]+)[\'"]?,Count:(\d+)b', snippet)
        for buy_id, buy_cnt, sell_id, sell_cnt in recipe_blocks:
            trades.append({
                "buy": buy_id,
                "buy_count": int(buy_cnt),
                "sell": sell_id,
                "sell_count": int(sell_cnt)
            })
        return trades


class MapConverterApp:
    """Orquestrador do processo completo de conversão e empacotamento."""

    KNOWN_EXPLORATION_NPCS = {
        "ylva": ("Ylva", "armorer", "jungle"),
        "jonne": ("Jonne", "cleric", "jungle"),
        "heri": ("Heri", "weaponsmith", "jungle"),
        "kai": ("Kai", "fletcher", "jungle"),
        "angus": ("Angus", "librarian", "jungle")
    }

    def __init__(self, java_zip: str, bedrock_world: str, output_dir: str = "dist", packs_dir: str = "packs", keep_temp: bool = False):
        self.java_zip = java_zip
        self.bedrock_world = bedrock_world
        self.output_dir = output_dir
        self.packs_dir = packs_dir
        self.keep_temp = keep_temp
        self.bp_dir = os.path.join(packs_dir, "mazerunner_bp")
        self.rp_dir = os.path.join(packs_dir, "mazerunner_rp")
        self.work_bedrock = os.path.join(output_dir, "work_bedrock")
        self.known_npcs = set()

    def run(self):
        print("=================================================================")
        print(" INICIANDO PROCESSO DE CONVERSÃO E VALIDAÇÃO JAVA -> BEDROCK ")
        print("=================================================================")
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.packs_dir, exist_ok=True)
        os.makedirs(self.bp_dir, exist_ok=True)
        os.makedirs(self.rp_dir, exist_ok=True)

        # 1. Auditoria Java
        auditor = JavaWorldAuditor(self.java_zip)
        auditor.audit()

        # 2. Descompactar mundo Bedrock para pasta de trabalho
        print("[*] Extraindo mundo Bedrock de trabalho...")
        if os.path.exists(self.work_bedrock):
            shutil.rmtree(self.work_bedrock)
        with zipfile.ZipFile(self.bedrock_world, "r") as z:
            z.extractall(self.work_bedrock)

        # 3. Gerar Manifestos BP e RP com UUIDs estáveis
        bp_header_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, "mazerunner.bp.header.1.26.40"))
        bp_module_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, "mazerunner.bp.module.1.26.40"))
        rp_header_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, "mazerunner.rp.header.1.26.40"))
        rp_module_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, "mazerunner.rp.module.1.26.40"))

        self._build_manifests(bp_header_uuid, bp_module_uuid, rp_header_uuid, rp_module_uuid)

        # 4. Extrair e converter recursos do Java (Loot tables, Funções, Texturas, NPCs, Bosses)
        self._convert_datapack_assets(auditor)

        # 5. Gerar Bosses e Funções de Inicialização
        self._generate_bosses_and_utility_functions()

        # 6. Integrar Pacotes no mundo Bedrock
        self._integrate_packs(bp_header_uuid, rp_header_uuid)

        # 7. Empacotar .mcworld e .mcpack finais
        final_mcworld = os.path.join(self.output_dir, "mazescapist-bedrock-1.26.40.mcworld")
        final_bp = os.path.join(self.output_dir, "mazerunner-behavior-pack.mcpack")
        final_rp = os.path.join(self.output_dir, "mazerunner-resource-pack.mcpack")

        self._package_zip(self.work_bedrock, final_mcworld)
        self._package_zip(self.bp_dir, final_bp)
        self._package_zip(self.rp_dir, final_rp)

        # Atualizar SHA256SUMS.txt
        sha_file = os.path.join(self.output_dir, "SHA256SUMS.txt")
        with open(sha_file, "w", encoding="utf-8") as f:
            f.write("# Checksums SHA-256 dos entregáveis finais (Mazescapist Bedrock 1.26.40)\n")
            f.write(f"{sha256_file(final_mcworld)} *{os.path.basename(final_mcworld)}\n")
            f.write(f"{sha256_file(final_bp)} *{os.path.basename(final_bp)}\n")
            f.write(f"{sha256_file(final_rp)} *{os.path.basename(final_rp)}\n")

        # Limpar pasta temporária de trabalho a menos que explicitamente solicitado
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

    def _build_manifests(self, bp_h, bp_m, rp_h, rp_m):
        bp_man = {
            "format_version": 2,
            "header": {
                "name": "Mazescapist Behavior Pack",
                "description": "Mazescapist Behavior Pack for Bedrock 1.26.40",
                "uuid": bp_h,
                "version": [1, 0, 0],
                "min_engine_version": [1, 26, 40]
            },
            "modules": [{"type": "data", "description": "Mazescapist BP Logic", "uuid": bp_m, "version": [1, 0, 0]}],
            "dependencies": [{"uuid": rp_h, "version": [1, 0, 0]}]
        }
        rp_man = {
            "format_version": 2,
            "header": {
                "name": "Mazescapist Resource Pack",
                "description": "Mazescapist Resource Pack for Bedrock 1.26.40",
                "uuid": rp_h,
                "version": [1, 0, 0],
                "min_engine_version": [1, 26, 40]
            },
            "modules": [{"type": "resources", "description": "Mazescapist RP Resources", "uuid": rp_m, "version": [1, 0, 0]}]
        }
        with open(os.path.join(self.bp_dir, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(bp_man, f, indent=2)
        with open(os.path.join(self.rp_dir, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(rp_man, f, indent=2)

    def _convert_datapack_assets(self, auditor: JavaWorldAuditor):
        print("[*] Convertendo recursos, loot tables e funções do datapack...")
        with zipfile.ZipFile(self.java_zip, "r") as z:
            namelist = z.namelist()

            # Extração de Ícone
            if "icon.png" in namelist:
                icon_bytes = z.read("icon.png")
                with open(os.path.join(self.bp_dir, "pack_icon.png"), "wb") as f: f.write(icon_bytes)
                with open(os.path.join(self.rp_dir, "pack_icon.png"), "wb") as f: f.write(icon_bytes)
                if HAS_PIL:
                    im = Image.open(io.BytesIO(icon_bytes))
                    im.convert("RGB").save(os.path.join(self.work_bedrock, "world_icon.jpeg"), "JPEG")

            # Extração de Texturas de Rocha-Mãe do Resource Pack Java
            tex_block_dir = os.path.join(self.rp_dir, "textures", "blocks")
            os.makedirs(tex_block_dir, exist_ok=True)
            for i in range(5):
                t_name = f"resources/assets/minecraft/textures/block/bedrock_{i}.png"
                if t_name in namelist:
                    with open(os.path.join(tex_block_dir, f"bedrock_{i}.png"), "wb") as f:
                        f.write(z.read(t_name))
            
            # terrain_texture.json
            terrain_texture = {
                "resource_pack_name": "mazerunner_rp",
                "texture_name": "atlas.terrain",
                "padding": 8,
                "num_mip_levels": 4,
                "texture_data": {
                    f"bedrock_{i}": {"textures": f"textures/blocks/bedrock_{i}"} for i in range(5)
                }
            }
            tex_dir = os.path.join(self.rp_dir, "textures")
            os.makedirs(tex_dir, exist_ok=True)
            with open(os.path.join(tex_dir, "terrain_texture.json"), "w", encoding="utf-8") as f:
                json.dump(terrain_texture, f, indent=2)

            # Loot tables
            loot_files = [n for n in namelist if "loot_tables/entities/" in n and n.endswith(".json")]
            loot_dest = os.path.join(self.bp_dir, "loot_tables", "entities")
            os.makedirs(loot_dest, exist_ok=True)
            for lf in loot_files:
                fname = os.path.basename(lf)
                j_loot = json.loads(z.read(lf).decode("utf-8"))
                b_loot = LootTableConverter.convert(j_loot)
                with open(os.path.join(loot_dest, fname), "w", encoding="utf-8") as f:
                    json.dump(b_loot, f, indent=2)

            # 10 NPCs de generates_npc.mcfunction
            gen_npc_path = "datapacks/MazeRunner/data/custom/functions/generates_npc.mcfunction"
            if gen_npc_path in namelist:
                lines = z.read(gen_npc_path).decode("utf-8", errors="replace").splitlines()
                for line in lines:
                    m_name = re.search(r'CustomName:\s*\'[^\']*?"text":"([^"]+)"', line)
                    if m_name:
                        raw_name = m_name.group(1)
                        npc_name = raw_name.lower().replace("ö", "o").replace(" ", "_")
                        if "j" in npc_name and "rn" in npc_name:
                            npc_name = "jorn"
                        self.known_npcs.add(npc_name)
                        trades = NPCTradeExtractor.parse_trades_from_command(line)
                        if trades:
                            m_prof = re.search(r'profession:"minecraft:([^"]+)"', line)
                            prof = m_prof.group(1) if m_prof else "farmer"
                            self._create_npc_files(npc_name, raw_name, prof, "savanna", trades)

            # 5 NPCs de Exploração em Blocos de Comando
            for cb in auditor.command_blocks:
                cmd = cb.get("command", "")
                if "summon" in cmd and "villager" in cmd:
                    for k_npc, (disp_n, prof_n, biome_n) in self.KNOWN_EXPLORATION_NPCS.items():
                        if disp_n.lower() in cmd.lower() and k_npc not in self.known_npcs:
                            self.known_npcs.add(k_npc)
                            trades = NPCTradeExtractor.parse_trades_from_command(cmd)
                            if trades:
                                self._create_npc_files(k_npc, disp_n, prof_n, biome_n, trades)

            # Funções (.mcfunction)
            funcs = [n for n in namelist if "datapacks/MazeRunner/data/custom/functions/" in n and n.endswith(".mcfunction")]
            func_dest = os.path.join(self.bp_dir, "functions", "custom")
            os.makedirs(func_dest, exist_ok=True)
            for fn in funcs:
                fname = os.path.basename(fn)
                raw_lines = z.read(fn).decode("utf-8", errors="replace").splitlines()
                conv_lines = [DatapackConverter.convert_command(l, self.known_npcs) for l in raw_lines]
                with open(os.path.join(func_dest, fname), "w", encoding="utf-8") as f:
                    f.write("\n".join(conv_lines) + "\n")

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
            tt_json["tiers"][0]["trades"].append({
                "wants": [{"item": t["buy"], "quantity": t["buy_count"]}],
                "gives": [{"item": t["sell"], "quantity": t["sell_count"]}],
                "max_uses": 999999
            })
        with open(os.path.join(trade_dir, f"{key}_trades.json"), "w", encoding="utf-8") as f:
            json.dump(tt_json, f, indent=2)

        # 2. BP Entity JSON
        ent_id = f"mazerunner:npc_{key}"
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

    def _generate_bosses_and_utility_functions(self):
        print("[*] Gerando entidades de Bosses e funções de utilidade...")
        entity_dir = os.path.join(self.bp_dir, "entities")
        rp_entity_dir = os.path.join(self.rp_dir, "entity")
        func_custom_dir = os.path.join(self.bp_dir, "functions", "custom")
        func_maze_dir = os.path.join(self.bp_dir, "functions", "mazerunner")
        os.makedirs(func_maze_dir, exist_ok=True)

        # Boss 1: Reaper (Spider)
        reaper_bp = {
            "format_version": "1.16.0",
            "minecraft:entity": {
                "description": {"identifier": "mazerunner:reaper", "is_spawnable": True, "is_summonable": True, "is_experimental": False},
                "components": {
                    "minecraft:type_family": {"family": ["spider", "monster", "mob"]},
                    "minecraft:health": {"value": 30, "max": 30},
                    "minecraft:movement": {"value": 0.35},
                    "minecraft:attack": {"damage": 6},
                    "minecraft:collision_box": {"width": 0.7, "height": 0.5},
                    "minecraft:behavior.melee_attack": {"priority": 3, "speed_multiplier": 1.3},
                    "minecraft:behavior.nearest_attackable_target": {
                        "priority": 2, "entity_types": [{"filters": {"test": "is_family", "subject": "other", "value": "player"}, "max_dist": 16}]
                    },
                    "minecraft:physics": {}
                }
            }
        }
        with open(os.path.join(entity_dir, "reaper.json"), "w", encoding="utf-8") as f: json.dump(reaper_bp, f, indent=2)
        reaper_rp = {
            "format_version": "1.10.0",
            "minecraft:client_entity": {
                "description": {
                    "identifier": "mazerunner:reaper", "materials": {"default": "spider"},
                    "textures": {"default": "textures/entity/spider/cave_spider"},
                    "geometry": {"default": "geometry.spider"},
                    "render_controllers": ["controller.render.spider"],
                    "spawn_egg": {"texture": "spawn_egg", "texture_index": 11}
                }
            }
        }
        with open(os.path.join(rp_entity_dir, "reaper.entity.json"), "w", encoding="utf-8") as f: json.dump(reaper_rp, f, indent=2)

        # Boss 2: Prometheus (Wither Skeleton)
        prometheus_bp = {
            "format_version": "1.16.0",
            "minecraft:entity": {
                "description": {"identifier": "mazerunner:prometheus", "is_spawnable": True, "is_summonable": True, "is_experimental": False},
                "components": {
                    "minecraft:type_family": {"family": ["skeleton", "monster", "mob", "undead"]},
                    "minecraft:health": {"value": 50, "max": 50},
                    "minecraft:movement": {"value": 0.3},
                    "minecraft:attack": {"damage": 8},
                    "minecraft:collision_box": {"width": 0.7, "height": 2.4},
                    "minecraft:behavior.melee_attack": {"priority": 3, "speed_multiplier": 1.2},
                    "minecraft:behavior.nearest_attackable_target": {
                        "priority": 2, "entity_types": [{"filters": {"test": "is_family", "subject": "other", "value": "player"}, "max_dist": 20}]
                    },
                    "minecraft:physics": {}
                }
            }
        }
        with open(os.path.join(entity_dir, "prometheus.json"), "w", encoding="utf-8") as f: json.dump(prometheus_bp, f, indent=2)
        prometheus_rp = {
            "format_version": "1.10.0",
            "minecraft:client_entity": {
                "description": {
                    "identifier": "mazerunner:prometheus", "materials": {"default": "skeleton"},
                    "textures": {"default": "textures/entity/skeleton/wither_skeleton"},
                    "geometry": {"default": "geometry.wither_skeleton"},
                    "render_controllers": ["controller.render.wither_skeleton"],
                    "spawn_egg": {"texture": "spawn_egg", "texture_index": 28}
                }
            }
        }
        with open(os.path.join(rp_entity_dir, "prometheus.entity.json"), "w", encoding="utf-8") as f: json.dump(prometheus_rp, f, indent=2)

        # Boss 3: Ascended Pillager (Evoker)
        evoker_bp = {
            "format_version": "1.16.0",
            "minecraft:entity": {
                "description": {"identifier": "mazerunner:ascended_pillager", "is_spawnable": True, "is_summonable": True, "is_experimental": False},
                "components": {
                    "minecraft:type_family": {"family": ["illager", "monster", "mob"]},
                    "minecraft:health": {"value": 60, "max": 60},
                    "minecraft:movement": {"value": 0.25},
                    "minecraft:collision_box": {"width": 0.6, "height": 1.9},
                    "minecraft:behavior.nearest_attackable_target": {
                        "priority": 2, "entity_types": [{"filters": {"test": "is_family", "subject": "other", "value": "player"}, "max_dist": 24}]
                    },
                    "minecraft:physics": {}
                }
            }
        }
        with open(os.path.join(entity_dir, "ascended_pillager.json"), "w", encoding="utf-8") as f: json.dump(evoker_bp, f, indent=2)
        evoker_rp = {
            "format_version": "1.10.0",
            "minecraft:client_entity": {
                "description": {
                    "identifier": "mazerunner:ascended_pillager", "materials": {"default": "illager"},
                    "textures": {"default": "textures/entity/illager/evoker"},
                    "geometry": {"default": "geometry.evoker"},
                    "render_controllers": ["controller.render.evoker"],
                    "spawn_egg": {"texture": "spawn_egg", "texture_index": 22}
                }
            }
        }
        with open(os.path.join(rp_entity_dir, "ascended_pillager.entity.json"), "w", encoding="utf-8") as f: json.dump(evoker_rp, f, indent=2)

        # Funções de Summon dos NPCs de Exploração
        for key, (disp, _, _) in self.KNOWN_EXPLORATION_NPCS.items():
            lines = [
                f"# Invocação de {disp} (Idempotente)",
                f"execute unless entity @e[type=mazerunner:npc_{key}] run summon mazerunner:npc_{key} 264 59 -2184",
                f'execute unless entity @e[type=mazerunner:npc_{key}] run tellraw @a {{"rawtext":[{{"text":"A§a§l newcomer§r has arrived in the §6§l§oloading area§r!"}}]}}'
            ]
            with open(os.path.join(func_custom_dir, f"summon_{key}.mcfunction"), "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")

        # Funções de Summon dos Bosses
        for key, ent_id in [("reaper", "mazerunner:reaper"), ("prometheus", "mazerunner:prometheus"), ("ascended_pillager", "mazerunner:ascended_pillager")]:
            with open(os.path.join(func_custom_dir, f"summon_{key}.mcfunction"), "w", encoding="utf-8") as f:
                f.write(f"summon {ent_id} ~ ~ ~\n")

        # Função Hall da Fama
        hof_lines = [
            "# Mazescapist Hall of Fame Statues Setup",
            'execute unless entity @e[name="Cyohg"] run summon armor_stand 99996.5 105.0 99955.5 0 0 mazerunner:cyohg "§6§lCyohg§r"',
            'execute unless entity @e[name="LordOfGnou"] run summon armor_stand 100000.5 105.0 99955.5 0 0 mazerunner:lordofgnou "§6§lLordOfGnou§r"',
            'execute unless entity @e[name="NereidRegulus"] run summon armor_stand 99979.5 105.0 99983.5 0 0 mazerunner:nereidregulus "§bNereidRegulus§r"',
            'execute unless entity @e[name="Cafeslayeur"] run summon armor_stand 99979.5 105.0 99987.5 0 0 mazerunner:cafeslayeur "§bCafeslayeur§r"',
            'execute unless entity @e[name="Beta Testers"] run summon armor_stand 99998.5 105.5 99956.5 0 0 mazerunner:beta_testers "§a§lBeta Testers§r"'
        ]
        with open(os.path.join(func_maze_dir, "setup_hall_of_fame.mcfunction"), "w", encoding="utf-8") as f:
            f.write("\n".join(hof_lines) + "\n")

        # Função de Inicialização Geral
        init_lines = [
            "# Mazescapist Bedrock 1.26.40 World Initialization",
            "scoreboard objectives add dayCounter dummy Day",
            "tickingarea add 250 0 -2250 330 80 -2150 maze_core",
            "tickingarea add 120 50 -2460 320 100 -1840 maze_doors",
            "function mazerunner/setup_hall_of_fame",
            'tellraw @a {"rawtext":[{"text":"§a[Mazescapist]§r World initialized for Bedrock 1.26.40!"}]}'
        ]
        with open(os.path.join(func_maze_dir, "init_world.mcfunction"), "w", encoding="utf-8") as f:
            f.write("\n".join(init_lines) + "\n")

        # Função Kit Inicial
        kit_lines = [
            "# Mazescapist Starter Kit for Bedrock Players",
            "give @s bread 16", "give @s torch 16", "give @s wooden_pickaxe 1",
            'tellraw @s {"rawtext":[{"text":"§a[Mazescapist]§r Starter kit received! Enjoy the maze!"}]}'
        ]
        with open(os.path.join(func_maze_dir, "starter_kit.mcfunction"), "w", encoding="utf-8") as f:
            f.write("\n".join(kit_lines) + "\n")

    def _integrate_packs(self, bp_h: str, rp_h: str):
        print("[*] Integrando Behavior Pack e Resource Pack no mundo Bedrock...")
        bp_dest = os.path.join(self.work_bedrock, "behavior_packs", "mazerunner_bp")
        rp_dest = os.path.join(self.work_bedrock, "resource_packs", "mazerunner_rp")
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


def resolve_input(param_val, candidates):
    if param_val and os.path.exists(param_val):
        return param_val
    for c in candidates:
        if os.path.exists(c):
            return c
    return param_val or candidates[0]


def main():
    parser = argparse.ArgumentParser(
        description="Conversor e Bridge Java <-> Bedrock 1.26.40+ (Mazescapist / MazeRunner)"
    )
    parser.add_argument("--java", default=None, help="Caminho do ZIP do mundo Java (padrão: inputs/java-version.zip ou java-version.zip)")
    parser.add_argument("--bedrock", default=None, help="Caminho do MCWORLD Bedrock inicial (padrão: inputs/bedrock-version.mcworld ou bedrock-version.mcworld)")
    parser.add_argument("--output", default="dist", help="Diretório de saída dos artefatos (.mcworld, .mcpack) [padrão: dist]")
    parser.add_argument("--packs", default="packs", help="Diretório dos pacotes descompactados BP/RP [padrão: packs]")
    parser.add_argument("--keep-temp", action="store_true", help="Preservar diretório temporário de extração (work_bedrock)")
    args = parser.parse_args()

    java_file = resolve_input(args.java, ["inputs/java-version.zip", "java-version.zip"])
    bedrock_file = resolve_input(args.bedrock, ["inputs/bedrock-version.mcworld", "bedrock-version.mcworld"])

    if not os.path.exists(java_file):
        print(f"[ERRO] Arquivo Java não encontrado: {java_file}")
        sys.exit(1)
    if not os.path.exists(bedrock_file):
        print(f"[ERRO] Arquivo Bedrock não encontrado: {bedrock_file}")
        sys.exit(1)

    app = MapConverterApp(
        java_zip=java_file,
        bedrock_world=bedrock_file,
        output_dir=args.output,
        packs_dir=args.packs,
        keep_temp=args.keep_temp
    )
    app.run()


if __name__ == "__main__":
    main()
