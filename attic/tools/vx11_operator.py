#!/usr/bin/env python3
"""Herramienta ligera de operador VX11 (staging).

Provee comandos para verificar estado forense, listar staging y aplicar cambios
de manera controlada. Este script no fuerza commits ni merges remotos.
"""
import argparse
import json
from pathlib import Path


def quick_health():
    try:
        from config.forensics import quick_health_check
        report = quick_health_check()
        print(json.dumps(report, indent=2, ensure_ascii=False))
    except Exception as e:
        print("Error ejecutando quick_health_check:", e)


def list_staging():
    p = Path('.tmp_copilot')
    if not p.exists():
        print("No existe .tmp_copilot/")
        return
    for f in sorted(p.iterdir()):
        print(f.name)


def mark_applied():
    p = Path('.tmp_copilot/applied.log')
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('a', encoding='utf-8') as fh:
        fh.write('Applied by vx11_operator\n')
    print('Registered apply in .tmp_copilot/applied.log')


def main():
    parser = argparse.ArgumentParser(prog='vx11-operator')
    sub = parser.add_subparsers(dest='cmd')
    sub.add_parser('health', help='Run quick health check')
    sub.add_parser('staging', help='List .tmp_copilot staging files')
    sub.add_parser('apply', help='Mark staged changes as applied (manual)')

    args = parser.parse_args()
    if args.cmd == 'health':
        quick_health()
    elif args.cmd == 'staging':
        list_staging()
    elif args.cmd == 'apply':
        mark_applied()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
