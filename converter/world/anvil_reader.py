#!/usr/bin/env python3
"""
Módulo de Leitura e Auditoria de Regiões Anvil (MCA) para Java Edition.
Suporte para Minecraft 1.16.5+ (Nether Update e posterior).
Autor: João Lucas Mayrinck
"""

import os
import struct
import zlib
import io
import math
from typing import Dict, List, Any, Optional, Tuple
import nbtlib

FACING_VECTORS = {
    "down": (0, -1, 0),
    "up": (0, 1, 0),
    "north": (0, 0, -1),
    "south": (0, 0, 1),
    "west": (-1, 0, 0),
    "east": (1, 0, 0)
}

class AnvilReader:
    """Lê arquivos .mca de mundos Java e extrai block entities, entidades e chunks."""

    @staticmethod
    def parse_chunk_nbt(raw_sector: bytes) -> Optional[dict]:
        """Descompacta e desserializa um chunk em NBT."""
        if len(raw_sector) < 5:
            return None
        length = struct.unpack(">I", raw_sector[:4])[0]
        comp_type = raw_sector[4]
        compressed = raw_sector[5:4 + length]
        try:
            if comp_type == 2:  # Zlib Deflate
                uncomp = zlib.decompress(compressed)
            elif comp_type == 1:  # Gzip
                import gzip
                uncomp = gzip.decompress(compressed)
            else:
                return None
            return nbtlib.File.from_fileobj(io.BytesIO(uncomp))
        except Exception:
            return None

    @staticmethod
    def get_block_state_at(section: dict, lx: int, ly: int, lz: int) -> Tuple[str, str, bool]:
        """Extrai (block_name, facing, conditional) para coordenadas locais 0..15."""
        palette = section.get("Palette", [])
        if not palette:
            return "minecraft:air", "up", False

        if len(palette) == 1:
            entry = palette[0]
            name = str(entry.get("Name", "minecraft:air"))
            props = entry.get("Properties", {})
            facing = str(props.get("facing", "up"))
            conditional = str(props.get("conditional", "false")).lower() == "true"
            return name, facing, conditional

        block_states = section.get("BlockStates")
        if block_states is None or len(block_states) == 0:
            # Fallback para primeiro item com command block se houver
            for entry in palette:
                if "command_block" in str(entry.get("Name", "")).lower():
                    name = str(entry.get("Name"))
                    props = entry.get("Properties", {})
                    facing = str(props.get("facing", "up"))
                    conditional = str(props.get("conditional", "false")).lower() == "true"
                    return name, facing, conditional
            return "minecraft:air", "up", False

        # Decodifica array compacto de 64-bit inteiros
        palette_len = len(palette)
        bits_per_entry = max(4, (palette_len - 1).bit_length())
        block_idx = ly * 256 + lz * 16 + lx
        entries_per_long = 64 // bits_per_entry

        long_idx = block_idx // entries_per_long
        bit_offset = (block_idx % entries_per_long) * bits_per_entry

        if long_idx < len(block_states):
            val = block_states[long_idx]
            if isinstance(val, nbtlib.Long):
                val = int(val)
            val = val & 0xFFFFFFFFFFFFFFFF  # unsigned 64-bit
            palette_idx = (val >> bit_offset) & ((1 << bits_per_entry) - 1)
            if palette_idx < len(palette):
                entry = palette[palette_idx]
                name = str(entry.get("Name", "minecraft:air"))
                props = entry.get("Properties", {})
                facing = str(props.get("facing", "up"))
                conditional = str(props.get("conditional", "false")).lower() == "true"
                return name, facing, conditional

        return "minecraft:air", "up", False

    @classmethod
    def scan_region_command_blocks(cls, mca_path: str, dimension: str) -> List[Dict[str, Any]]:
        """Extrai todos os command blocks de um arquivo de região .mca."""
        command_blocks = []
        if not os.path.exists(mca_path):
            return command_blocks

        with open(mca_path, "rb") as f:
            raw = f.read()

        if len(raw) < 8192:
            return command_blocks

        filename = os.path.basename(mca_path)
        # Formato: r.X.Z.mca
        parts = filename.split(".")
        try:
            rx, rz = int(parts[1]), int(parts[2])
        except Exception:
            rx, rz = 0, 0

        for chunk_idx in range(1024):
            header_offset = chunk_idx * 4
            sector_offset = struct.unpack(">I", b"\x00" + raw[header_offset:header_offset + 3])[0] * 4096
            if sector_offset == 0 or sector_offset >= len(raw):
                continue

            chunk_nbt = cls.parse_chunk_nbt(raw[sector_offset:])
            if not chunk_nbt:
                continue

            level = chunk_nbt.get("Level", chunk_nbt)
            tile_entities = level.get("TileEntities", [])
            sections = {int(s.get("Y", -999)): s for s in level.get("Sections", [])}

            for te in tile_entities:
                te_id = str(te.get("id", "")).lower()
                if "command_block" not in te_id:
                    continue

                x = int(te.get("x", 0))
                y = int(te.get("y", 0))
                z = int(te.get("z", 0))
                cmd = str(te.get("Command", ""))
                auto = bool(int(te.get("auto", 0)))
                powered = bool(int(te.get("powered", 0)))
                condition_met = bool(int(te.get("conditionMet", 0)))
                custom_name = str(te.get("CustomName", "")) if "CustomName" in te else None

                # Normalização de tipo
                if "chain" in te_id:
                    cb_type = "minecraft:chain_command_block"
                elif "repeating" in te_id:
                    cb_type = "minecraft:repeating_command_block"
                else:
                    cb_type = "minecraft:command_block"

                # Busca estado do bloco (facing e conditional)
                sec_y = y // 16
                facing = "up"
                conditional = False
                if sec_y in sections:
                    lx, ly, lz = x % 16, y % 16, z % 16
                    _, facing, conditional = cls.get_block_state_at(sections[sec_y], lx, ly, lz)

                command_blocks.append({
                    "dimension": dimension,
                    "region": filename,
                    "chunk": [x // 16, z // 16],
                    "x": x,
                    "y": y,
                    "z": z,
                    "type": cb_type,
                    "command": cmd,
                    "auto": auto,
                    "powered": powered,
                    "condition_met": condition_met,
                    "conditional": conditional,
                    "facing": facing,
                    "custom_name": custom_name
                })

        return command_blocks

    @classmethod
    def scan_all_dimensions(cls, world_dir: str) -> List[Dict[str, Any]]:
        """Varre todas as dimensões do mundo e extrai todos os command blocks."""
        dim_map = {
            "overworld": os.path.join(world_dir, "region"),
            "nether": os.path.join(world_dir, "DIM-1", "region"),
            "the_end": os.path.join(world_dir, "DIM1", "region")
        }
        all_cbs = []
        for dim, reg_dir in dim_map.items():
            if not os.path.isdir(reg_dir):
                continue
            mca_files = [os.path.join(reg_dir, f) for f in os.listdir(reg_dir) if f.endswith(".mca")]
            for mca in mca_files:
                cbs = cls.scan_region_command_blocks(mca, dim)
                all_cbs.extend(cbs)
        return all_cbs

    @classmethod
    def build_command_chains(cls, cbs: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Agrupa command blocks em cadeias lógicas e sistemas (Seção 5 e 6)."""
        # Indexa por coordenadas (x, y, z, dimension)
        cb_index = {(cb["x"], cb["y"], cb["z"], cb["dimension"]): cb for cb in cbs}

        for cb in cbs:
            cb["next_block"] = None
            cb["prev_block"] = None
            cb["chain_id"] = None
            cb["order"] = 0

        # Conecta anterior e seguinte
        for cb in cbs:
            vec = FACING_VECTORS.get(cb.get("facing", "up"), (0, 1, 0))
            next_pos = (cb["x"] + vec[0], cb["y"] + vec[1], cb["z"] + vec[2], cb["dimension"])
            if next_pos in cb_index:
                next_cb = cb_index[next_pos]
                cb["next_block"] = [next_cb["x"], next_cb["y"], next_cb["z"]]
                next_cb["prev_block"] = [cb["x"], cb["y"], cb["z"]]

        # Constrói cadeias lineares
        chains = []
        visited = set()
        chain_counter = 1

        # Primeiro cabeças de cadeia (sem bloco anterior, ou repeating/impulse)
        heads = [cb for cb in cbs if cb["prev_block"] is None or cb["type"] in ("minecraft:command_block", "minecraft:repeating_command_block")]
        for head in heads:
            pos_key = (head["x"], head["y"], head["z"], head["dimension"])
            if pos_key in visited:
                continue

            curr = head
            chain_blocks = []
            order = 1
            chain_id = f"chain_{chain_counter}"

            while curr:
                c_key = (curr["x"], curr["y"], curr["z"], curr["dimension"])
                if c_key in visited:
                    break
                visited.add(c_key)
                curr["chain_id"] = chain_id
                curr["order"] = order
                chain_blocks.append({
                    "pos": [curr["x"], curr["y"], curr["z"]],
                    "type": curr["type"],
                    "auto": curr["auto"],
                    "conditional": curr["conditional"],
                    "command": curr["command"]
                })
                order += 1
                if curr["next_block"]:
                    next_key = (curr["next_block"][0], curr["next_block"][1], curr["next_block"][2], curr["dimension"])
                    curr = cb_index.get(next_key)
                else:
                    curr = None

            if chain_blocks:
                chains.append({
                    "chain_id": chain_id,
                    "dimension": head["dimension"],
                    "start_pos": [head["x"], head["y"], head["z"]],
                    "length": len(chain_blocks),
                    "is_loop": head["type"] == "minecraft:repeating_command_block",
                    "blocks": chain_blocks
                })
                chain_counter += 1

        # Blocos isolados ou em loops fechados não visitados
        for cb in cbs:
            pos_key = (cb["x"], cb["y"], cb["z"], cb["dimension"])
            if pos_key not in visited:
                visited.add(pos_key)
                chain_id = f"isolated_{chain_counter}"
                cb["chain_id"] = chain_id
                cb["order"] = 1
                chains.append({
                    "chain_id": chain_id,
                    "dimension": cb["dimension"],
                    "start_pos": [cb["x"], cb["y"], cb["z"]],
                    "length": 1,
                    "is_loop": cb["type"] == "minecraft:repeating_command_block",
                    "blocks": [{
                        "pos": [cb["x"], cb["y"], cb["z"]],
                        "type": cb["type"],
                        "auto": cb["auto"],
                        "conditional": cb["conditional"],
                        "command": cb["command"]
                    }]
                })
                chain_counter += 1

        return cbs, chains

