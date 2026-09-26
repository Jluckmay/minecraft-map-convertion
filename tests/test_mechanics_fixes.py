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
import io
import shutil
import nbtlib

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from converter.commands.translator import CommandTranslator
from converter.behavior_pack.bp_generator import BehaviorPackGenerator
from converter.resource_pack.rp_generator import ResourcePackGenerator
from converter.world.leveldb_manager import BedrockLevelDBManager


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
        """Testa a tradução do comando /summon villager com CustomName para entidade villager_v2 nativa Bedrock com evento e nome."""
        cmd = 'execute if score DAY_COUNTER dayCounter matches 4 run summon minecraft:villager 264 59 -2184 {CustomName:\'{"text":"Bruce"}\'}'
        translated = CommandTranslator.translate(cmd, known_npcs={"bruce"}, world_safe_name="mazescapist")
        expected = 'execute if score DAY_COUNTER dayCounter matches 4 unless entity @e[name="Bruce"] run summon villager_v2 264 59 -2184 0 0 mazescapist:spawn_bruce "Bruce"'
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

            # Render controllers para NPCs
            rc_file = os.path.join(target_rp, "render_controllers", "npc_villager.render_controllers.json")
            self.assertTrue(os.path.exists(rc_file))
            with open(rc_file, "r", encoding="utf-8") as f:
                rc_data = json.load(f)
            self.assertIn("controller.render.villager_v2", rc_data.get("render_controllers", {}))
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
            self.assertIn("scoreboard objectives add world_init dummy", content)
            self.assertIn("scoreboard players set #world world_init 1", content)
            self.assertIn("setblock 286 100 -2168 daylight_detector", content)
            self.assertIn("setblock 286 1 -2168 redstone_block", content)
            self.assertNotIn("cycle_morning", content)
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

    def test_day_counter_reset_translation(self):
        """Testa se comandos de reset do fakeplayer DAY_COUNTER são traduzidos para set 1."""
        cmd1 = "/scoreboard players reset DAY_COUNTER dayCounter"
        cmd2 = "scoreboard players reset DAY_COUNTER"
        self.assertEqual(CommandTranslator.translate(cmd1), "scoreboard players set DAY_COUNTER dayCounter 1")
        self.assertEqual(CommandTranslator.translate(cmd2), "scoreboard players set DAY_COUNTER dayCounter 1")

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
            self.assertNotIn('"closing"', n_content)

            # morning_gate
            mg_func = os.path.join(target_bp, "functions", "mazerunner", "morning_gate.mcfunction")
            self.assertTrue(os.path.exists(mg_func))
            with open(mg_func, "r", encoding="utf-8") as f:
                mg_content = f.read()
            self.assertIn("The gates are ", mg_content)
            self.assertIn("§e§lopening", mg_content)
            self.assertIn("execute unless score DAY_COUNTER dayCounter matches 1.. run scoreboard players set DAY_COUNTER dayCounter 1", mg_content)

            # generates_npc
            gn_func = os.path.join(target_bp, "functions", "mazerunner", "generates_npc.mcfunction")
            self.assertTrue(os.path.exists(gn_func))
            with open(gn_func, "r", encoding="utf-8") as f:
                gn_content = f.read()
            self.assertIn('summon villager_v2 264 59 -2184 0 0 mazerunner:spawn_bruce "Bruce"', gn_content)
            self.assertIn("tag @e[name=Bruce] add Vil", gn_content)
            self.assertIn("tag @e[name=Boris] add Vil", gn_content)
            self.assertIn("tag @e[name=Jorn] add Vil", gn_content)
            self.assertIn("tag @e[type=villager,x=264,y=59,z=-2184,r=3] add Vil", gn_content)
            self.assertIn("tag @e[type=villager_v2,x=264,y=59,z=-2184,r=3] add Vil", gn_content)

            # day_display
            dd_func = os.path.join(target_bp, "functions", "mazerunner", "day_display.mcfunction")
            self.assertTrue(os.path.exists(dd_func))
            with open(dd_func, "r", encoding="utf-8") as f:
                dd_content = f.read()
            self.assertIn("execute unless score DAY_COUNTER dayCounter matches 1.. run scoreboard players set DAY_COUNTER dayCounter 1", dd_content)
            self.assertIn('tellraw @a {"rawtext":[{"text":"§7Day "},{"score":{"name":"DAY_COUNTER","objective":"dayCounter"}}]}', dd_content)

            # day_title
            dt_func = os.path.join(target_bp, "functions", "mazerunner", "day_title.mcfunction")
            self.assertTrue(os.path.exists(dt_func))
            with open(dt_func, "r", encoding="utf-8") as f:
                dt_content = f.read()
            self.assertIn("execute unless score DAY_COUNTER dayCounter matches 1.. run scoreboard players set DAY_COUNTER dayCounter 1", dt_content)
            self.assertIn('titleraw @a title {"rawtext":[{"text":"§7Day "},{"score":{"name":"DAY_COUNTER","objective":"dayCounter"}}]}', dt_content)

            # tick.mcfunction
            tick_func = os.path.join(target_bp, "functions", "tick.mcfunction")
            self.assertTrue(os.path.exists(tick_func))
            with open(tick_func, "r", encoding="utf-8") as f:
                t_content = f.read()
            self.assertIn("daylight_detector", t_content)
            self.assertIn("cycle_night", t_content)
            self.assertIn("cycle_morning", t_content)
            self.assertIn("scoreboard players add #world world_init 0", t_content)
            self.assertIn("execute if entity @a if score #world world_init matches 0", t_content)
            self.assertIn("player_join", t_content)
            self.assertFalse(os.path.exists(os.path.join(target_bp, "tick.json")))
            self.assertTrue(os.path.exists(os.path.join(target_bp, "functions", "tick.json")))

            # player_join.mcfunction
            join_func = os.path.join(target_bp, "functions", "mazerunner", "player_join.mcfunction")
            self.assertTrue(os.path.exists(join_func))
            with open(join_func, "r", encoding="utf-8") as f:
                j_content = f.read()
            self.assertIn("tag @s add joined", j_content)
            self.assertIn("scoreboard players add DAY_COUNTER dayCounter 0", j_content)
            self.assertIn("execute if score #world world_init matches 0 run function mazerunner/init_world", j_content)
            self.assertNotIn("titleraw @s title", j_content)
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
            self.assertEqual(ta_count, 3, "Devem existir exatamente 3 ticking areas: glade, templates e station.")
            self.assertEqual(total_chunks, 98, "Total de chunks deve ser exatamente 98 (64 + 30 + 4).")
        finally:
            shutil.rmtree(tmp_dir)

    def test_train_station_ticking_area(self):
        """Testa se a ticking area da estação de trem cobre todos os blocos de comando e receptores dos 8 geradores."""
        tmp_dir = tempfile.mkdtemp()
        try:
            target_bp = os.path.join(tmp_dir, "target_bp")
            BehaviorPackGenerator.generate("", target_bp, "MazeRunner", "mazerunner", "dummy-rp-uuid")

            init_func = os.path.join(target_bp, "functions", "mazerunner", "init_world.mcfunction")
            with open(init_func, "r", encoding="utf-8") as f:
                lines = f.readlines()

            station_box = None
            for line in lines:
                if "maze_station" in line and line.strip().startswith("tickingarea add"):
                    parts = line.strip().split()
                    station_box = (
                        min(int(parts[2]), int(parts[5])),
                        max(int(parts[2]), int(parts[5])),
                        min(int(parts[4]), int(parts[7])),
                        max(int(parts[4]), int(parts[7])),
                    )
                    break

            self.assertIsNotNone(station_box, "A ticking area maze_station deve estar declarada no init_world.")
            min_x, max_x, min_z, max_z = station_box

            # Todos os 8 alvos de /setblock dos geradores na estação
            targets = [
                (213, -2212), (214, -2212), (216, -2212), (217, -2212),
                (213, -2208), (214, -2208), (216, -2208), (217, -2208)
            ]
            for tx, tz in targets:
                self.assertTrue(
                    min_x <= tx <= max_x and min_z <= tz <= max_z,
                    f"Alvo da estação ({tx}, {tz}) deve estar contido em maze_station [{min_x}..{max_x}, {min_z}..{max_z}]"
                )
        finally:
            shutil.rmtree(tmp_dir)

    def test_elevator_arrival_day_counter(self):
        """Testa se (306, 2, -2102) fixa o Dia 1 e nao executa cycle_night, e (271, 1, -2201) executa cycle_night."""
        tmp_dir = tempfile.mkdtemp()
        try:
            db_dir = os.path.join(tmp_dir, "db")
            os.makedirs(db_dir)

            cbs = [
                (306, 2, -2102, "scoreboard players add DAY_COUNTER dayCounter 1"),
                (271, 1, -2201, "scoreboard players add DAY_COUNTER dayCounter 1"),
                (377, 6, -2117, "scoreboard players reset DAY_COUNTER dayCounter"),
                (273, 1, -2200, "scoreboard players reset DAY_COUNTER dayCounter"),
            ]

            entries = []
            for i, (x, y, z, cmd) in enumerate(cbs):
                tag = nbtlib.Compound({
                    "id": nbtlib.String("CommandBlock"),
                    "x": nbtlib.Int(x),
                    "y": nbtlib.Int(y),
                    "z": nbtlib.Int(z),
                    "Command": nbtlib.String(cmd),
                    "CustomName": nbtlib.String("@"),
                    "ExecuteOnFirstTick": nbtlib.Byte(0),
                    "auto": nbtlib.Byte(0),
                })
                buf = io.BytesIO()
                nbtlib.File(tag).write(buf, byteorder="little")
                entries.append((f"chunk_key_{i}".encode("ascii"), buf.getvalue()))

            ldb_bytes = BedrockLevelDBManager.build_ldb([entries])
            ldb_path = os.path.join(db_dir, "000001.ldb")
            with open(ldb_path, "wb") as f:
                f.write(ldb_bytes)

            count = BedrockLevelDBManager.update_command_blocks(
                db_dir,
                lambda cmd: CommandTranslator.translate(cmd, set(), "mazerunner"),
                safe_name="mazerunner"
            )
            self.assertEqual(count, 4)

            with open(ldb_path, "rb") as f:
                updated_raw = f.read()
            read_blocks = BedrockLevelDBManager.read_ldb_all_entries(updated_raw)

            results = {}
            for block_entries in read_blocks:
                for k, v in block_entries:
                    tag = nbtlib.File.from_fileobj(io.BytesIO(v), byteorder="little")
                    coord = (int(tag.get("x", 0)), int(tag.get("y", 0)), int(tag.get("z", 0)))
                    results[coord] = str(tag.get("Command", ""))

            self.assertEqual(results[(306, 2, -2102)], "scoreboard players set DAY_COUNTER dayCounter 1")
            self.assertNotIn("cycle_night", results[(306, 2, -2102)])
            self.assertEqual(results[(271, 1, -2201)], "function mazerunner/cycle_night")
            self.assertEqual(results[(377, 6, -2117)], "scoreboard players set DAY_COUNTER dayCounter 1")
            self.assertNotIn("init_world", results[(377, 6, -2117)])
            self.assertEqual(results[(273, 1, -2200)], "scoreboard players set DAY_COUNTER dayCounter 1")
        finally:
            shutil.rmtree(tmp_dir)


if __name__ == "__main__":
    unittest.main()

