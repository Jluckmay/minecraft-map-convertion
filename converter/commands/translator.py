#!/usr/bin/env python3
"""
Módulo de Parsing e Tradução Estruturada de Comandos Java -> Bedrock (Seções 8, 11, 12, 39).
Autor: João Lucas Mayrinck
"""

import re
import json
from typing import Set, Tuple, Optional, Dict, Any

COLOR_MAP = {
    "black": "§0", "dark_blue": "§1", "dark_green": "§2", "dark_aqua": "§3",
    "dark_red": "§4", "dark_purple": "§5", "gold": "§6", "gray": "§7",
    "dark_gray": "§8", "blue": "§9", "green": "§a", "aqua": "§b",
    "red": "§c", "light_purple": "§d", "yellow": "§e", "white": "§f"
}

SOUND_MAP = {
    "minecraft:entity.player.levelup": "random.levelup",
    "entity.player.levelup": "random.levelup",
    "minecraft:block.chest.open": "random.chestopen",
    "block.chest.open": "random.chestopen",
    "minecraft:block.chest.close": "random.chestclosed",
    "block.chest.close": "random.chestclosed",
    "minecraft:entity.experience_orb.pickup": "random.orb",
    "entity.experience_orb.pickup": "random.orb",
    "minecraft:block.portal.trigger": "portal.trigger",
    "block.portal.trigger": "portal.trigger",
    "minecraft:block.portal.travel": "portal.travel",
    "block.portal.travel": "portal.travel",
    "minecraft:block.end_portal.spawn": "portal.travel",
    "block.end_portal.spawn": "portal.travel",
    "minecraft:entity.generic.explode": "random.explode",
    "entity.generic.explode": "random.explode",
    "minecraft:entity.wither.spawn": "mob.wither.spawn",
    "entity.wither.spawn": "mob.wither.spawn",
    "minecraft:entity.wither.death": "mob.wither.death",
    "entity.wither.death": "mob.wither.death",
    "minecraft:entity.zombie.ambient": "mob.zombie.say",
    "entity.zombie.ambient": "mob.zombie.say"
}

class CommandTranslator:
    """Tradutor estruturado de comandos Minecraft Java 1.16.5 para Bedrock 1.20+."""

    @classmethod
    def translate_selector(cls, sel: str) -> str:
        """Converte seletores e argumentos Java para sintaxe Bedrock equivalente."""
        # distance=..X -> r=X
        sel = re.sub(r'distance=\.\.([0-9.]+)', r'r=\1', sel)
        # distance=X..Y -> rm=X,r=Y
        sel = re.sub(r'distance=([0-9.]+)\.\.([0-9.]+)', r'rm=\1,r=\2', sel)
        # distance=X.. -> rm=X
        sel = re.sub(r'distance=([0-9.]+)\.\.', r'rm=\1', sel)
        # limit=1,sort=nearest -> c=1
        sel = re.sub(r'limit=([0-9]+)', r'c=\1', sel)
        sel = re.sub(r',?sort=(?:nearest|arbitrary)', '', sel)
        # remove minecraft: de type=
        sel = re.sub(r'type=minecraft:', 'type=', sel)
        return sel

    @classmethod
    def convert_tellraw_json(cls, json_str: str) -> str:
        """Converte JSON Java text/tellraw/title para formato nativo Bedrock rawtext."""
        try:
            parsed = json.loads(json_str)
            text_acc = ""
            def extract(node):
                nonlocal text_acc
                if isinstance(node, str):
                    text_acc += node
                elif isinstance(node, dict):
                    color = node.get("color", "")
                    prefix = COLOR_MAP.get(color, "")
                    text = node.get("text", "")
                    text_acc += f"{prefix}{text}"
                    if "extra" in node:
                        extract(node["extra"])
                elif isinstance(node, list):
                    for item in node:
                        extract(item)
            extract(parsed)
            if not text_acc and isinstance(parsed, dict) and "text" in parsed:
                text_acc = parsed["text"]
            return json.dumps({"rawtext": [{"text": text_acc}]}, ensure_ascii=False)
        except Exception:
            return json.dumps({"rawtext": [{"text": json_str}]}, ensure_ascii=False)

    @classmethod
    def translate(cls, cmd: str, known_npcs: Optional[Set[str]] = None, world_safe_name: str = "custom") -> str:
        """Traduz um comando de Java para Bedrock preservando a lógica e semântica."""
        s = cmd.strip()
        if not s:
            return ""

        # Remove barra inicial (obrigatório em .mcfunction e command blocks Bedrock)
        if s.startswith('/'):
            s = s[1:].strip()

        # Suporte recursivo a execute ... run <subcommand>
        if s.startswith("execute ") and " run " in s:
            exec_prefix, run_cmd = s.split(" run ", 1)
            exec_prefix = cls.translate_selector(exec_prefix)
            # Normalização de namespace em chamadas de função
            exec_prefix = re.sub(r'\bfunction\s+([a-zA-Z0-9._-]+):([a-zA-Z0-9._/-]+)', r'function \1/\2', exec_prefix)
            trans_inner = cls.translate(run_cmd, known_npcs, world_safe_name)
            return f"{exec_prefix} run {trans_inner}"

        # 1. forceload -> tickingarea funcional
        if s.startswith("forceload add ") or s.startswith("forceload remove "):
            parts = s.split()
            if len(parts) in (4, 6) and parts[1] == "add":
                x1, z1 = int(parts[2]), int(parts[3])
                x2, z2 = (int(parts[4]), int(parts[5])) if len(parts) == 6 else (x1, z1)
                bx1, bz1 = min(x1, x2) * 16, min(z1, z2) * 16
                bx2, bz2 = max(x1, x2) * 16 + 15, max(z1, z2) * 16 + 15
                area_name = f"fl_{x1}_{z1}_{x2}_{z2}".replace("-", "m")
                return f"tickingarea add {bx1} 0 {bz1} {bx2} 319 {bz2} {area_name}"
            if len(parts) in (4, 6) and parts[1] == "remove":
                x1, z1 = int(parts[2]), int(parts[3])
                x2, z2 = (int(parts[4]), int(parts[5])) if len(parts) == 6 else (x1, z1)
                area_name = f"fl_{x1}_{z1}_{x2}_{z2}".replace("-", "m")
                return f"tickingarea remove {area_name}"
            return f"# [Bedrock Conversion] {s}"

        # 2. data merge block {Delay:0}
        if s.startswith("data merge block ") and "Delay:0" in s:
            match = re.match(r"data merge block (-?\d+) (-?\d+) (-?\d+) .*", s)
            if match:
                x, y, z = match.groups()
                return f"setblock {x} {y} {z} mob_spawner"
            return f"# [Bedrock Conversion] {s}"

        # 3. Tradução de seletores
        s = cls.translate_selector(s)

        # 4. Chamadas de função: namespace:nome -> namespace/nome
        s = re.sub(r'\bfunction\s+([a-zA-Z0-9._-]+):([a-zA-Z0-9._/-]+)', r'function \1/\2', s)

        # 5. tellraw e title
        m_tr = re.match(r'^(tellraw\s+@[aeprs](?:\[[^\]]*\])?)\s+(\{.*\})$', s)
        if m_tr:
            prefix, payload = m_tr.group(1), m_tr.group(2)
            return f"{prefix} {cls.convert_tellraw_json(payload)}"

        m_ti = re.match(r'^(title\s+@[aeprs](?:\[[^\]]*\])?\s+(?:title|subtitle|actionbar))\s+(\{.*\})$', s)
        if m_ti:
            prefix, payload = m_ti.group(1), m_ti.group(2)
            return f"{prefix} {cls.convert_tellraw_json(payload)}"

        # 6. playsound
        if s.startswith("playsound "):
            parts = s.split()
            if len(parts) >= 3:
                snd = parts[1]
                snd_bedrock = SOUND_MAP.get(snd, snd.replace("minecraft:", ""))
                idx = 2
                if idx < len(parts) and parts[idx] in ("master", "ambient", "weather", "record", "hostile", "neutral", "player", "voice"):
                    idx += 1
                rest = parts[idx:]
                return f"playsound {snd_bedrock} {' '.join(rest)}".strip()

        # 7. effect give
        if s.startswith("effect give "):
            rem = s[len("effect give "):].strip()
            if "glowing" in rem:
                return f"# [Bedrock Conversion] effect glowing não suportado no Bedrock: {s}"
            return f"effect {rem}"

        # 8. give com livros/NBT complexo
        if s.startswith("give ") and "written_book{" in s:
            parts = s.split()
            target = parts[1] if len(parts) > 1 else "@s"
            return f"give {target} written_book 1"

        # 9. summon com NPCs e tags
        if known_npcs:
            for npc in known_npcs:
                npc_tag = f":npc_{npc}"
                if npc_tag in s and not s.startswith("execute unless entity"):
                    entity_type = f"{world_safe_name}:npc_{npc}"
                    return f"execute unless entity @e[type={entity_type}] run {s}"

        m_sm = re.search(r'^(.*?\bsummon\s+)([a-zA-Z0-9:_]+)\s+([~^0-9.-]+)\s+([~^0-9.-]+)\s+([~^0-9.-]+)(\s*\{.*\}|\s*)$', s)
        if m_sm:
            prefix, ent_type, x, y, z, nbt_part = m_sm.groups()
            clean_type = ent_type.replace("minecraft:", "")
            if nbt_part and nbt_part.strip():
                if "npc_" in clean_type:
                    return f"{prefix}{clean_type} {x} {y} {z}"
                name_match = re.search(r'CustomName\s*:\s*\'(?:\{.*?"text"\s*:\s*"([^"]+)".*?\}|"([^"]+)")\'', nbt_part)
                if name_match:
                    found_name = name_match.group(1) or name_match.group(2)
                    return f"{prefix}{clean_type} {x} {y} {z} \"{found_name}\""
                return f"{prefix}{clean_type} {x} {y} {z}"
            return f"{prefix}{clean_type} {x} {y} {z}"

        # 10. setblock / fill - limpeza de namespace
        if s.startswith("setblock ") or s.startswith("fill "):
            s = re.sub(r'\bminecraft:', '', s)

        # 11. gamerule
        if s.startswith("gamerule "):
            parts = s.split()
            if len(parts) == 3:
                rule, val = parts[1].lower(), parts[2].lower()
                return f"gamerule {rule} {val}"

        return s

