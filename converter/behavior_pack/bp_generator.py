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
                                        formatted_trades = []
                                        for tr in trades:
                                            ft = {
                                                "wants": [
                                                    {
                                                        "item": f"minecraft:{w['item'].replace('minecraft:', '')}",
                                                        "quantity": w["quantity"]
                                                    }
                                                    for w in tr.get("wants", [])
                                                ],
                                                "gives": [
                                                    {
                                                        "item": f"minecraft:{g['item'].replace('minecraft:', '')}",
                                                        "quantity": g["quantity"]
                                                    }
                                                    for g in tr.get("gives", [])
                                                ],
                                                "max_uses": tr.get("max_uses", 9999),
                                                "trader_exp": tr.get("trader_exp", 0)
                                            }
                                            formatted_trades.append(ft)
                                        trade_data = {
                                            "tiers": [
                                                {
                                                    "total_exp_required": 0,
                                                    "groups": [
                                                        {
                                                            "num_to_select": len(formatted_trades),
                                                            "trades": formatted_trades
                                                        }
                                                    ],
                                                    "trades": formatted_trades
                                                }
                                            ]
                                        }
                                        with open(t_file, "w", encoding="utf-8") as tf:
                                            json.dump(trade_data, tf, indent=2)

                                        # Cria definição de entidade customizada
                                        os.makedirs(entities_dir, exist_ok=True)
                                        ent_data = {
                                            "format_version": "1.16.0",
                                            "minecraft:entity": {
                                                "description": {
                                                    "identifier": f"{safe_name}:npc_{clean_id}",
                                                    "runtime_identifier": "minecraft:villager_v2",
                                                    "is_spawnable": True,
                                                    "is_summonable": True
                                                },
                                                "components": {
                                                    "minecraft:nameable": {
                                                        "always_show": True,
                                                        "allow_name_tag_renaming": False
                                                    },
                                                    "minecraft:health": {"value": 100, "max": 100},
                                                    "minecraft:damage_sensor": {"triggers": [{"cause": "all", "deals_damage": False}]},
                                                    "minecraft:type_family": {"family": ["npc", "villager", "mob"]},
                                                    "minecraft:collision_box": {"width": 0.6, "height": 1.9},
                                                    "minecraft:movement": {"value": 0.0},
                                                    "minecraft:navigation.walk": {"can_path_over_water": True},
                                                    "minecraft:trade_table": {
                                                        "display_name": n_val.capitalize(),
                                                        "table": f"trading/{clean_id}_trades.json"
                                                    },
                                                    "minecraft:economy_trade_table": {
                                                        "display_name": n_val.capitalize(),
                                                        "table": f"trading/{clean_id}_trades.json",
                                                        "convert_trades_economy": False
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
                            if "generates_npc" in fname:
                                if "tellraw @a" in trans and "matches " in trans and "unless entity" not in trans:
                                    m_npc = re.search(r'matches\s+(\d+)', trans)
                                    if m_npc:
                                        day_num = int(m_npc.group(1))
                                        day_to_npc = {
                                            4: "bruce", 9: "boris", 13: "joe", 17: "tobias",
                                            21: "george", 26: "erik", 31: "adam", 38: "joakim",
                                            47: "seth", 55: "jorn"
                                        }
                                        npc_slug = day_to_npc.get(day_num)
                                        if npc_slug:
                                            trans = re.sub(r'matches\s+\d+', f'matches {day_num}.. unless entity @e[type={safe_name}:npc_{npc_slug}]', trans)
                                elif "summon" in trans and "matches " in trans:
                                    trans = re.sub(r'matches\s+(\d+)\b', r'matches \1..', trans)
                                elif "setblock" in trans and "matches 55" in trans:
                                    trans = re.sub(r'matches\s+55\b', f'matches 55.. unless entity @e[type={safe_name}:npc_jorn]', trans)
                            converted_lines.append(trans)

                    if "a_tp_spawn" in fname:
                        converted_lines.insert(0, f"execute if score #world world_init matches 0 run function {safe_name}/init_world")

                    if "generates_npc" in fname:
                        # Reordena para que tellraw execute antes de summon
                        # Isso garante que a mensagem execute antes de a entidade existir no mundo
                        reordered = []
                        pending_summon = None
                        for cline in converted_lines:
                            if "summon" in cline and "matches " in cline:
                                pending_summon = cline
                            elif "tellraw" in cline and "matches " in cline and pending_summon:
                                reordered.append(cline)
                                reordered.append(pending_summon)
                                pending_summon = None
                            else:
                                if pending_summon:
                                    reordered.append(pending_summon)
                                    pending_summon = None
                                reordered.append(cline)
                        if pending_summon:
                            reordered.append(pending_summon)
                        converted_lines = reordered

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
        custom_func_dir = os.path.join(func_dir, "custom")
        os.makedirs(custom_func_dir, exist_ok=True)

        # 4a. Funções do Motor de Ciclo Dia/Noite (Abertura/Fechamento de Portões, Display e NPCs)
        morning_lines = [
            f"# {world_name} Morning Cycle - Gate opening, day display, NPCs & chests",
            'scoreboard objectives add dayCounter dummy "Dias"',
            "scoreboard objectives add DAY_COUNTER dummy",
            "scoreboard players add DAY_COUNTER dayCounter 0",
            "execute unless score DAY_COUNTER dayCounter matches 1.. run scoreboard players set DAY_COUNTER dayCounter 1",
            "scoreboard players operation @a dayCounter = DAY_COUNTER dayCounter",
            "execute as @a run scoreboard players operation @s dayCounter = DAY_COUNTER dayCounter",
            f'tellraw @a {{"rawtext":[{{"text":"The gates are "}},{{"text":"§e§lopening"}},{{"text":"..."}}]}}',
            "setblock 286 1 -2168 redstone_block",
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
            "kill @e[type=villager,tag=!Vil]"
        ]
        morning_content = "\n".join(morning_lines) + "\n"
        for d in (world_func_dir, func_dir, custom_func_dir):
            with open(os.path.join(d, "cycle_morning.mcfunction"), "w", encoding="utf-8") as f:
                f.write(morning_content)

        # 4a-2. Função de Abertura do Portão e Inicialização do Contador Matinal (acoplada ao bloco em 276 1 -2191)
        morning_gate_lines = [
            f"# {world_name} Morning Gate Opening & Day Counter Initialization",
            'scoreboard objectives add dayCounter dummy "Dias"',
            "scoreboard objectives add DAY_COUNTER dummy",
            "scoreboard players add DAY_COUNTER dayCounter 0",
            "execute unless score DAY_COUNTER dayCounter matches 1.. run scoreboard players set DAY_COUNTER dayCounter 1",
            "scoreboard players operation @a dayCounter = DAY_COUNTER dayCounter",
            "execute as @a run scoreboard players operation @s dayCounter = DAY_COUNTER dayCounter",
            f'tellraw @a {{"rawtext":[{{"text":"The gates are "}},{{"text":"§e§lopening"}},{{"text":"..."}}]}}'
        ]
        morning_gate_content = "\n".join(morning_gate_lines) + "\n"
        for d in (world_func_dir, func_dir, custom_func_dir):
            with open(os.path.join(d, "morning_gate.mcfunction"), "w", encoding="utf-8") as f:
                f.write(morning_gate_content)

        # 4a-3. Função de Invocação de Aldeões / Newcomers na Área de Carga (acoplada ao bloco em 279 1 -2191)
        generates_npc_lines = [
            f"# {world_name} Newcomer Villagers Spawning in Loading Area",
            "",
            "# Day 4: Bruce (Farmer)",
            f'execute if score DAY_COUNTER dayCounter matches 4.. unless entity @e[name=Bruce] unless entity @e[type={safe_name}:npc_bruce] run tellraw @a {{"rawtext":[{{"text":"A"}},{{"text":"§a§l newcomer"}},{{"text":" has arrived in the"}},{{"text":"§6§l§o loading area"}},{{"text":"!"}}]}}',
            f'execute if score DAY_COUNTER dayCounter matches 4.. unless entity @e[name=Bruce] unless entity @e[type={safe_name}:npc_bruce] run summon {safe_name}:npc_bruce Bruce 264 59 -2184',
            'tag @e[name=Bruce] add Vil',
            f'tag @e[type={safe_name}:npc_bruce] add Vil',
            'tag @e[type=villager,x=264,y=59,z=-2184,r=3] add Vil',
            'tag @e[x=264,y=59,z=-2184,r=3] add Vil',
            "",
            "# Day 9: Boris (Shepherd)",
            f'execute if score DAY_COUNTER dayCounter matches 9.. unless entity @e[name=Boris] unless entity @e[type={safe_name}:npc_boris] run tellraw @a {{"rawtext":[{{"text":"A"}},{{"text":"§a§l newcomer"}},{{"text":" has arrived in the"}},{{"text":"§6§l§o loading area"}},{{"text":"!"}}]}}',
            f'execute if score DAY_COUNTER dayCounter matches 9.. unless entity @e[name=Boris] unless entity @e[type={safe_name}:npc_boris] run summon {safe_name}:npc_boris Boris 264 59 -2184',
            'tag @e[name=Boris] add Vil',
            f'tag @e[type={safe_name}:npc_boris] add Vil',
            'tag @e[type=villager,x=264,y=59,z=-2184,r=3] add Vil',
            'tag @e[x=264,y=59,z=-2184,r=3] add Vil',
            "",
            "# Day 13: Joe (Fletcher)",
            f'execute if score DAY_COUNTER dayCounter matches 13.. unless entity @e[name=Joe] unless entity @e[type={safe_name}:npc_joe] run tellraw @a {{"rawtext":[{{"text":"A"}},{{"text":"§a§l newcomer"}},{{"text":" has arrived in the"}},{{"text":"§6§l§o loading area"}},{{"text":"!"}}]}}',
            f'execute if score DAY_COUNTER dayCounter matches 13.. unless entity @e[name=Joe] unless entity @e[type={safe_name}:npc_joe] run summon {safe_name}:npc_joe Joe 264 59 -2184',
            'tag @e[name=Joe] add Vil',
            f'tag @e[type={safe_name}:npc_joe] add Vil',
            'tag @e[type=villager,x=264,y=59,z=-2184,r=3] add Vil',
            'tag @e[x=264,y=59,z=-2184,r=3] add Vil',
            "",
            "# Day 17: Tobias (Weaponsmith)",
            f'execute if score DAY_COUNTER dayCounter matches 17.. unless entity @e[name=Tobias] unless entity @e[type={safe_name}:npc_tobias] run tellraw @a {{"rawtext":[{{"text":"A"}},{{"text":"§a§l newcomer"}},{{"text":" has arrived in the"}},{{"text":"§6§l§o loading area"}},{{"text":"!"}}]}}',
            f'execute if score DAY_COUNTER dayCounter matches 17.. unless entity @e[name=Tobias] unless entity @e[type={safe_name}:npc_tobias] run summon {safe_name}:npc_tobias Tobias 264 59 -2184',
            'tag @e[name=Tobias] add Vil',
            f'tag @e[type={safe_name}:npc_tobias] add Vil',
            'tag @e[type=villager,x=264,y=59,z=-2184,r=3] add Vil',
            'tag @e[x=264,y=59,z=-2184,r=3] add Vil',
            "",
            "# Day 21: George (Butcher)",
            f'execute if score DAY_COUNTER dayCounter matches 21.. unless entity @e[name=George] unless entity @e[type={safe_name}:npc_george] run tellraw @a {{"rawtext":[{{"text":"A"}},{{"text":"§a§l newcomer"}},{{"text":" has arrived in the"}},{{"text":"§6§l§o loading area"}},{{"text":"!"}}]}}',
            f'execute if score DAY_COUNTER dayCounter matches 21.. unless entity @e[name=George] unless entity @e[type={safe_name}:npc_george] run summon {safe_name}:npc_george George 264 59 -2184',
            'tag @e[name=George] add Vil',
            f'tag @e[type={safe_name}:npc_george] add Vil',
            'tag @e[type=villager,x=264,y=59,z=-2184,r=3] add Vil',
            'tag @e[x=264,y=59,z=-2184,r=3] add Vil',
            "",
            "# Day 26: Erik (Cleric)",
            f'execute if score DAY_COUNTER dayCounter matches 26.. unless entity @e[name=Erik] unless entity @e[type={safe_name}:npc_erik] run tellraw @a {{"rawtext":[{{"text":"A"}},{{"text":"§a§l newcomer"}},{{"text":" has arrived in the"}},{{"text":"§6§l§o loading area"}},{{"text":"!"}}]}}',
            f'execute if score DAY_COUNTER dayCounter matches 26.. unless entity @e[name=Erik] unless entity @e[type={safe_name}:npc_erik] run summon {safe_name}:npc_erik Erik 264 59 -2184',
            'tag @e[name=Erik] add Vil',
            f'tag @e[type={safe_name}:npc_erik] add Vil',
            'tag @e[type=villager,x=264,y=59,z=-2184,r=3] add Vil',
            'tag @e[x=264,y=59,z=-2184,r=3] add Vil',
            "",
            "# Day 31: Adam (Mason)",
            f'execute if score DAY_COUNTER dayCounter matches 31.. unless entity @e[name=Adam] unless entity @e[type={safe_name}:npc_adam] run tellraw @a {{"rawtext":[{{"text":"A"}},{{"text":"§a§l newcomer"}},{{"text":" has arrived in the"}},{{"text":"§6§l§o loading area"}},{{"text":"!"}}]}}',
            f'execute if score DAY_COUNTER dayCounter matches 31.. unless entity @e[name=Adam] unless entity @e[type={safe_name}:npc_adam] run summon {safe_name}:npc_adam Adam 264 59 -2184',
            'tag @e[name=Adam] add Vil',
            f'tag @e[type={safe_name}:npc_adam] add Vil',
            'tag @e[type=villager,x=264,y=59,z=-2184,r=3] add Vil',
            'tag @e[x=264,y=59,z=-2184,r=3] add Vil',
            "",
            "# Day 38: Joakim (Armorer)",
            f'execute if score DAY_COUNTER dayCounter matches 38.. unless entity @e[name=Joakim] unless entity @e[type={safe_name}:npc_joakim] run tellraw @a {{"rawtext":[{{"text":"A"}},{{"text":"§a§l newcomer"}},{{"text":" has arrived in the"}},{{"text":"§6§l§o loading area"}},{{"text":"!"}}]}}',
            f'execute if score DAY_COUNTER dayCounter matches 38.. unless entity @e[name=Joakim] unless entity @e[type={safe_name}:npc_joakim] run summon {safe_name}:npc_joakim Joakim 264 59 -2184',
            'tag @e[name=Joakim] add Vil',
            f'tag @e[type={safe_name}:npc_joakim] add Vil',
            'tag @e[type=villager,x=264,y=59,z=-2184,r=3] add Vil',
            'tag @e[x=264,y=59,z=-2184,r=3] add Vil',
            "",
            "# Day 47: Seth (Librarian)",
            f'execute if score DAY_COUNTER dayCounter matches 47.. unless entity @e[name=Seth] unless entity @e[type={safe_name}:npc_seth] run tellraw @a {{"rawtext":[{{"text":"A"}},{{"text":"§a§l newcomer"}},{{"text":" has arrived in the"}},{{"text":"§6§l§o loading area"}},{{"text":"!"}}]}}',
            f'execute if score DAY_COUNTER dayCounter matches 47.. unless entity @e[name=Seth] unless entity @e[type={safe_name}:npc_seth] run summon {safe_name}:npc_seth Seth 264 59 -2184',
            'tag @e[name=Seth] add Vil',
            f'tag @e[type={safe_name}:npc_seth] add Vil',
            'tag @e[type=villager,x=264,y=59,z=-2184,r=3] add Vil',
            'tag @e[x=264,y=59,z=-2184,r=3] add Vil',
            "",
            "# Day 55: Jorn (Cartographer) & Redstone Trigger",
            f'execute if score DAY_COUNTER dayCounter matches 55.. unless entity @e[name=Jorn] unless entity @e[type={safe_name}:npc_jorn] run tellraw @a {{"rawtext":[{{"text":"A"}},{{"text":"§a§l newcomer"}},{{"text":" has arrived in the"}},{{"text":"§6§l§o loading area"}},{{"text":"!"}}]}}',
            f'execute if score DAY_COUNTER dayCounter matches 55.. unless entity @e[name=Jorn] unless entity @e[type={safe_name}:npc_jorn] run summon {safe_name}:npc_jorn Jorn 264 59 -2184',
            'tag @e[name=Jorn] add Vil',
            f'tag @e[type={safe_name}:npc_jorn] add Vil',
            'tag @e[type=villager,x=264,y=59,z=-2184,r=3] add Vil',
            'tag @e[x=264,y=59,z=-2184,r=3] add Vil',
            'execute if score DAY_COUNTER dayCounter matches 55.. unless entity @e[name=Jorn] run setblock 279 1 -2177 redstone_block'
        ]
        generates_npc_content = "\n".join(generates_npc_lines) + "\n"
        for d in (world_func_dir, func_dir, custom_func_dir):
            with open(os.path.join(d, "generates_npc.mcfunction"), "w", encoding="utf-8") as f:
                f.write(generates_npc_content)

        # 4a-4. Funções de Exibição de Dia no Chat e Título (acopladas a 280 1 -2192 e 279 1 -2192)
        day_display_lines = [
            f"# {world_name} Day Counter Chat Announcement",
            'scoreboard objectives add dayCounter dummy "Dias"',
            "scoreboard objectives add DAY_COUNTER dummy",
            "scoreboard players add DAY_COUNTER dayCounter 0",
            "execute unless score DAY_COUNTER dayCounter matches 1.. run scoreboard players set DAY_COUNTER dayCounter 1",
            "scoreboard players operation @a dayCounter = DAY_COUNTER dayCounter",
            "execute as @a run scoreboard players operation @s dayCounter = DAY_COUNTER dayCounter",
            'tellraw @a {"rawtext":[{"text":"§7Day "},{"score":{"name":"DAY_COUNTER","objective":"dayCounter"}}]}'
        ]
        day_display_content = "\n".join(day_display_lines) + "\n"
        for d in (world_func_dir, func_dir, custom_func_dir):
            with open(os.path.join(d, "day_display.mcfunction"), "w", encoding="utf-8") as f:
                f.write(day_display_content)

        day_title_lines = [
            f"# {world_name} Day Counter Title Announcement",
            'scoreboard objectives add dayCounter dummy "Dias"',
            "scoreboard objectives add DAY_COUNTER dummy",
            "scoreboard players add DAY_COUNTER dayCounter 0",
            "execute unless score DAY_COUNTER dayCounter matches 1.. run scoreboard players set DAY_COUNTER dayCounter 1",
            "scoreboard players operation @a dayCounter = DAY_COUNTER dayCounter",
            "execute as @a run scoreboard players operation @s dayCounter = DAY_COUNTER dayCounter",
            'titleraw @a title {"rawtext":[{"text":"§7Day "},{"score":{"name":"DAY_COUNTER","objective":"dayCounter"}}]}'
        ]
        day_title_content = "\n".join(day_title_lines) + "\n"
        for d in (world_func_dir, func_dir, custom_func_dir):
            with open(os.path.join(d, "day_title.mcfunction"), "w", encoding="utf-8") as f:
                f.write(day_title_content)

        night_lines = [
            f"# {world_name} Night Cycle - Gate closing & day counter increment",
            'scoreboard objectives add dayCounter dummy "Dias"',
            "scoreboard objectives add DAY_COUNTER dummy",
            "scoreboard players add DAY_COUNTER dayCounter 0",
            "execute unless score DAY_COUNTER dayCounter matches 1.. run scoreboard players set DAY_COUNTER dayCounter 1",
            "scoreboard players add DAY_COUNTER dayCounter 1",
            "scoreboard players operation @a dayCounter = DAY_COUNTER dayCounter",
            "execute as @a run scoreboard players operation @s dayCounter = DAY_COUNTER dayCounter",
            "setblock 287 1 -2168 redstone_block",
            "setblock 164 44 -2210 redstone_block",
            "playsound entity.illusioner.prepare_mirror @a 173 64 -2148 10.0 1 0.03",
            "playsound entity.illusioner.prepare_mirror @a 220 64 -2195 10.0 1 0.03",
            "playsound entity.illusioner.prepare_mirror @a 220 64 -2100 10.0 1 0.03",
            "playsound entity.illusioner.prepare_mirror @a 268 64 -2148 10.0 1 0.03",
            "playsound mob.evocation_illager.prepare_summon @a ~ ~ ~ 1.0 1 0.03",
            "playsound mob.ghast.scream @a ~ ~ ~ 10000"
        ]
        night_content = "\n".join(night_lines) + "\n"
        for d in (world_func_dir, func_dir, custom_func_dir):
            with open(os.path.join(d, "cycle_night.mcfunction"), "w", encoding="utf-8") as f:
                f.write(night_content)

        # 4b. Inicialização do Mundo e Ticking Areas Enxutas (<100 chunks)
        init_lines = [
            f"# {world_name} Initialization for Bedrock 1.21+",
            "gamerule commandblockoutput false",
            "gamerule sendcommandfeedback false",
            "gamerule doimmediaterespawn true",
            "gamerule domobspawning false",
            "gamerule dodaylightcycle true",
            "# Ticking areas permanentes cobrindo centro, portoes, clareira, templates e relogio (76 chunks)",
            "tickingarea add 170 50 -2205 275 110 -2095 maze_glade_center",
            "tickingarea add 276 0 -2205 310 50 -2060 maze_templates_clock",
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
            f"function {safe_name}/cycle_morning",
            "scoreboard players set #world world_init 1",
            f'tellraw @a {{"rawtext":[{{"text":"§a[{world_name}]§r World and mechanics successfully initialized for Bedrock 1.21+!"}}]}}'
        ]
        init_content = "\n".join(init_lines) + "\n"
        for d in (world_func_dir, func_dir, custom_func_dir):
            with open(os.path.join(d, "init_world.mcfunction"), "w", encoding="utf-8") as f:
                f.write(init_content)

        # 4c. Manipulador de Entrada de Jogador (Boas-vindas e Exibição de Dia)
        player_join_lines = [
            f"# {world_name} Player Join Handler",
            "tag @s add joined",
            'scoreboard objectives add dayCounter dummy "Dias"',
            "scoreboard objectives add DAY_COUNTER dummy",
            "scoreboard objectives add world_init dummy",
            "scoreboard players add #world world_init 0",
            "scoreboard players add DAY_COUNTER dayCounter 0",
            "execute unless score DAY_COUNTER dayCounter matches 1.. run scoreboard players set DAY_COUNTER dayCounter 1",
            "scoreboard players add @s dayCounter 0",
            "scoreboard players operation @s dayCounter = DAY_COUNTER dayCounter",
            f"execute if score #world world_init matches 0 run function {safe_name}/init_world",
            'titleraw @s title {"rawtext":[{"text":"§7Day "},{"score":{"name":"DAY_COUNTER","objective":"dayCounter"}}]}',
            f'tellraw @s {{"rawtext":[{{"text":"§a[{world_name}]§r Welcome to the Maze! Day counter and world mechanics are active."}}]}}'
        ]
        player_join_content = "\n".join(player_join_lines) + "\n"
        for d in (world_func_dir, func_dir, custom_func_dir):
            with open(os.path.join(d, "player_join.mcfunction"), "w", encoding="utf-8") as f:
                f.write(player_join_content)

        # 4d. Driver de Ticks Contínuo (Daylight Detector State Machine + Sincronização)
        tick_lines = [
            f"# 1. Ticking areas permanentes",
            f"scoreboard objectives add areas_added dummy",
            f"scoreboard players add #world areas_added 0",
            f"execute if score #world areas_added matches 0 run tickingarea add 170 50 -2205 275 110 -2095 maze_glade_center",
            f"execute if score #world areas_added matches 0 run tickingarea add 276 0 -2205 310 50 -2060 maze_templates_clock",
            f"scoreboard players set #world areas_added 1",
            f"# 2. Inicializacao automatica do mundo e do contador ao entrar o primeiro jogador",
            f"scoreboard objectives add world_init dummy",
            f"scoreboard players add #world world_init 0",
            f"execute unless score #world world_init matches 0.. run scoreboard players set #world world_init 0",
            f"execute if entity @a if score #world world_init matches 0 run function {safe_name}/init_world",
            f"execute if entity @a if score #world world_init matches 0 run function init_world",
            f"# 3. Sincronizacao continua do contador de dias e garantia de DAY_COUNTER >= 1",
            'scoreboard objectives add dayCounter dummy "Dias"',
            "scoreboard objectives add DAY_COUNTER dummy",
            "scoreboard players add DAY_COUNTER dayCounter 0",
            "execute unless score DAY_COUNTER dayCounter matches 1.. run scoreboard players set DAY_COUNTER dayCounter 1",
            "scoreboard players add @a dayCounter 0",
            "scoreboard players operation @a dayCounter = DAY_COUNTER dayCounter",
            "execute as @a run scoreboard players operation @s dayCounter = DAY_COUNTER dayCounter",
            f"execute as @a[tag=!joined] run function {safe_name}/player_join",
            f"# 4. Manutencao dos detectores de ciclo dia/noite",
            "execute if score #world world_init matches 1 unless block 286 100 -2168 daylight_detector run setblock 286 100 -2168 daylight_detector",
            "execute if score #world world_init matches 1 unless block 287 100 -2168 daylight_detector_inverted run setblock 287 100 -2168 daylight_detector_inverted",
            f"# 5. Detector de noite (pôr do sol / /time set 13000+ / celestial darkness)",
            'execute if score #world is_night matches 0 if block 286 100 -2168 daylight_detector ["redstone_signal"=0] run scoreboard players set #world is_night 1',
            f'execute if score #world is_night matches 1 if score #world cycle_ran matches 0 run function {safe_name}/cycle_night',
            'execute if score #world is_night matches 1 if score #world cycle_ran matches 0 run scoreboard players set #world cycle_ran 1',
            f"# 6. Detector de dia (amanhecer / sono / /time set 1000 / celestial light)",
            'execute if score #world is_night matches 1 unless block 286 100 -2168 daylight_detector ["redstone_signal"=0] run scoreboard players set #world is_night 0',
            f'execute if score #world is_night matches 0 if score #world cycle_ran matches 1 run function {safe_name}/cycle_morning',
            'execute if score #world is_night matches 0 if score #world cycle_ran matches 1 run scoreboard players set #world cycle_ran 0'
        ]
        tick_content = "\n".join(tick_lines) + "\n"
        for d in (func_dir, world_func_dir, custom_func_dir):
            with open(os.path.join(d, "tick.mcfunction"), "w", encoding="utf-8") as f:
                f.write(tick_content)

        # Garante que tick.json legado na raiz do BP seja removido
        stale_tick = os.path.join(target_bp_dir, "tick.json")
        if os.path.exists(stale_tick):
            os.remove(stale_tick)

        # tick.json configurado na pasta functions/ (e subpastas de funcoes)
        tick_json_data = {"values": ["tick"]}
        for d in (func_dir, world_func_dir, custom_func_dir):
            with open(os.path.join(d, "tick.json"), "w", encoding="utf-8") as f:
                json.dump(tick_json_data, f, indent=2)

        return {
            "header_uuid": bp_header_uuid,
            "module_uuid": bp_module_uuid,
            "functions_count": converted_funcs,
            "known_npcs": list(known_npcs)
        }

