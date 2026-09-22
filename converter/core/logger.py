#!/usr/bin/env python3
"""
Módulo de Logging Estruturado de Conversão (Seção 29).
Autor: João Lucas Mayrinck
"""

import sys

class ConversionLogger:
    """Registra transformações e adaptações de comandos e recursos."""

    @staticmethod
    def log_command(java_cmd: str, bedrock_cmd: str, status: str = "CONVERTED", reason: str = ""):
        """Registra a transformação de um comando no formato exigido pela Seção 29."""
        print("[COMMAND]")
        print("Java:")
        print(f"  {java_cmd}")
        print("Bedrock:")
        print(f"  {bedrock_cmd}")
        print("Status:")
        print(f"  {status}")
        if reason:
            print("Reason:")
            print(f"  {reason}")
        print("-" * 50)

