#!/usr/bin/env python3
"""
Testes unitários para as correções das 3 mecânicas:
1. Drops de esmeralda nas tabelas de saque de entidades
2. Tradução de summon de NPCs e inicialização de DAY_COUNTER
3. Definições de som do portão (illusioner) em sound_definitions.json
Autor: João Lucas Mayrinck
"""

import os
import sys
import json
import unittest
import tempfile
import shutil

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from converter.commands.translator import CommandTranslator
from converter.behavior_pack.bp_generator import BehaviorPackGenerator
from converter.resource_pack.rp_generator import ResourcePackGenerator


class TestMechanicsFixes(unittest.TestCase):

    def test_loot_table_converter(self):
        """Testa se a conversão de loot tables preserva o pool de esmeraldas e funções."""
        java_loot = {
            "pools": [
                {
                    "rolls": 1,
                    "entries": [
                        {
                            "type": "minecraft:item",
                            "name": "minecraft:rotten_flesh",
                            "weight": 1,
                            "functions": [
                                {
                                    "function": "minecraft:set_count",
                                    "count": {"min": 0, "max": 2}
                                }
                            ]
                        }
                    ]
                },
                {
                    "rolls": 1,
                    "entries": [
                        {
                            "type": "minecraft:item",
                            "name": "minecraft:emerald",
                            "weight": 1,
                            "functions": [
                                {
                                    "function": "minecraft:set_count",
                                    "count": {"min": 1, "max": 1}
                                },
                                {
                                    "function": "minecraft:looting_enchant",
                                    "count": {"min": 0, "max": 1}
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        b_loot = BehaviorPackGenerator.convert_loot_table(java_loot)
        self.assertEqual(len(b_loot["pools"]), 2)
        emerald_pool = b_loot["pools"][1]
        entry = emerald_pool["entries"][0]
        self.assertEqual(entry["name"], "minecraft:emerald")
        self.assertEqual(len(entry["functions"]), 2)
        func_names = [f["function"] for f in entry["functions"]]
        self.assertIn("set_count", func_names)
        self.assertIn("looting_enchant", func_names)

    def test_npc_summon_translation(self):
        """Testa a tradução do comando /summon villager com CustomName para entidade customizada Bedrock."""
        cmd = 'execute if score DAY_COUNTER dayCounter matches 4 run summon minecraft:villager 264 59 -2184 {CustomName:\'{"text":"Bruce"}\'}'
        translated = CommandTranslator.translate(cmd, known_npcs={"bruce"}, world_safe_name="mazescapist")
        expected = "execute if score DAY_COUNTER dayCounter matches 4 unless entity @e[type=mazescapist:npc_bruce] run summon mazescapist:npc_bruce 264 59 -2184"
        self.assertEqual(translated, expected)

    def test_gate_sound_translation(self):
        """Testa a tradução dos comandos de som do portão (/playsound)."""
        cmd1 = "/playsound minecraft:entity.illusioner.prepare_mirror master @a 173 64 -2148 0.7 1 0.03"
        t1 = CommandTranslator.translate(cmd1)
        self.assertEqual(t1, "playsound entity.illusioner.prepare_mirror @a 173 64 -2148 0.7 1 0.03")

        cmd2 = "/execute positioned as @a[distance=..180] run playsound minecraft:entity.illusioner.mirror_move master @a ~ ~ ~"
        t2 = CommandTranslator.translate(cmd2)
        self.assertEqual(t2, "execute positioned as @a[r=180] run playsound entity.illusioner.mirror_move @a ~ ~ ~")

    def test_sound_definitions_generation(self):
        """Testa a geração de sound_definitions.json com os eventos de som do portão."""
        tmp_dir = tempfile.mkdtemp()
        try:
            dummy_source_rp = os.path.join(tmp_dir, "source_rp")
            target_rp = os.path.join(tmp_dir, "target_rp")
            os.makedirs(dummy_source_rp, exist_ok=True)
            ResourcePackGenerator.generate(dummy_source_rp, target_rp, "TestWorld", "testworld")

            sound_def_file = os.path.join(target_rp, "sounds", "sound_definitions.json")
            self.assertTrue(os.path.exists(sound_def_file))
            with open(sound_def_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            defs = data.get("sound_definitions", {})
            self.assertIn("entity.illusioner.mirror_move", defs)
            self.assertIn("entity.illusioner.prepare_mirror", defs)
            self.assertIn("entity.illusioner.prepare_blind", defs)
            self.assertIn("entity.ghast.scream", defs)
            self.assertIn("entity.wither_skeleton.death", defs)
        finally:
            shutil.rmtree(tmp_dir)

    def test_init_world_day_counter(self):
        """Testa se init_world.mcfunction inicializa o objetivo dayCounter e o jogador fake DAY_COUNTER."""
        tmp_dir = tempfile.mkdtemp()
        try:
            target_bp = os.path.join(tmp_dir, "target_bp")
            BehaviorPackGenerator.generate("", target_bp, "TestWorld", "testworld", "dummy-rp-uuid")

            init_func = os.path.join(target_bp, "functions", "testworld", "init_world.mcfunction")
            self.assertTrue(os.path.exists(init_func))
            with open(init_func, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn("scoreboard objectives add dayCounter dummy", content)
            self.assertIn("scoreboard players add DAY_COUNTER dayCounter 0", content)
            self.assertIn("setblock 286 100 -2168 daylight_detector", content)
        finally:
            shutil.rmtree(tmp_dir)

    def test_tellraw_score_rawtext(self):
        """Testa se convert_tellraw_json preserva o nome de fake players (ex: DAY_COUNTER) no rawtext do Bedrock."""
        payload = json.dumps([
            "",
            {"text": "Day ", "color": "gray"},
            {"score": {"name": "DAY_COUNTER", "objective": "dayCounter"}}
        ])
        converted = CommandTranslator.convert_tellraw_json(payload)
        data = json.loads(converted)
        rawtext = data.get("rawtext", [])
        self.assertEqual(len(rawtext), 2)
        score_elem = rawtext[1]
        self.assertIn("score", score_elem)
        self.assertEqual(score_elem["score"]["name"], "DAY_COUNTER")
        self.assertEqual(score_elem["score"]["objective"], "dayCounter")

    def test_day_cycle_functions_generation(self):
        """Testa se cycle_morning.mcfunction e cycle_night.mcfunction são geradas com os comandos corretos."""
        tmp_dir = tempfile.mkdtemp()
        try:
            target_bp = os.path.join(tmp_dir, "target_bp")
            BehaviorPackGenerator.generate("", target_bp, "MazeRunner", "mazerunner", "dummy-rp-uuid")

            # cycle_morning
            m_func = os.path.join(target_bp, "functions", "mazerunner", "cycle_morning.mcfunction")
            self.assertTrue(os.path.exists(m_func))
            with open(m_func, "r", encoding="utf-8") as f:
                m_content = f.read()
            self.assertIn("setblock 286 1 -2168 redstone_block", m_content)
            self.assertIn("titleraw @a title", m_content)
            self.assertIn("tellraw @a", m_content)
            self.assertIn("function custom/generates_npc", m_content)
            self.assertIn("function custom/generates_chest", m_content)

            # cycle_night
            n_func = os.path.join(target_bp, "functions", "mazerunner", "cycle_night.mcfunction")
            self.assertTrue(os.path.exists(n_func))
            with open(n_func, "r", encoding="utf-8") as f:
                n_content = f.read()
            self.assertIn("setblock 287 1 -2168 redstone_block", n_content)
            self.assertIn("scoreboard players add DAY_COUNTER dayCounter 1", n_content)
            self.assertIn("scoreboard players operation @a dayCounter = DAY_COUNTER dayCounter", n_content)

            # tick.mcfunction
            tick_func = os.path.join(target_bp, "functions", "tick.mcfunction")
            self.assertTrue(os.path.exists(tick_func))
            with open(tick_func, "r", encoding="utf-8") as f:
                t_content = f.read()
            self.assertIn("daylight_detector", t_content)
            self.assertIn("cycle_night", t_content)
            self.assertIn("cycle_morning", t_content)
            self.assertIn("scoreboard players add #world mazerunner_initialized 0", t_content)
            self.assertIn("player_join", t_content)

            # player_join.mcfunction
            join_func = os.path.join(target_bp, "functions", "mazerunner", "player_join.mcfunction")
            self.assertTrue(os.path.exists(join_func))
            with open(join_func, "r", encoding="utf-8") as f:
                j_content = f.read()
            self.assertIn("tag @s add joined", j_content)
            self.assertIn("titleraw @s title", j_content)
        finally:
            shutil.rmtree(tmp_dir)

    def test_ticking_areas_budget(self):
        """Testa se as ticking areas permanentes respeitam o teto de 100 chunks do Bedrock."""
        tmp_dir = tempfile.mkdtemp()
        try:
            target_bp = os.path.join(tmp_dir, "target_bp")
            BehaviorPackGenerator.generate("", target_bp, "MazeRunner", "mazerunner", "dummy-rp-uuid")

            init_func = os.path.join(target_bp, "functions", "mazerunner", "init_world.mcfunction")
            self.assertTrue(os.path.exists(init_func))
            with open(init_func, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Extrai coordenadas de cada tickingarea add
            total_chunks = 0
            ta_count = 0
            for line in lines:
                if line.strip().startswith("tickingarea add"):
                    parts = line.strip().split()
                    x1, z1, x2, z2 = int(parts[2]), int(parts[4]), int(parts[5]), int(parts[7])
                    cx1, cx2 = min(x1, x2) // 16, max(x1, x2) // 16
                    cz1, cz2 = min(z1, z2) // 16, max(z1, z2) // 16
                    chunks = (cx2 - cx1 + 1) * (cz2 - cz1 + 1)
                    total_chunks += chunks
                    ta_count += 1

            self.assertLessEqual(ta_count, 10, "Bedrock permite no máximo 10 ticking areas.")
            self.assertLessEqual(total_chunks, 100, f"Total de chunks ({total_chunks}) deve ser <= 100.")
        finally:
            shutil.rmtree(tmp_dir)


if __name__ == "__main__":
    unittest.main()

