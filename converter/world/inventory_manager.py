#!/usr/bin/env python3
"""
Módulo de Preservação e Conversão de Inventários de Jogadores e Contêineres.
Suporte para Minecraft Java (level.dat / playerdata) -> Bedrock (~local_player / LevelDB).
Autor: João Lucas Mayrinck
"""

import os
import io
import gc
import gzip
import zipfile
from typing import Dict, List, Any, Optional, Tuple
import nbtlib

try:
    import leveldb
    HAS_LEVELDB = True
except ImportError:
    HAS_LEVELDB = False


# Mapeamento de itens clássicos Java para Bedrock quando aplicável
ITEM_MAP = {
    "minecraft:scute": "minecraft:turtle_scute",
    "minecraft:totem_of_undying": "minecraft:totem_of_undying",
    "minecraft:lead": "minecraft:lead",
}

def map_item_id(java_id: str) -> str:
    """Mapeia identificadores de itens Java para Bedrock."""
    clean_id = java_id if java_id.startswith("minecraft:") else f"minecraft:{java_id}"
    return ITEM_MAP.get(clean_id, clean_id)


class PlayerInventoryManager:
    """Gerenciador de conversão e sincronização de inventários entre Java e Bedrock."""

    @staticmethod
    def extract_java_player_data(java_world_dir: str) -> Dict[str, Any]:
        """Extrai inventário, armaduras, offhand e ender chest do jogador Java."""
        res = {
            "inventory": [],
            "armor": [None, None, None, None],  # [feet, legs, torso, head]
            "offhand": None,
            "ender_items": [],
            "xp_level": 0,
            "score": 0
        }

        player_compound = None

        # 1. Tenta carregar de arquivo ZIP ou diretório
        if os.path.isfile(java_world_dir) and java_world_dir.lower().endswith(".zip"):
            try:
                with zipfile.ZipFile(java_world_dir, "r") as z:
                    for name in z.namelist():
                        if name.endswith("level.dat"):
                            raw = z.read(name)
                            try:
                                decomp = gzip.decompress(raw)
                                nbt = nbtlib.File.from_fileobj(io.BytesIO(decomp))
                            except Exception:
                                nbt = nbtlib.File.from_fileobj(io.BytesIO(raw))
                            player = nbt.get("Data", {}).get("Player")
                            if player and (player.get("Inventory") or player.get("EnderItems")):
                                player_compound = player
                                break
                    if not player_compound:
                        for name in z.namelist():
                            if "playerdata/" in name and name.endswith(".dat"):
                                try:
                                    raw = z.read(name)
                                    try:
                                        decomp = gzip.decompress(raw)
                                        pnbt = nbtlib.File.from_fileobj(io.BytesIO(decomp))
                                    except Exception:
                                        pnbt = nbtlib.File.from_fileobj(io.BytesIO(raw))
                                    if pnbt.get("Inventory") or pnbt.get("EnderItems"):
                                        player_compound = pnbt
                                        break
                                except Exception:
                                    pass
            except Exception:
                pass
        else:
            level_dat_path = os.path.join(java_world_dir, "level.dat")
            if os.path.exists(level_dat_path):
                try:
                    with open(level_dat_path, "rb") as f:
                        raw = f.read()
                    try:
                        decomp = gzip.decompress(raw)
                        nbt = nbtlib.File.from_fileobj(io.BytesIO(decomp))
                    except Exception:
                        nbt = nbtlib.File.from_fileobj(io.BytesIO(raw))
                    player = nbt.get("Data", {}).get("Player")
                    if player and (player.get("Inventory") or player.get("EnderItems")):
                        player_compound = player
                except Exception:
                    pass

            # 2. Se vazio em level.dat, busca em playerdata/*.dat
            if not player_compound:
                pdata_dir = os.path.join(java_world_dir, "playerdata")
                if os.path.isdir(pdata_dir):
                    for pf in os.listdir(pdata_dir):
                        if pf.endswith(".dat"):
                            try:
                                pnbt = nbtlib.load(os.path.join(pdata_dir, pf))
                                if pnbt.get("Inventory") or pnbt.get("EnderItems"):
                                    player_compound = pnbt
                                    break
                            except Exception:
                                pass

        if not player_compound:
            return res

        res["xp_level"] = int(player_compound.get("XpLevel", 0))
        res["score"] = int(player_compound.get("Score", 0))

        # Itera sobre itens do inventário Java
        for it in player_compound.get("Inventory", []):
            slot = int(it.get("Slot", 0))
            item_id = str(it.get("id", "minecraft:air"))
            count = int(it.get("Count", 1))
            tag = it.get("tag")

            # Danos
            damage = 0
            if tag and "Damage" in tag:
                try:
                    damage = int(tag["Damage"])
                except Exception:
                    pass

            item_data = {
                "id": item_id,
                "count": count,
                "damage": damage,
                "tag": tag
            }

            # Slots 0 a 35: inventário principal e hotbar
            if 0 <= slot <= 35:
                res["inventory"].append((slot, item_data))
            # Slots de Armadura Java: 100=pés, 101=pernas, 102=peitoral, 103=capacete
            elif slot == 100:  # Botas / Feet
                res["armor"][0] = item_data
            elif slot == 101:  # Calças / Legs
                res["armor"][1] = item_data
            elif slot == 102:  # Peitoral / Torso
                res["armor"][2] = item_data
            elif slot == 103:  # Capacete / Head
                res["armor"][3] = item_data
            # Slot -106: mão secundária / Offhand
            elif slot == -106 or slot == 150:
                res["offhand"] = item_data

        # Ender Chest
        for it in player_compound.get("EnderItems", []):
            slot = int(it.get("Slot", 0))
            item_id = str(it.get("id", "minecraft:air"))
            count = int(it.get("Count", 1))
            tag = it.get("tag")
            damage = 0
            if tag and "Damage" in tag:
                try:
                    damage = int(tag["Damage"])
                except Exception:
                    pass
            res["ender_items"].append((slot, {
                "id": item_id,
                "count": count,
                "damage": damage,
                "tag": tag
            }))

        return res

    @staticmethod
    def create_bedrock_item(slot: int, item_data: dict) -> nbtlib.Compound:
        """Constrói um Compound NBT de item no formato nativo Bedrock."""
        bedrock_name = map_item_id(item_data["id"])
        c = nbtlib.Compound({
            "Count": nbtlib.Byte(item_data["count"]),
            "Damage": nbtlib.Short(item_data["damage"]),
            "Name": nbtlib.String(bedrock_name),
            "Slot": nbtlib.Byte(slot),
            "WasPickedUp": nbtlib.Byte(0)
        })
        if item_data.get("tag"):
            # Preserva tags NBT (ex: display name, enchantments)
            c["tag"] = item_data["tag"]
        return c

    @classmethod
    def sync_player_inventory(cls, java_world_dir: str, bedrock_db_dir: str) -> int:
        """
        Sincroniza o inventário do jogador Java com o ~local_player no banco LevelDB Bedrock.
        Retorna o total de itens injetados.
        """
        if not HAS_LEVELDB or not os.path.isdir(bedrock_db_dir):
            return 0
        if not os.path.exists(os.path.join(bedrock_db_dir, "CURRENT")):
            return 0

        pdata = cls.extract_java_player_data(java_world_dir)
        total_items = (len(pdata["inventory"]) +
                       sum(1 for a in pdata["armor"] if a) +
                       (1 if pdata["offhand"] else 0) +
                       len(pdata["ender_items"]))

        if total_items == 0:
            return 0

        db = None
        try:
            db = leveldb.LevelDB(bedrock_db_dir)
            player_key = b"~local_player"

            try:
                raw = db.get(player_key)
                pnbt = nbtlib.File.from_fileobj(io.BytesIO(raw), byteorder="little")
            except Exception:
                # Se não existir chave ~local_player, cria uma estrutura base
                pnbt = nbtlib.File({
                    "Pos": nbtlib.List[nbtlib.Float]([0.0, 64.0, 0.0]),
                    "Motion": nbtlib.List[nbtlib.Float]([0.0, 0.0, 0.0]),
                    "Rotation": nbtlib.List[nbtlib.Float]([0.0, 0.0]),
                    "DimensionId": nbtlib.Int(0),
                    "PlayerGameMode": nbtlib.Int(2),
                }, byteorder="little")

            # 1. Injeta inventário principal
            b_inv = []
            for slot, it in pdata["inventory"]:
                b_inv.append(cls.create_bedrock_item(slot, it))
            pnbt["Inventory"] = nbtlib.List[nbtlib.Compound](b_inv)

            # 2. Injeta armaduras (4 slots: 0=feet, 1=legs, 2=torso, 3=head)
            b_armor = []
            for i in range(4):
                it = pdata["armor"][i]
                if it:
                    b_armor.append(cls.create_bedrock_item(i, it))
                else:
                    b_armor.append(nbtlib.Compound({}))
            pnbt["Armor"] = nbtlib.List[nbtlib.Compound](b_armor)

            # 3. Injeta mão secundária (offhand)
            if pdata["offhand"]:
                pnbt["Offhand"] = nbtlib.List[nbtlib.Compound]([
                    cls.create_bedrock_item(0, pdata["offhand"])
                ])

            # 4. Injeta baú do fim (Ender Chest)
            if pdata["ender_items"]:
                b_ender = []
                for slot, it in pdata["ender_items"]:
                    b_ender.append(cls.create_bedrock_item(slot, it))
                pnbt["EnderChestInventory"] = nbtlib.List[nbtlib.Compound](b_ender)

            # Grava no banco LevelDB
            out_buf = io.BytesIO()
            pnbt.write(out_buf, byteorder="little")
            db.put(player_key, out_buf.getvalue())
            return total_items
        finally:
            if db is not None:
                del db
                gc.collect()

    @classmethod
    def audit_leveldb_containers(cls, bedrock_db_dir: str) -> Tuple[int, int]:
        """
        Audita contêineres e baús no banco LevelDB.
        Retorna (total_contêineres, contêineres_com_itens).
        """
        if not HAS_LEVELDB or not os.path.isdir(bedrock_db_dir):
            return 0, 0
        if not os.path.exists(os.path.join(bedrock_db_dir, "CURRENT")):
            return 0, 0

        db = None
        total_containers = 0
        containers_with_items = 0
        container_ids = {"Chest", "TrappedChest", "Barrel", "ShulkerBox", "Dispenser", "Dropper", "Hopper"}

        try:
            db = leveldb.LevelDB(bedrock_db_dir)
            for k, val in db.items():
                if len(k) >= 9 and k[8:9] == b'1':
                    buf = io.BytesIO(val)
                    while buf.tell() < len(val):
                        try:
                            te_nbt = nbtlib.File.from_fileobj(buf, byteorder="little")
                            te_id = str(te_nbt.get("id", ""))
                            if te_id in container_ids:
                                total_containers += 1
                                items = te_nbt.get("Items", [])
                                if items and len(items) > 0:
                                    containers_with_items += 1
                        except Exception:
                            break
        finally:
            if db is not None:
                del db
                gc.collect()

        return total_containers, containers_with_items
