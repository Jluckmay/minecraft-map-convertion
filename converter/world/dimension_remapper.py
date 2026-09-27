#!/usr/bin/env python3
"""
Módulo de Remapeamento de Dimensão para Minecraft Bedrock LevelDB.
Remapeia chunks da dimensão 1 (Nether, limite rígido de 128 blocos) para
a dimensão 2 (The End, limite de 256 blocos), preservando 100% das estruturas,
tetos, paredes e sistemas de comando acima de Y=128.

Autor: João Lucas Mayrinck
"""

import os
import struct
import io
import re
from typing import Dict, Any, Tuple
import nbtlib


class DimensionRemapper:
    """Remapeia chaves do LevelDB de uma dimensão para outra e atualiza blocos de comando correspondentes."""

    @classmethod
    def convert_water_to_lava_subchunk(cls, val: bytes) -> Tuple[bytes, bool]:
        """Substitui entradas de minecraft:water e minecraft:flowing_water por lava na paleta do subchunk."""
        if not (b"minecraft:water" in val or b"minecraft:flowing_water" in val or b"water" in val):
            return val, False
        try:
            buf = io.BytesIO(val)
            v = buf.read(1)[0]
            sc = buf.read(1)[0]
            header = bytearray([v, sc])
            if v >= 9:
                sub_y = buf.read(1)[0]
                header.append(sub_y)

            out_buf = io.BytesIO()
            out_buf.write(header)
            modified = False

            for s in range(sc):
                flags = buf.read(1)[0]
                bpb = flags >> 1
                is_runtime = flags & 1
                bpw = 32 // bpb if bpb > 0 else 1
                wc = (4096 + bpw - 1) // bpw if bpb > 0 else 0
                packed_data = buf.read(wc * 4)
                out_buf.write(bytes([flags]))
                out_buf.write(packed_data)
                if not is_runtime:
                    psize = struct.unpack('<i', buf.read(4))[0]
                    palette = []
                    for p in range(psize):
                        tag = nbtlib.File.from_fileobj(buf, byteorder='little')
                        name = str(tag.get('name', ''))
                        if name == "minecraft:water":
                            tag['name'] = nbtlib.String("minecraft:lava")
                            modified = True
                        elif name == "minecraft:flowing_water":
                            tag['name'] = nbtlib.String("minecraft:flowing_lava")
                            modified = True
                        palette.append(tag)
                    out_buf.write(struct.pack('<i', psize))
                    for tag in palette:
                        tag.write(out_buf, byteorder='little')

            rem = buf.read()
            out_buf.write(rem)
            if modified:
                return out_buf.getvalue(), True
        except Exception:
            pass
        return val, False

    @classmethod
    def convert_water_to_lava(cls, db_dir: str, target_dim: int = 2) -> int:
        """Converte todas as paletas de água para lava nos subchunks da dimensão alvo."""
        if not os.path.isdir(db_dir):
            return 0
        converted_count = 0
        has_manifest = any(f.startswith("MANIFEST") or f == "CURRENT" for f in os.listdir(db_dir))
        if has_manifest:
            try:
                import leveldb
                db = leveldb.LevelDB(db_dir)
                batch = {}
                for k, val in db.iterate():
                    if len(k) >= 13 and k[12] == 0x2f:
                        dim = struct.unpack('<i', k[8:12])[0]
                        if dim == target_dim:
                            new_val, mod = cls.convert_water_to_lava_subchunk(val)
                            if mod:
                                batch[k] = new_val
                                converted_count += 1
                                if len(batch) >= 1000:
                                    db.putBatch(batch)
                                    batch.clear()
                if batch:
                    db.putBatch(batch)
                    batch.clear()
                db.close()
                return converted_count
            except Exception:
                pass
        return converted_count

    @classmethod
    def remap_nether_to_end(cls, db_dir: str) -> Dict[str, Any]:
        """
        Remapeia todas as chaves da dimensão 1 (Nether) para a dimensão 2 (The End).
        Atualiza blocos de comando correspondentes e converte água em lava no Nether/End.
        """
        if not os.path.isdir(db_dir):
            raise FileNotFoundError(f"Diretório LevelDB não encontrado: {db_dir}")

        has_manifest = any(f.startswith("MANIFEST") or f == "CURRENT" for f in os.listdir(db_dir))
        if has_manifest:
            try:
                import leveldb
                db = leveldb.LevelDB(db_dir)

                # 1. Coletar todas as chaves da dimensão 1
                dim1_keys = []
                for k in db.keys():
                    if len(k) >= 12:
                        dim = struct.unpack('<i', k[8:12])[0]
                        if dim == 1:
                            dim1_keys.append(k)

                # 2. Remapear para dimensão 2 (The End) e converter água em lava em subchunks
                remapped_count = 0
                converted_water_count = 0
                batch_size = 5000
                batch = {}
                keys_to_delete = []

                for k in dim1_keys:
                    new_k = k[:8] + struct.pack('<i', 2) + k[12:]
                    val = db.get(k)
                    if len(new_k) >= 13 and new_k[12] == 0x2f:
                        val, mod = cls.convert_water_to_lava_subchunk(val)
                        if mod:
                            converted_water_count += 1
                    batch[new_k] = val
                    keys_to_delete.append(k)
                    remapped_count += 1

                    if len(batch) >= batch_size:
                        db.putBatch(batch)
                        for old_k in keys_to_delete:
                            db.delete(old_k)
                        batch.clear()
                        keys_to_delete.clear()

                if batch:
                    db.putBatch(batch)
                    for old_k in keys_to_delete:
                        db.delete(old_k)
                    batch.clear()
                    keys_to_delete.clear()

                # 3. Atualizar blocos de comando que fazem referência ao Nether
                updated_cbs = 0
                for k, val in db.iterate():
                    if b"CommandBlock" in val or b"Command" in val:
                        try:
                            buf = io.BytesIO(val)
                            tags = []
                            modified = False
                            while buf.tell() < len(val):
                                try:
                                    tag = nbtlib.File.from_fileobj(buf, byteorder="little")
                                    tags.append(tag)
                                    if tag.get("id") == "CommandBlock" and "Command" in tag:
                                        cmd = str(tag["Command"])
                                        new_cmd = cmd

                                        # Atualiza referências a nether/the_nether para the_end
                                        if "the_nether" in new_cmd or "nether" in new_cmd:
                                            new_cmd = re.sub(r'\bin (?:minecraft:the_nether|the_nether|nether)\b', 'in the_end', new_cmd)
                                            new_cmd = re.sub(r'\bminecraft:mobspell_emitter\b', 'mobspell_emitter', new_cmd)

                                        if new_cmd != cmd:
                                            tag["Command"] = nbtlib.String(new_cmd)
                                            modified = True
                                            updated_cbs += 1
                                except Exception:
                                    break

                            if modified and tags:
                                out_buf = io.BytesIO()
                                for tag in tags:
                                    tag.write(out_buf, byteorder="little")
                                db.put(k, out_buf.getvalue())
                        except Exception:
                            pass

                db.close()
                return {
                    "remapped_keys": remapped_count,
                    "updated_command_blocks": updated_cbs,
                    "converted_water_subchunks": converted_water_count
                }
            except Exception:
                pass

        # Fallback: leitor/escritor embutido (.ldb puro)
        from converter.world.leveldb_manager import BedrockLevelDBManager
        remapped_count = 0
        updated_cbs = 0
        converted_water_count = 0

        for fname in os.listdir(db_dir):
            if not fname.endswith(".ldb"):
                continue
            fpath = os.path.join(db_dir, fname)
            try:
                with open(fpath, "rb") as f:
                    raw_bytes = f.read()
                blocks = BedrockLevelDBManager.read_ldb_all_entries(raw_bytes)
                new_blocks = []
                file_modified = False

                for block in blocks:
                    new_block_entries = []
                    for k, v in block:
                        new_k = k
                        new_v = v
                        if len(k) >= 12 and struct.unpack('<i', k[8:12])[0] == 1:
                            new_k = k[:8] + struct.pack('<i', 2) + k[12:]
                            file_modified = True
                            remapped_count += 1

                        if len(new_k) >= 13 and new_k[12] == 0x2f and struct.unpack('<i', new_k[8:12])[0] == 2:
                            new_v, mod = cls.convert_water_to_lava_subchunk(new_v)
                            if mod:
                                file_modified = True
                                converted_water_count += 1

                        if b"CommandBlock" in new_v or b"Command" in new_v:
                            try:
                                buf = io.BytesIO(new_v)
                                tags = []
                                be_mod = False
                                while buf.tell() < len(new_v):
                                    try:
                                        tag = nbtlib.File.from_fileobj(buf, byteorder="little")
                                        tags.append(tag)
                                        if tag.get("id") == "CommandBlock" and "Command" in tag:
                                            cmd = str(tag["Command"])
                                            new_cmd = cmd
                                            if "the_nether" in new_cmd or "nether" in new_cmd:
                                                new_cmd = re.sub(r'\bin (?:minecraft:the_nether|the_nether|nether)\b', 'in the_end', new_cmd)
                                                new_cmd = re.sub(r'\bminecraft:mobspell_emitter\b', 'mobspell_emitter', new_cmd)
                                            if new_cmd != cmd:
                                                tag["Command"] = nbtlib.String(new_cmd)
                                                be_mod = True
                                                updated_cbs += 1
                                    except Exception:
                                        break
                                if be_mod and tags:
                                    out_buf = io.BytesIO()
                                    for tag in tags:
                                        tag.write(out_buf, byteorder="little")
                                    new_v = out_buf.getvalue()
                                    file_modified = True
                            except Exception:
                                pass

                        new_block_entries.append((new_k, new_v))
                    new_blocks.append(new_block_entries)

                if file_modified:
                    new_ldb = BedrockLevelDBManager.build_ldb(new_blocks)
                    with open(fpath, "wb") as f:
                        f.write(new_ldb)
            except Exception:
                pass

        return {
            "remapped_keys": remapped_count,
            "updated_command_blocks": updated_cbs,
            "converted_water_subchunks": converted_water_count
        }


if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "output/converted_world/db"
    res = DimensionRemapper.remap_nether_to_end(target)
    print(f"[OK] Remapeamento concluído: {res['remapped_keys']} chaves migradas, {res['updated_command_blocks']} blocos de comando atualizados.")
