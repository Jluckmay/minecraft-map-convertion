#!/usr/bin/env python3
"""
Suíte de Testes Automatizados de Integridade e Validação:
Minecraft Map Converter Java <-> Bedrock 1.26.40+ (Mazescapist / MazeRunner)
Autor: João Lucas Mayrinck
"""

import os
import sys
import json
import zipfile
import hashlib
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DIST_DIR = os.path.join(PROJECT_ROOT, "dist")
PACKS_DIR = os.path.join(PROJECT_ROOT, "packs")
INPUTS_DIR = os.path.join(PROJECT_ROOT, "inputs")
BP_DIR = os.path.join(PACKS_DIR, "mazerunner_bp")
RP_DIR = os.path.join(PACKS_DIR, "mazerunner_rp")


def sha256_file(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192 * 1024):
            h.update(chunk)
    return h.hexdigest()


class TestMinecraftConversion(unittest.TestCase):
    """Testes de conformidade e integridade da conversão."""

    def test_01_dist_artifacts_exist(self):
        """Verifica se todos os artefatos finais foram gerados em dist/."""
        expected_files = [
            "mazescapist-bedrock-1.26.40.mcworld",
            "mazerunner-behavior-pack.mcpack",
            "mazerunner-resource-pack.mcpack",
            "SHA256SUMS.txt"
        ]
        for f in expected_files:
            path = os.path.join(DIST_DIR, f)
            self.assertTrue(os.path.exists(path), f"Arquivo não encontrado: {path}")
            self.assertGreater(os.path.getsize(path), 0, f"Arquivo vazio: {path}")

    def test_02_sha256_sums_match(self):
        """Valida se os hashes dos arquivos em dist/ coincidem com SHA256SUMS.txt."""
        sha_file = os.path.join(DIST_DIR, "SHA256SUMS.txt")
        self.assertTrue(os.path.exists(sha_file))
        with open(sha_file, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]
        
        for line in lines:
            parts = line.split()
            self.assertEqual(len(parts), 2)
            expected_hash = parts[0]
            filename = parts[1].lstrip("*")
            filepath = os.path.join(DIST_DIR, filename)
            self.assertTrue(os.path.exists(filepath), f"Arquivo referenciado em SHA256SUMS não existe: {filepath}")
            actual_hash = sha256_file(filepath)
            self.assertEqual(actual_hash.lower(), expected_hash.lower(), f"Hash incorreto para {filename}")

    def test_03_behavior_pack_structure(self):
        """Valida a estrutura de arquivos e JSONs do Behavior Pack."""
        # Manifest
        manifest_path = os.path.join(BP_DIR, "manifest.json")
        self.assertTrue(os.path.exists(manifest_path))
        with open(manifest_path, "r", encoding="utf-8") as f:
            bp_man = json.load(f)
        self.assertEqual(bp_man["format_version"], 2)
        self.assertEqual(bp_man["header"]["min_engine_version"], [1, 26, 40])

        # 15 NPCs em trading/
        trade_dir = os.path.join(BP_DIR, "trading")
        self.assertTrue(os.path.isdir(trade_dir))
        trade_files = [f for f in os.listdir(trade_dir) if f.endswith("_trades.json")]
        self.assertEqual(len(trade_files), 15, f"Esperado 15 arquivos de trade, encontrados {len(trade_files)}")
        for tf in trade_files:
            with open(os.path.join(trade_dir, tf), "r", encoding="utf-8") as f:
                data = json.load(f)
                self.assertIn("tiers", data)
                self.assertGreater(len(data["tiers"][0]["trades"]), 0)

        # 18 Entidades BP (15 NPCs + 3 Bosses)
        entity_dir = os.path.join(BP_DIR, "entities")
        self.assertTrue(os.path.isdir(entity_dir))
        ent_files = [f for f in os.listdir(entity_dir) if f.endswith(".json")]
        self.assertEqual(len(ent_files), 18, f"Esperado 18 entidades BP, encontrados {len(ent_files)}")

        # Funções
        fn_dir = os.path.join(BP_DIR, "functions")
        self.assertTrue(os.path.isdir(fn_dir))
        self.assertTrue(os.path.exists(os.path.join(fn_dir, "mazerunner", "init_world.mcfunction")))
        self.assertTrue(os.path.exists(os.path.join(fn_dir, "mazerunner", "setup_hall_of_fame.mcfunction")))
        self.assertTrue(os.path.exists(os.path.join(fn_dir, "mazerunner", "starter_kit.mcfunction")))

    def test_04_resource_pack_structure(self):
        """Valida a estrutura de arquivos e JSONs do Resource Pack."""
        # Manifest
        manifest_path = os.path.join(RP_DIR, "manifest.json")
        self.assertTrue(os.path.exists(manifest_path))
        with open(manifest_path, "r", encoding="utf-8") as f:
            rp_man = json.load(f)
        self.assertEqual(rp_man["format_version"], 2)
        self.assertEqual(rp_man["header"]["min_engine_version"], [1, 26, 40])

        # Client Entities
        rp_ent_dir = os.path.join(RP_DIR, "entity")
        self.assertTrue(os.path.isdir(rp_ent_dir))
        rp_ent_files = [f for f in os.listdir(rp_ent_dir) if f.endswith(".entity.json")]
        self.assertEqual(len(rp_ent_files), 18, f"Esperado 18 client entities RP, encontrados {len(rp_ent_files)}")

        # Texturas das Paredes (bedrock_0..4.png)
        tex_dir = os.path.join(RP_DIR, "textures", "blocks")
        self.assertTrue(os.path.isdir(tex_dir))
        for i in range(5):
            self.assertTrue(os.path.exists(os.path.join(tex_dir, f"bedrock_{i}.png")), f"Faltando bedrock_{i}.png")

        # terrain_texture.json
        tt_path = os.path.join(RP_DIR, "textures", "terrain_texture.json")
        self.assertTrue(os.path.exists(tt_path))
        with open(tt_path, "r", encoding="utf-8") as f:
            tt_data = json.load(f)
            for i in range(5):
                self.assertIn(f"bedrock_{i}", tt_data["texture_data"])

    def test_05_mcworld_pack_integration(self):
        """Verifica se o .mcworld contém os pacotes incorporados internamente."""
        mcworld_path = os.path.join(DIST_DIR, "mazescapist-bedrock-1.26.40.mcworld")
        self.assertTrue(os.path.exists(mcworld_path))
        with zipfile.ZipFile(mcworld_path, "r") as z:
            names = z.namelist()
            self.assertTrue(any(n.startswith("db/") for n in names), "LevelDB ausente no mcworld")
            self.assertIn("world_behavior_packs.json", names)
            self.assertIn("world_resource_packs.json", names)
            self.assertTrue(any(n.startswith("behavior_packs/mazerunner_bp/") for n in names))
            self.assertTrue(any(n.startswith("resource_packs/mazerunner_rp/") for n in names))


if __name__ == "__main__":
    unittest.main(verbosity=2)

