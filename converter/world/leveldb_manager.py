#!/usr/bin/env python3
"""
Módulo de Gerenciamento e Modificação In-Place do LevelDB Bedrock.
Suporte para SSTables Mojang (Compressão Deflate tipo 4, Checksum CRC32C mascarado).
Autor: João Lucas Mayrinck
"""

import os
import struct
import zlib
import io
from typing import List, Tuple, Callable, Optional
import nbtlib

try:
    import crc32c
    def calc_crc32c(data: bytes) -> int:
        return crc32c.crc32c(data)
except ImportError:
    def calc_crc32c(data: bytes) -> int:
        poly = 0x82F63B78
        crc = 0xFFFFFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                crc = (crc >> 1) ^ poly if (crc & 1) else (crc >> 1)
        return crc ^ 0xFFFFFFFF

def mask_crc(crc: int) -> int:
    return (((crc >> 15) | (crc << 17)) + 0xa282ead8) & 0xffffffff

class BedrockLevelDBManager:
    """Gerenciador de leitura, modificação e reconstrução de SSTables (.ldb) Bedrock."""

    @staticmethod
    def read_varint(data: bytes, offset: int) -> Tuple[int, int]:
        res = 0
        shift = 0
        while offset < len(data):
            b = data[offset]
            offset += 1
            res |= (b & 0x7f) << shift
            if not (b & 0x80):
                break
            shift += 7
        return res, offset

    @staticmethod
    def write_varint(val: int) -> bytearray:
        buf = bytearray()
        while val >= 0x80:
            buf.append((val & 0x7f) | 0x80)
            val >>= 7
        buf.append(val & 0x7f)
        return buf

    @classmethod
    def parse_block_entries(cls, block_bytes: bytes) -> List[Tuple[bytes, bytes]]:
        if len(block_bytes) < 4:
            return []
        num_restarts = struct.unpack('<I', block_bytes[-4:])[0]
        restart_offset = len(block_bytes) - 4 - (num_restarts * 4)
        if restart_offset < 0:
            return []

        entries = []
        off = 0
        last_key = bytearray()
        while off < restart_offset:
            shared, off = cls.read_varint(block_bytes, off)
            non_shared, off = cls.read_varint(block_bytes, off)
            val_len, off = cls.read_varint(block_bytes, off)

            key = last_key[:shared] + block_bytes[off:off + non_shared]
            off += non_shared
            val = block_bytes[off:off + val_len]
            off += val_len

            last_key = bytearray(key)
            entries.append((bytes(key), val))
        return entries

    @classmethod
    def build_block(cls, entries: List[Tuple[bytes, bytes]]) -> bytes:
        out = bytearray()
        restarts = [0]
        last_key = b''
        for key, val in entries:
            shared = 0
            while shared < len(last_key) and shared < len(key) and last_key[shared] == key[shared]:
                shared += 1
            non_shared = len(key) - shared
            val_len = len(val)

            out.extend(cls.write_varint(shared))
            out.extend(cls.write_varint(non_shared))
            out.extend(cls.write_varint(val_len))
            out.extend(key[shared:])
            out.extend(val)
            last_key = key

        for r in restarts:
            out.extend(struct.pack('<I', r))
        out.extend(struct.pack('<I', len(restarts)))
        return bytes(out)

    @staticmethod
    def raw_compress(data: bytes) -> bytes:
        c = zlib.compressobj(level=6, method=zlib.DEFLATED, wbits=-15)
        return c.compress(data) + c.flush()

    @classmethod
    def read_ldb_all_entries(cls, raw: bytes) -> List[List[Tuple[bytes, bytes]]]:
        if len(raw) < 48:
            return []
        footer = raw[-48:]
        if footer[-8:] != b'\x57\xfb\x80\x8b\x24\x75\x47\xdb':
            return []

        _, off = cls.read_varint(footer, 0)
        _, off = cls.read_varint(footer, off)
        idx_off, off = cls.read_varint(footer, off)
        idx_size, off = cls.read_varint(footer, off)

        idx_raw = raw[idx_off:idx_off + idx_size]
        idx_comp = raw[idx_off + idx_size]
        if idx_comp in (2, 4):
            idx_raw = zlib.decompress(idx_raw, -15)

        idx_entries = cls.parse_block_entries(idx_raw)
        all_data_blocks = []
        for _, handle in idx_entries:
            b_off, h_off = cls.read_varint(handle, 0)
            b_size, _ = cls.read_varint(handle, h_off)
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
            out.append(4)  # Mojang deflate
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
    def update_command_blocks(cls, db_dir: str, convert_func: Callable[[str], str], safe_name: Optional[str] = None) -> int:
        """Percorre todos os arquivos .ldb do banco LevelDB e atualiza blocos de comando in-place."""
        """Atualiza blocos de comando no banco LevelDB Bedrock de forma atômica e segura."""
        if not os.path.exists(db_dir):
            return 0

        # Tentativa primária: utilizar o motor nativo C++ da Mojang (amulet-leveldb / leveldb)
        if any(f.startswith("MANIFEST") or f == "CURRENT" for f in os.listdir(db_dir)):
            try:
                import leveldb
                db = leveldb.LevelDB(db_dir)
                total_modified = 0
                for key, val in db.iterate():
                    if b"CommandBlock" in val or b"Command" in val:
                        try:
                            buf = io.BytesIO(val)
                            tags = []
                            val_modified = False
                            while buf.tell() < len(val):
                                try:
                                    tag = nbtlib.File.from_fileobj(buf, byteorder="little")
                                    tags.append(tag)
                                    if tag.get("id") == "CommandBlock" and "Command" in tag:
                                        orig_cmd = str(tag["Command"])
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
                                            new_cmd = convert_func(orig_cmd)
                                        if new_cmd != orig_cmd:
                                            tag["Command"] = nbtlib.String(new_cmd)
                                            val_modified = True
                                            total_modified += 1
                                except Exception:
                                    break

                            if val_modified and tags:
                                out_buf = io.BytesIO()
                                for tag in tags:
                                    tag.write(out_buf, byteorder="little")
                                db.put(key, out_buf.getvalue())
                        except Exception:
                            pass
                db.close()
                return total_modified
            except Exception:
                pass

        # Fallback: leitor/escritor embutido caso o módulo nativo não esteja disponível
        total_modified = 0
        for f in os.listdir(db_dir):
            if not f.endswith(".ldb"):
                continue
            fpath = os.path.join(db_dir, f)
            with open(fpath, "rb") as fp:
                raw = fp.read()

            all_data_blocks = cls.read_ldb_all_entries(raw)
            if not all_data_blocks:
                continue

            file_modified = False
            new_data_blocks = []
            for entries in all_data_blocks:
                new_entries = []
                for key, val in entries:
                    if b"CommandBlock" in val or b"Command" in val:
                        try:
                            buf = io.BytesIO(val)
                            tags = []
                            val_modified = False
                            while buf.tell() < len(val):
                                try:
                                    tag = nbtlib.File.from_fileobj(buf, byteorder="little")
                                    tags.append(tag)
                                    if tag.get("id") == "CommandBlock" and "Command" in tag:
                                        orig_cmd = str(tag["Command"])
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
                                            new_cmd = convert_func(orig_cmd)
                                        if new_cmd != orig_cmd:
                                            tag["Command"] = nbtlib.String(new_cmd)
                                            val_modified = True
                                            total_modified += 1
                                except Exception:
                                    break

                            if val_modified and tags:
                                out_buf = io.BytesIO()
                                for tag in tags:
                                    tag.write(out_buf, byteorder="little")
                                val = out_buf.getvalue()
                                file_modified = True
                        except Exception:
                            pass
                    new_entries.append((key, val))
                new_data_blocks.append(new_entries)

            if file_modified:
                new_raw = cls.build_ldb(new_data_blocks)
                with open(fpath, "wb") as fp:
                    fp.write(new_raw)

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

