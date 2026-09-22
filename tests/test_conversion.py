#!/usr/bin/env python3
"""
Suíte de Testes Automatizados e Universais:
Minecraft Map Converter & Bridge Tool: Java <-> Bedrock (1.26.40+)
Autor: João Lucas Mayrinck
"""

import io
import os
import sys
import json
import zipfile
import tempfile
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from map_converter import (
    DatapackConverter,
    LootTableConverter,
    NPCTradeExtractor,
    MapConverterApp,
    sha256_file
)


class TestUniversalMapConverter(unittest.TestCase):
    """Testes unitários e de integração do motor de conversão universal."""

    def test_01_tellraw_color_conversion(self):
        """Testa conversão de tellraw Java com cores para Bedrock rawtext."""
        java_cmd = 'tellraw @a {"text":"Bem-vindo ao labirinto","color":"green"}'
        bedrock_cmd = DatapackConverter.convert_command(java_cmd)
        self.assertIn('"rawtext"', bedrock_cmd)
        self.assertIn("§aBem-vindo ao labirinto", bedrock_cmd)

    def test_02_playsound_translation(self):
        """Testa mapeamento de sons Java para identificadores Bedrock."""
        java_cmd = "playsound minecraft:entity.player.levelup master @p"
        bedrock_cmd = DatapackConverter.convert_command(java_cmd)
        self.assertIn("playsound random.levelup @p", bedrock_cmd)
        self.assertNotIn("master", bedrock_cmd)

    def test_03_forceload_and_data_merge(self):
        """Testa conversão de comandos exclusivos de Java (/forceload e /data merge)."""
        f_cmd = "forceload add 100 100 200 200"
        conv_f = DatapackConverter.convert_command(f_cmd)
        self.assertTrue(conv_f.startswith("tickingarea add"))

        d_cmd = "data merge block 10 20 30 {Delay:0}"
        conv_d = DatapackConverter.convert_command(d_cmd)
        self.assertEqual(conv_d, "setblock 10 20 30 mob_spawner")

    def test_04_loot_table_conversion(self):
        """Testa conversão de pools, rolls e funções em loot tables."""
        java_loot = {
            "pools": [
                {
                    "rolls": 1,
                    "entries": [
                        {
                            "type": "minecraft:item",
                            "name": "minecraft:emerald",
                            "weight": 1,
                            "functions": [
                                {"function": "minecraft:set_count", "count": {"min": 1, "max": 3}},
                                {"function": "minecraft:looting_enchant", "count": {"min": 0, "max": 1}}
                            ]
                        }
                    ]
                }
            ]
        }
        b_loot = LootTableConverter.convert(java_loot)
        self.assertEqual(len(b_loot["pools"]), 1)
        entry = b_loot["pools"][0]["entries"][0]
        self.assertEqual(entry["name"], "minecraft:emerald")
        self.assertEqual(len(entry["functions"]), 2)
        self.assertEqual(entry["functions"][0]["function"], "set_count")
        self.assertEqual(entry["functions"][1]["function"], "looting_enchant")

    def test_05_trade_extraction_and_metadata(self):
        """Testa extração de ofertas NBT e metadados de aldeões de comando summon."""
        cmd = (
            'summon villager 10 65 20 {'
            'CustomName:\'{"text":"Merchant_John"}\','
            'VillagerData:{profession:"minecraft:cleric",type:"minecraft:desert"},'
            'Offers:{Recipes:['
            '{buy:{id:"minecraft:emerald",Count:5b},sell:{id:"minecraft:potion",Count:1b}},'
            '{buy:{id:"minecraft:gold_ingot",Count:3b},buyB:{id:"minecraft:emerald",Count:1b},sell:{id:"minecraft:golden_apple",Count:1b}}'
            ']}}'
        )
        slug, disp_name, prof, biome = NPCTradeExtractor.extract_npc_metadata(cmd)
        self.assertEqual(slug, "merchant_john")
        self.assertEqual(disp_name, "Merchant_John")
        self.assertEqual(prof, "cleric")
        self.assertEqual(biome, "desert")

        trades = NPCTradeExtractor.parse_trades_from_command(cmd)
        self.assertEqual(len(trades), 2)
        self.assertEqual(trades[0]["buy"], "emerald")
        self.assertEqual(trades[0]["buy_count"], 5)
        self.assertEqual(trades[0]["sell"], "potion")
        self.assertEqual(trades[0]["sell_count"], 1)

        self.assertEqual(trades[1]["buy"], "gold_ingot")
        self.assertEqual(trades[1]["buyB"], "emerald")
        self.assertEqual(trades[1]["sell"], "golden_apple")

    def test_06_idempotent_summon_wrapping(self):
        """Testa inserção automática de cláusula de idempotência em invocações."""
        cmd = "summon namespace:npc_trader 100 64 200"
        conv = DatapackConverter.convert_command(cmd, known_npcs={"trader"})
        self.assertTrue(conv.startswith("execute unless entity @e[type=custom:npc_trader] run summon"))

    def test_07_end_to_end_synthetic_conversion(self):
        """Testa o fluxo completo do conversor utilizando um mundo sintético em memória."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            java_zip_path = os.path.join(tmp_dir, "synthetic_java.zip")
            bedrock_mcworld_path = os.path.join(tmp_dir, "synthetic_bedrock.mcworld")
            out_dir = os.path.join(tmp_dir, "dist")
            packs_dir = os.path.join(tmp_dir, "packs")

            # Cria mock do Java zip
            with zipfile.ZipFile(java_zip_path, "w") as z:
                # Função com summon e tellraw
                fn_content = (
                    'summon villager 0 64 0 {CustomName:\'{"text":"Alex"}\',VillagerData:{profession:"minecraft:fletcher",type:"minecraft:plains"},Offers:{Recipes:[{buy:{id:"minecraft:stick",Count:32b},sell:{id:"minecraft:emerald",Count:1b}}]}}\n'
                    'tellraw @a {"text":"Villager spawned","color":"gold"}\n'
                )
                z.writestr("datapacks/custom_pack/data/custom/functions/spawn_trader.mcfunction", fn_content)
                # Loot table
                loot_content = json.dumps({"pools": [{"rolls": 1, "entries": [{"name": "minecraft:iron_ingot", "functions": []}]}]})
                z.writestr("datapacks/custom_pack/data/custom/loot_tables/entities/custom_mob.json", loot_content)

            # Cria mock do Bedrock mcworld inicial do Chunker
            with zipfile.ZipFile(bedrock_mcworld_path, "w") as z:
                z.writestr("db/CURRENT", "CURRENT LEVELDB")
                z.writestr("level.dat", b"MOCK_LEVEL_DAT")

            # Executa conversor
            app = MapConverterApp(
                java_zip=java_zip_path,
                bedrock_world=bedrock_mcworld_path,
                output_dir=out_dir,
                packs_dir=packs_dir,
                world_name="TestAdventure",
                keep_temp=False
            )
            app.run()

            # Verificações
            expected_mcworld = os.path.join(out_dir, "testadventure-bedrock.mcworld")
            expected_bp = os.path.join(out_dir, "testadventure-behavior-pack.mcpack")
            expected_rp = os.path.join(out_dir, "testadventure-resource-pack.mcpack")
            sha_file = os.path.join(out_dir, "SHA256SUMS.txt")

            self.assertTrue(os.path.exists(expected_mcworld), "MCWORLD final não gerado")
            self.assertTrue(os.path.exists(expected_bp), "Behavior pack não gerado")
            self.assertTrue(os.path.exists(expected_rp), "Resource pack não gerado")
            self.assertTrue(os.path.exists(sha_file), "SHA256SUMS não gerado")

            # Valida manifesto do BP
            bp_man_path = os.path.join(packs_dir, "testadventure_bp", "manifest.json")
            self.assertTrue(os.path.exists(bp_man_path))
            with open(bp_man_path, "r", encoding="utf-8") as f:
                bp_data = json.load(f)
                self.assertEqual(bp_data["format_version"], 2)
                self.assertEqual(bp_data["header"]["min_engine_version"], [1, 20, 0])

            # Valida trade table gerada para Alex
            trade_path = os.path.join(packs_dir, "testadventure_bp", "trading", "alex_trades.json")
            self.assertTrue(os.path.exists(trade_path), "Trade table do NPC Alex não foi gerada")
            with open(trade_path, "r", encoding="utf-8") as f:
                t_data = json.load(f)
                self.assertEqual(t_data["tiers"][0]["trades"][0]["wants"][0]["item"], "stick")
                self.assertEqual(t_data["tiers"][0]["trades"][0]["gives"][0]["item"], "emerald")

    def test_08_distance_selector_and_functions(self):
        """Testa tradução de seletores distance= para r= e funções com namespace."""
        cmd1 = "/execute if entity @p[distance=..50] run function custom:open_doors_1"
        conv1 = DatapackConverter.convert_command(cmd1)
        self.assertIn("@p[r=50]", conv1)
        self.assertIn("function custom/open_doors_1", conv1)
        self.assertFalse(conv1.startswith("/"))

        cmd2 = "effect give @a[distance=5..20] speed 10 1"
        conv2 = DatapackConverter.convert_command(cmd2)
        self.assertIn("@a[rm=5,r=20]", conv2)

    def test_09_bedrock_texture_variations_and_blocks_json(self):
        """Testa geração de variações no terrain_texture.json e blocks.json para bedrock."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            java_zip = os.path.join(tmp_dir, "test_bs.zip")
            bedrock_mcworld = os.path.join(tmp_dir, "test_b.mcworld")
            out_dir = os.path.join(tmp_dir, "dist")
            packs_dir = os.path.join(tmp_dir, "packs")

            with zipfile.ZipFile(java_zip, "w") as z:
                # Mock blockstate bedrock.json
                bs_content = json.dumps({
                    "variants": {
                        "": [
                            {"model": "block/bedrock/0", "weight": 40},
                            {"model": "block/bedrock/1", "weight": 20}
                        ]
                    }
                })
                z.writestr("resources/assets/minecraft/blockstates/bedrock.json", bs_content)
                z.writestr("resources/assets/minecraft/textures/block/bedrock_0.png", b"PNG0")
                z.writestr("resources/assets/minecraft/textures/block/bedrock_1.png", b"PNG1")

            with zipfile.ZipFile(bedrock_mcworld, "w") as z:
                z.writestr("db/CURRENT", "CURRENT")
                z.writestr("level.dat", b"LEVEL")

            app = MapConverterApp(java_zip, bedrock_mcworld, out_dir, packs_dir, "BrickWorld", False)
            app.run()

            # Valida terrain_texture.json
            tt_path = os.path.join(packs_dir, "brickworld_rp", "textures", "terrain_texture.json")
            self.assertTrue(os.path.exists(tt_path))
            with open(tt_path, "r", encoding="utf-8") as f:
                tt = json.load(f)
                self.assertIn("bedrock", tt["texture_data"])
                variations = tt["texture_data"]["bedrock"]["textures"]["variations"]
                self.assertEqual(len(variations), 2)
                self.assertEqual(variations[0]["weight"], 40)
                self.assertEqual(variations[1]["weight"], 20)

            # Valida blocks.json
            blocks_path = os.path.join(packs_dir, "brickworld_rp", "blocks.json")
            self.assertTrue(os.path.exists(blocks_path))
            with open(blocks_path, "r", encoding="utf-8") as f:
                b_data = json.load(f)
                self.assertEqual(b_data["bedrock"]["textures"], "bedrock")

            # Valida fallback bedrock.png
            fallback_png = os.path.join(packs_dir, "brickworld_rp", "textures", "blocks", "bedrock.png")
            self.assertTrue(os.path.exists(fallback_png))

    def test_10_leveldb_command_block_update(self):
        """Testa o BedrockLevelDBManager lendo, modificando e salvando blocos LevelDB."""
        from map_converter import BedrockLevelDBManager
        import nbtlib

        # Cria mock de registro NBT com CommandBlock
        cb_tag = nbtlib.Compound({
            "id": nbtlib.String("CommandBlock"),
            "x": nbtlib.Int(100),
            "y": nbtlib.Int(65),
            "z": nbtlib.Int(-200),
            "Command": nbtlib.String("/execute if entity @p[distance=..50] run function custom:open_doors_1"),
            "CustomName": nbtlib.String("@"),
            "ExecuteOnFirstTick": nbtlib.Byte(0),
            "auto": nbtlib.Byte(0)
        })
        nbt_file = nbtlib.File(cb_tag)
        nbt_buf = io.BytesIO()
        nbt_file.write(nbt_buf, byteorder="little")

        with tempfile.TemporaryDirectory() as tmp_dir:
            db_dir = os.path.join(tmp_dir, "db")
            os.makedirs(db_dir)

            # Constrói um arquivo .ldb sintético
            chunk_key = b"\x00\x00\x00\x00\x00\x00\x00\x001"
            entries = [(chunk_key, nbt_buf.getvalue())]
            data_blocks = [entries]
            ldb_bytes = BedrockLevelDBManager.build_ldb(data_blocks)
            ldb_path = os.path.join(db_dir, "000001.ldb")
            with open(ldb_path, "wb") as f:
                f.write(ldb_bytes)

            # Executa atualização
            count = BedrockLevelDBManager.update_command_blocks(
                db_dir,
                lambda cmd: DatapackConverter.convert_command(cmd, set(), "custom")
            )
            self.assertEqual(count, 1)

            # Lê de volta e valida comando convertido
            with open(ldb_path, "rb") as f:
                updated_raw = f.read()
            read_blocks = BedrockLevelDBManager.read_ldb_all_entries(updated_raw)
            updated_chunk_val = read_blocks[0][0][1]
            updated_tag = nbtlib.File.from_fileobj(io.BytesIO(updated_chunk_val), byteorder="little")
            updated_cmd = str(updated_tag["Command"])
            self.assertIn("@p[r=50]", updated_cmd)
            self.assertIn("function custom/open_doors_1", updated_cmd)
            self.assertFalse(updated_cmd.startswith("/"))


if __name__ == "__main__":
    unittest.main(verbosity=2)

