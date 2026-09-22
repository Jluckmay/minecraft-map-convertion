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

    @classmethod
    def generate(cls, datapacks_dir: str, target_bp_dir: str, world_name: str, safe_name: str, rp_header_uuid: str) -> Dict[str, Any]:
        os.makedirs(target_bp_dir, exist_ok=True)
        func_dir = os.path.join(target_bp_dir, "functions")
        os.makedirs(func_dir, exist_ok=True)
        trading_dir = os.path.join(target_bp_dir, "trading")
        entities_dir = os.path.join(target_bp_dir, "entities")

        # 1. UUIDs estáveis
        bp_header_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{safe_name}.bp.header.1.20.0"))
        bp_module_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{safe_name}.bp.module.1.20.0"))

        manifest = {
            "format_version": 2,
            "header": {
                "name": f"{world_name} Behavior Pack",
                "description": f"Behavior Pack for {world_name} (Bedrock 1.20+)",
                "uuid": bp_header_uuid,
                "version": [1, 0, 0],
                "min_engine_version": [1, 20, 0]
            },
            "modules": [{
                "type": "data",
                "description": f"{world_name} BP Logic",
                "uuid": bp_module_uuid,
                "version": [1, 0, 0]
            }],
            "dependencies": [{
                "uuid": rp_header_uuid,
                "version": [1, 0, 0]
            }]
        }
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
                                clean_id = re.sub(r'[^a-zA-Z0-9_]', '', n_val)
                                if clean_id:
                                    known_npcs.add(clean_id)
                                    trades = cls.extract_trades_from_command(line_s)
                                    if trades:
                                        os.makedirs(trading_dir, exist_ok=True)
                                        t_file = os.path.join(trading_dir, f"{clean_id}_trades.json")
                                        trade_data = {"tiers": [{"total_exp_required": 0, "trades": trades}]}
                                        with open(t_file, "w", encoding="utf-8") as tf:
                                            json.dump(trade_data, tf, indent=2)

                                        # Cria definição de entidade customizada
                                        os.makedirs(entities_dir, exist_ok=True)
                                        ent_file = os.path.join(entities_dir, f"npc_{clean_id}.json")
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
                                        with open(ent_file, "w", encoding="utf-8") as ef:
                                            json.dump(ent_data, ef, indent=2)

                # Segundo passo: traduzir todas as funções
                for fname, lines in func_files:
                    norm_path = fname
                    if "data/" in norm_path:
                        parts = norm_path.split("data/", 1)[1].split("/")
                        ns = parts[0]
                        subpath = "/".join(parts[2:]) if len(parts) > 2 and parts[1] == "functions" else "/".join(parts[1:])
                        out_func_path = os.path.join(func_dir, ns, subpath)
                    else:
                        out_func_path = os.path.join(func_dir, os.path.basename(fname))

                    os.makedirs(os.path.dirname(out_func_path), exist_ok=True)
                    converted_lines = []
                    for line in lines:
                        line_s = line.strip()
                        if not line_s or line_s.startswith("#"):
                            converted_lines.append(line)
                        else:
                            trans = CommandTranslator.translate(line_s, known_npcs, safe_name)
                            converted_lines.append(trans)

                    with open(out_func_path, "w", encoding="utf-8") as of:
                        of.write("\n".join(converted_lines) + "\n")
                    converted_funcs += 1

        # 3. Funções Utilitárias e Hooks de Tick
        world_func_dir = os.path.join(func_dir, safe_name)
        os.makedirs(world_func_dir, exist_ok=True)

        init_lines = [
            f"# {world_name} Initialization for Bedrock 1.20+",
            f"tickingarea add 0 0 0 0 319 0 {safe_name}_core",
            f"scoreboard objectives add {safe_name}_initialized dummy",
            f"scoreboard players set #world {safe_name}_initialized 1",
            f'tellraw @a {{"rawtext":[{{"text":"§a[{world_name}]§r World successfully initialized for Bedrock 1.20+!"}}]}}'
        ]
        with open(os.path.join(world_func_dir, "init_world.mcfunction"), "w", encoding="utf-8") as f:
            f.write("\n".join(init_lines) + "\n")

        tick_lines = [
            f"scoreboard objectives add {safe_name}_initialized dummy",
            f"execute unless score #world {safe_name}_initialized matches 1 run function {safe_name}/init_world"
        ]
        with open(os.path.join(func_dir, "tick.mcfunction"), "w", encoding="utf-8") as f:
            f.write("\n".join(tick_lines) + "\n")
        with open(os.path.join(target_bp_dir, "tick.json"), "w", encoding="utf-8") as f:
            json.dump({"values": ["tick"]}, f, indent=2)

        return {
            "header_uuid": bp_header_uuid,
            "module_uuid": bp_module_uuid,
            "functions_count": converted_funcs,
            "known_npcs": list(known_npcs)
        }

