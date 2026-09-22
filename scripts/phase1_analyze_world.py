#!/usr/bin/env python3
"""
Fase 1: Extração e Inspeção Estrutural do Mundo Minecraft Java
Autor: João Lucas Mayrinck
"""

import os
import sys
import json
import gzip
import zipfile
import io
import nbtlib

def extract_archives(java_zip_path: str, resources_zip_path: str, ext_world: str, ext_rp: str):
    print(f"[*] Extraindo Mundo Java de: {java_zip_path} para {ext_world}...")
    with zipfile.ZipFile(java_zip_path, "r") as z:
        z.extractall(ext_world)
    print(f"    [OK] Mundo Java extraído com sucesso.")

    if os.path.exists(resources_zip_path):
    if resources_zip_path and os.path.exists(resources_zip_path):
        print(f"[*] Extraindo Resource Pack de: {resources_zip_path} para {ext_rp}...")
        with zipfile.ZipFile(resources_zip_path, "r") as z:
            z.extractall(ext_rp)
        print(f"    [OK] Resource Pack extraído com sucesso.")
    else:
        # Fallback se resources estiver dentro de extracted/java_world/resources
        # Fallback 1: resources.zip embutido no mundo Java
        embedded_zip = os.path.join(ext_world, "resources.zip")
        embedded_rp = os.path.join(ext_world, "resources")
        if os.path.isdir(embedded_rp):
        if os.path.exists(embedded_zip):
            print(f"[*] Extraindo Resource Pack embutido ({embedded_zip}) para {ext_rp}...")
            with zipfile.ZipFile(embedded_zip, "r") as z:
                z.extractall(ext_rp)
            print(f"    [OK] Resource Pack embutido extraído com sucesso.")
        elif os.path.isdir(embedded_rp):
            print(f"[*] Copiando Resource Pack interno de {embedded_rp} para {ext_rp}...")
            import shutil
            shutil.copytree(embedded_rp, ext_rp, dirs_exist_ok=True)
            print(f"    [OK] Resource Pack interno copiado.")

def parse_level_dat(world_dir: str) -> dict:
    level_path = os.path.join(world_dir, "level.dat")
    if not os.path.exists(level_path):
        return {}
    with open(level_path, "rb") as f:
        raw = f.read()
    try:
        decompressed = gzip.decompress(raw)
        nbt = nbtlib.File.from_fileobj(io.BytesIO(decompressed))
    except Exception:
        nbt = nbtlib.File.from_fileobj(io.BytesIO(raw))

    data = nbt.get("Data", {})
    gamerules = {}
    if "GameRules" in data:
        for k, v in data["GameRules"].items():
            gamerules[str(k)] = str(v)

    version_info = data.get("Version", {})
    return {
        "LevelName": str(data.get("LevelName", "Unknown")),
        "DataVersion": int(data.get("DataVersion", 0)),
        "Version": {
            "Name": str(version_info.get("Name", "Unknown")),
            "Id": int(version_info.get("Id", 0)),
            "Snapshot": int(version_info.get("Snapshot", 0))
        } if version_info else {},
        "SpawnX": int(data.get("SpawnX", 0)),
        "SpawnY": int(data.get("SpawnY", 0)),
        "SpawnZ": int(data.get("SpawnZ", 0)),
        "Time": int(data.get("Time", 0)),
        "DayTime": int(data.get("DayTime", 0)),
        "Difficulty": int(data.get("Difficulty", 1)),
        "DifficultyLocked": bool(data.get("DifficultyLocked", 0)),
        "Hardcore": bool(data.get("hardcore", 0)),
        "GameRules": gamerules
    }

def scan_scoreboard(world_dir: str) -> dict:
    sb_path = os.path.join(world_dir, "data", "scoreboard.dat")
    if not os.path.exists(sb_path):
        return {"objectives": [], "teams": []}
    try:
        with open(sb_path, "rb") as f:
            raw = gzip.decompress(f.read())
        nbt = nbtlib.File.from_fileobj(io.BytesIO(raw))
        data = nbt.get("data", {})
        objs = []
        for obj in data.get("Objectives", []):
            objs.append({
                "Name": str(obj.get("Name")),
                "DisplayName": str(obj.get("DisplayName")),
                "CriteriaName": str(obj.get("CriteriaName"))
            })
        teams = []
        for t in data.get("Teams", []):
            teams.append({
                "Name": str(t.get("Name")),
                "DisplayName": str(t.get("DisplayName")),
                "Members": [str(m) for m in t.get("Players", [])]
            })
        return {"objectives": objs, "teams": teams}
    except Exception as e:
        return {"error": str(e), "objectives": [], "teams": []}

def scan_datapacks(world_dir: str) -> list:
    dp_dir = os.path.join(world_dir, "datapacks")
    datapacks = []
    if not os.path.isdir(dp_dir):
        return datapacks

    for item in os.listdir(dp_dir):
        full_p = os.path.join(dp_dir, item)
        dp_info = {"name": item, "is_zip": item.endswith(".zip"), "functions": 0, "loot_tables": 0, "tags": 0}
        if item.endswith(".zip"):
            try:
                with zipfile.ZipFile(full_p, "r") as z:
                    for name in z.namelist():
                        if name.endswith(".mcfunction"):
                            dp_info["functions"] += 1
                        elif "/loot_tables/" in name and name.endswith(".json"):
                            dp_info["loot_tables"] += 1
                        elif "/tags/" in name and name.endswith(".json"):
                            dp_info["tags"] += 1
            except Exception:
                pass
        elif os.path.isdir(full_p):
            for root, _, files in os.walk(full_p):
                for f in files:
                    if f.endswith(".mcfunction"):
                        dp_info["functions"] += 1
                    elif "loot_tables" in root and f.endswith(".json"):
                        dp_info["loot_tables"] += 1
                    elif "tags" in root and f.endswith(".json"):
                        dp_info["tags"] += 1
        datapacks.append(dp_info)
    return datapacks

def scan_dimensions(world_dir: str) -> dict:
    dims = {
        "overworld": {"regions": 0, "path": "region"},
        "nether": {"regions": 0, "path": "DIM-1/region"},
        "the_end": {"regions": 0, "path": "DIM1/region"}
    }
    for dim_key, dim_val in dims.items():
        reg_dir = os.path.join(world_dir, dim_val["path"])
        if os.path.isdir(reg_dir):
            mca_files = [f for f in os.listdir(reg_dir) if f.endswith(".mca")]
            dim_val["regions"] = len(mca_files)
            dim_val["mca_files"] = mca_files
        else:
            dim_val["mca_files"] = []
    return dims

def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    input_java = os.path.join(base_dir, "input", "java-version.zip")
    inputs_dir = os.path.join(base_dir, "inputs")
    expected_dir = os.path.join(base_dir, "expected")

    # Localiza o arquivo .zip do mundo Java em inputs/
    input_java = os.path.join(inputs_dir, "java-version.zip")
    if not os.path.exists(input_java) and os.path.isdir(inputs_dir):
        zips = [os.path.join(inputs_dir, f) for f in os.listdir(inputs_dir) if f.endswith(".zip")]
        if zips:
            input_java = zips[0]

    if not os.path.exists(input_java):
        input_java = os.path.join(base_dir, "inputs", "java-version.zip")
    
    input_rp = os.path.join(base_dir, "input", "resources.zip")
    if not os.path.exists(input_rp):
        input_rp = os.path.join(base_dir, "inputs", "maze-runner-resource-pack.mcpack")
        print(f"[ERRO] Arquivo Java (.zip) não encontrado em {inputs_dir}")
        sys.exit(1)

    # Localiza Resource Pack externo opcional (se ausente, extrai o embutido no mundo Java)
    input_rp = ""
    for candidate in [
        os.path.join(inputs_dir, "resources.zip"),
        os.path.join(expected_dir, "resources.zip"),
        os.path.join(expected_dir, "maze-runner-resource-pack.mcpack")
    ]:
        if os.path.exists(candidate):
            input_rp = candidate
            break

    ext_world = os.path.join(base_dir, "extracted", "java_world")
    ext_rp = os.path.join(base_dir, "extracted", "java_resource_pack")
    analysis_dir = os.path.join(base_dir, "analysis")
    os.makedirs(analysis_dir, exist_ok=True)

    # 1. Extração
    extract_archives(input_java, input_rp, ext_world, ext_rp)

    # 2. Inspeção Estrutural
    print("[*] Inspecionando level.dat...")
    level_info = parse_level_dat(ext_world)
    print(f"    [OK] Nome: {level_info.get('LevelName')} | Versão: {level_info.get('Version', {}).get('Name')} (DataVersion: {level_info.get('DataVersion')})")

    print("[*] Inspecionando dimensões e regiões MCA...")
    dims = scan_dimensions(ext_world)
    for dim, dinfo in dims.items():
        print(f"    [OK] Dimensão {dim}: {dinfo['regions']} arquivos de região (.mca)")

    print("[*] Inspecionando scoreboards...")
    sb_info = scan_scoreboard(ext_world)
    print(f"    [OK] Scoreboards encontrados: {len(sb_info.get('objectives', []))} objetivos, {len(sb_info.get('teams', []))} equipes")

    print("[*] Inspecionando datapacks...")
    dps = scan_datapacks(ext_world)
    for dp in dps:
        print(f"    [OK] Datapack: {dp['name']} ({dp['functions']} funções, {dp['loot_tables']} loot tables)")

    # 3. Gerar world_structure.json
    structure_report = {
        "source_archive": input_java,
        "level_info": level_info,
        "dimensions": {k: {"regions": v["regions"], "sample_mca": v["mca_files"][:5]} for k, v in dims.items()},
        "scoreboard": sb_info,
        "datapacks": dps,
        "total_regions": sum(v["regions"] for v in dims.values())
    }

    out_file = os.path.join(analysis_dir, "world_structure.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(structure_report, f, indent=2, ensure_ascii=False)
    print(f"\n[SUCESSO] Relatório de estrutura salvo em: {out_file}")

if __name__ == "__main__":
    main()

