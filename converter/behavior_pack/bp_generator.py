#!/usr/bin/env python3
"""
Módulo Gerador do Behavior Pack Bedrock (Seções 15, 16, 22).
Autor: João Lucas Mayrinck
"""

import os
import json
import re
import uuid
import zipfile
import shutil
from typing import Dict, Any, List, Set
from converter.commands.translator import CommandTranslator

class BehaviorPackGenerator:
    """Gera manifestos, funções convertidas, loot tables, NPCs e tick.json do BP Bedrock."""

    @staticmethod
    def extract_trades_from_command(cmd: str) -> List[Dict[str, Any]]:
        """Extrai ofertas de trocas (Recipes:[...]) de comandos /summon villager."""
        trades = []
        rec_idx = cmd.find("Recipes:[")
        if rec_idx == -1:
            return trades

        start = rec_idx + len("Recipes:[")
        depth = 1
        pos = start
        while pos < len(cmd) and depth > 0:
            if cmd[pos] == '[':
                depth += 1
            elif cmd[pos] == ']':
                depth -= 1
            pos += 1
        raw_recipes = cmd[start:pos-1]

        # Extrai blocos {...} de cada receita
        recipe_blocks = []
        d = 0
        b_start = 0
        for i, ch in enumerate(raw_recipes):
            if ch == '{':
                if d == 0:
                    b_start = i
                d += 1
            elif ch == '}':
                d -= 1
                if d == 0:
                    recipe_blocks.append(raw_recipes[b_start:i+1])

        for block in recipe_blocks:
            buy_m = re.search(r'buy:\{id:"([^"]+)",Count:(\d+)b?\}', block)
            buyB_m = re.search(r'buyB:\{id:"([^"]+)",Count:(\d+)b?\}', block)
            sell_m = re.search(r'sell:\{id:"([^"]+)",Count:(\d+)b?\}', block)
            if buy_m and sell_m:
                wants = [{"item": buy_m.group(1).replace("minecraft:", ""), "quantity": int(buy_m.group(2))}]
                if buyB_m:
                    wants.append({"item": buyB_m.group(1).replace("minecraft:", ""), "quantity": int(buyB_m.group(2))})
                gives = [{"item": sell_m.group(1).replace("minecraft:", ""), "quantity": int(sell_m.group(2))}]
                trades.append({
                    "wants": wants,
                    "gives": gives,
                    "max_uses": 9999,
                    "trader_exp": 0
                })
        return trades

    @staticmethod
    def convert_loot_table(java_loot: dict) -> dict:
        """Converte uma tabela de loot Java para o formato Bedrock, preservando drops de esmeralda."""
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
                                "count": {"min": float(count.get("min", 1)), "max": float(count.get("max", 1))}
                            })
                        else:
                            functions.append({"function": "set_count", "count": int(count)})
                    elif "looting_enchant" in f_name:
                        functions.append({
                            "function": "looting_enchant",
                            "count": f.get("count", {"min": 0.0, "max": 1.0})
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

    @classmethod
    def generate(cls, datapacks_dir: str, target_bp_dir: str, world_name: str, safe_name: str, rp_header_uuid: str) -> Dict[str, Any]:
        if os.path.exists(target_bp_dir):
            shutil.rmtree(target_bp_dir, ignore_errors=True)
        os.makedirs(target_bp_dir, exist_ok=True)
        func_dir = os.path.join(target_bp_dir, "functions")
        os.makedirs(func_dir, exist_ok=True)
        trading_dir = os.path.join(target_bp_dir, "trading")
        entities_dir = os.path.join(target_bp_dir, "entities")

        # 1. UUIDs estáveis
        bp_header_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{safe_name}.bp.header.1.21.0"))
        bp_module_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{safe_name}.bp.module.1.21.0"))

        manifest = {
            "format_version": 2,
            "header": {
                "name": f"{world_name} Behavior Pack",
                "description": f"Behavior Pack for {world_name} (Bedrock 1.21+)",
                "uuid": bp_header_uuid,
                "version": [1, 0, 0],
                "min_engine_version": [1, 21, 0]
            },
            "modules": [{
                "type": "data",
                "description": f"{world_name} BP Logic",
                "uuid": bp_module_uuid,
                "version": [1, 0, 0]
            }]
        }
        if rp_header_uuid:
            manifest["dependencies"] = [{
                "uuid": rp_header_uuid,
                "version": [1, 0, 0]
            }]

        with open(os.path.join(target_bp_dir, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        # 2. Varredura e conversão de funções e identificação de NPCs
        known_npcs = set()
        converted_funcs = 0

        # Primeiro passo: extrair NPCs de summon
        if os.path.isdir(datapacks_dir):
            for item in os.listdir(datapacks_dir):
                full_p = os.path.join(datapacks_dir, item)
                func_files = []
                if item.endswith(".zip"):
                    try:
                        with zipfile.ZipFile(full_p, "r") as z:
                            for name in z.namelist():
                                if name.endswith(".mcfunction"):
                                    lines = z.read(name).decode("utf-8", errors="ignore").splitlines()
                                    func_files.append((name, lines))
                    except Exception:
                        pass
                elif os.path.isdir(full_p):
                    for root, _, files in os.walk(full_p):
                        for f in files:
                            if f.endswith(".mcfunction"):
                                fpath = os.path.join(root, f)
                                rel = os.path.relpath(fpath, full_p).replace("\\", "/")
                                with open(fpath, "r", encoding="utf-8", errors="ignore") as fp:
                                    lines = fp.read().splitlines()
                                func_files.append((rel, lines))

                for fname, lines in func_files:
                    for line in lines:
                        line_s = line.strip()
                        if "summon" in line_s and "villager" in line_s and "Recipes:" in line_s:
                            name_match = re.search(r'CustomName\s*:\s*\'(?:\{.*?"text"\s*:\s*"([^"]+)".*?\}|"([^"]+)")\'', line_s)
                            if name_match:
                                n_val = (name_match.group(1) or name_match.group(2)).lower()
                                clean_id = re.sub(r'[^a-zA-Z0-9_]', '_', n_val.replace("ö", "o").replace("ø", "o")).strip('_')
                                clean_stripped = clean_id.replace("_", "")
                                if clean_id:
                                    known_npcs.add(clean_id)
                                    known_npcs.add(clean_stripped)
                                    known_npcs.add(n_val)
                                    trades = cls.extract_trades_from_command(line_s)
                                    if trades:
                                        os.makedirs(trading_dir, exist_ok=True)
                                        t_file = os.path.join(trading_dir, f"{clean_id}_trades.json")
                                        trade_data = {"tiers": [{"total_exp_required": 0, "trades": trades}]}
                                        with open(t_file, "w", encoding="utf-8") as tf:
                                            json.dump(trade_data, tf, indent=2)

                                        # Cria definição de entidade customizada
                                        os.makedirs(entities_dir, exist_ok=True)
                                        ent_data = {
                                            "format_version": "1.16.0",
                                            "minecraft:entity": {
                                                "description": {
                                                    "identifier": f"{safe_name}:npc_{clean_id}",
                                                    "is_spawnable": True,
                                                    "is_summonable": True
                                                },
                                                "components": {
                                                    "minecraft:type_family": {"family": ["npc", "villager", "mob"]},
                                                    "minecraft:collision_box": {"width": 0.6, "height": 1.9},
                                                    "minecraft:movement": {"value": 0.0},
                                                    "minecraft:navigation.walk": {"can_path_over_water": True},
                                                    "minecraft:economy_trade_table": {
                                                        "table": f"trading/{clean_id}_trades.json",
                                                        "convert_trades_economy": True
                                                    },
                                                    "minecraft:interact": {
                                                        "interactions": [{
                                                            "on_interact": {"filters": {"test": "is_family", "subject": "other", "value": "player"}},
                                                            "open_trading": True
                                                        }]
                                                    }
                                                }
                                            }
                                        }
                                        with open(os.path.join(entities_dir, f"npc_{clean_id}.json"), "w", encoding="utf-8") as ef:
                                            json.dump(ent_data, ef, indent=2)
                                        if clean_id != clean_stripped:
                                            with open(os.path.join(entities_dir, f"npc_{clean_stripped}.json"), "w", encoding="utf-8") as ef:
                                                json.dump(ent_data, ef, indent=2)

                # Segundo passo: traduzir todas as funções e salvar em ambos os caminhos (namespaced e root)
                for fname, lines in func_files:
                    norm_path = fname
                    ns = "custom"
                    subpath = os.path.basename(fname)
                    if "data/" in norm_path:
                        parts = norm_path.split("data/", 1)[1].split("/")
                        ns = parts[0]
                        subpath = "/".join(parts[2:]) if len(parts) > 2 and parts[1] == "functions" else "/".join(parts[1:])

                    out_func_path = os.path.join(func_dir, ns, subpath)
                    root_func_path = os.path.join(func_dir, os.path.basename(fname))

                    os.makedirs(os.path.dirname(out_func_path), exist_ok=True)
                    converted_lines = []
                    for line in lines:
                        line_s = line.strip()
                        if not line_s or line_s.startswith("#"):
                            converted_lines.append(line)
                        else:
                            trans = CommandTranslator.translate(line_s, known_npcs, safe_name)
                            converted_lines.append(trans)

                    content_str = "\n".join(converted_lines) + "\n"
                    with open(out_func_path, "w", encoding="utf-8") as of:
                        of.write(content_str)
                    with open(root_func_path, "w", encoding="utf-8") as rf:
                        rf.write(content_str)
                    converted_funcs += 1

        # 3. Conversão e Cópia de Loot Tables de Entidades (Drops de Esmeraldas)
        target_loot_dir = os.path.join(target_bp_dir, "loot_tables", "entities")
        os.makedirs(target_loot_dir, exist_ok=True)
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

        # Fonte 1: Datapacks Java extraídos
        if os.path.isdir(datapacks_dir):
            for root, _, files in os.walk(datapacks_dir):
                if "loot_tables" in root and "entities" in root:
                    for lf in files:
                        if lf.endswith(".json"):
                            try:
                                with open(os.path.join(root, lf), "r", encoding="utf-8") as f:
                                    j_loot = json.load(f)
                                b_loot = cls.convert_loot_table(j_loot)
                                with open(os.path.join(target_loot_dir, lf), "w", encoding="utf-8") as f:
                                    json.dump(b_loot, f, indent=2)
                            except Exception:
                                pass

        # Fonte 2: Packs de referência (packs/*/loot_tables/entities)
        packs_dir = os.path.join(base_dir, "packs")
        if os.path.isdir(packs_dir):
            for d in os.listdir(packs_dir):
                ref_loot = os.path.join(packs_dir, d, "loot_tables", "entities")
                if os.path.isdir(ref_loot):
                    for lf in os.listdir(ref_loot):
                        if lf.endswith(".json"):
                            dst_f = os.path.join(target_loot_dir, lf)
                            if not os.path.exists(dst_f):
                                shutil.copyfile(os.path.join(ref_loot, lf), dst_f)

        # 4. Funções Utilitárias e Hooks de Tick com Tickingareas do Labirinto
        world_func_dir = os.path.join(func_dir, safe_name)
        os.makedirs(world_func_dir, exist_ok=True)

        init_lines = [
            f"# {world_name} Initialization for Bedrock 1.21+",
            "tickingarea add 250 0 -2250 350 120 -2150 maze_spawn",
            "tickingarea add 250 0 -2450 350 120 -2350 maze_north",
            "tickingarea add 450 0 -2250 550 120 -2050 maze_east",
            "# Ticking areas permanentes cobrindo todos os portões, levers e blocos de comando",
            "tickingarea add 100 0 -2460 350 120 -2420 maze_doors_north",
            "tickingarea add 100 0 -1865 350 120 -1820 maze_doors_south",
            "tickingarea add 490 0 -2260 540 120 -2040 maze_doors_east",
            "tickingarea add -95 0 -2260 -55 120 -2040 maze_doors_west",
            "tickingarea add 200 0 -2210 290 120 -2140 maze_center_clones",
            "tickingarea add -280 0 -2320 -150 120 -2180 maze_cmd_blocks",
            "gamerule commandblockoutput false",
            "gamerule sendcommandfeedback true",
            "gamerule doimmediaterespawn true",
            "gamerule domobspawning false",
            "scoreboard objectives add DAY_COUNTER dummy",
            "scoreboard objectives add dayCounter dummy",
            "scoreboard players add DAY_COUNTER dayCounter 0",
            "scoreboard players add #world dayCounter 0",
            f"scoreboard objectives add {safe_name}_initialized dummy",
            f"scoreboard players set #world {safe_name}_initialized 1",
            f'tellraw @a {{"rawtext":[{{"text":"§a[{world_name}]§r World and mechanics successfully initialized for Bedrock 1.21+!"}}]}}'
        ]
        init_content = "\n".join(init_lines) + "\n"
        with open(os.path.join(world_func_dir, "init_world.mcfunction"), "w", encoding="utf-8") as f:
            f.write(init_content)
        with open(os.path.join(func_dir, "init_world.mcfunction"), "w", encoding="utf-8") as f:
            f.write(init_content)
        custom_func_dir = os.path.join(func_dir, "custom")
        os.makedirs(custom_func_dir, exist_ok=True)
        with open(os.path.join(custom_func_dir, "init_world.mcfunction"), "w", encoding="utf-8") as f:
            f.write(init_content)

        tick_lines = [
            f"scoreboard objectives add {safe_name}_initialized dummy",
            f"execute unless score #world {safe_name}_initialized matches 1 run function {safe_name}/init_world"
        ]
        with open(os.path.join(func_dir, "tick.mcfunction"), "w", encoding="utf-8") as f:
            f.write("\n".join(tick_lines) + "\n")
        # tick.json DEVE estar em functions/tick.json no Bedrock
        with open(os.path.join(func_dir, "tick.json"), "w", encoding="utf-8") as f:
            json.dump({"values": ["tick"]}, f, indent=2)
        with open(os.path.join(target_bp_dir, "tick.json"), "w", encoding="utf-8") as f:
            json.dump({"values": ["tick"]}, f, indent=2)

        return {
            "header_uuid": bp_header_uuid,
            "module_uuid": bp_module_uuid,
            "functions_count": converted_funcs,
            "known_npcs": list(known_npcs)
        }

