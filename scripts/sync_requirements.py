#!/usr/bin/env python3
"""
Script para sincronizar requirements.txt da raiz com backend/requirements.txt.

Este script garante que todas as dependências em backend/requirements.txt
também estejam no requirements.txt da raiz (usado pelo Railway).

Uso:
    python scripts/sync_requirements.py
    python scripts/sync_requirements.py --check  # Apenas verifica, não modifica
"""

import sys
import argparse
from pathlib import Path
from typing import Set, List

# Caminhos dos arquivos
ROOT_DIR = Path(__file__).parent.parent
ROOT_REQUIREMENTS = ROOT_DIR / "requirements.txt"
BACKEND_REQUIREMENTS = ROOT_DIR / "backend" / "requirements.txt"


def parse_requirements(file_path: Path) -> Set[str]:
    """Parse requirements.txt e retorna conjunto de pacotes (sem versão)."""
    if not file_path.exists():
        return set()
    
    packages = set()
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # Ignorar comentários e linhas vazias
            if not line or line.startswith('#'):
                continue
            
            # Remover comentários inline
            if '#' in line:
                line = line.split('#')[0].strip()
            
            # Extrair nome do pacote (antes de >=, ==, etc)
            if line:
                package_name = line.split('>=')[0].split('==')[0].split('<=')[0].split('~=')[0].split('!=')[0].strip()
                if package_name:
                    packages.add(package_name.lower())
    
    return packages


def get_requirements_with_versions(file_path: Path) -> dict:
    """Retorna dict {package_name: full_line} do requirements.txt."""
    if not file_path.exists():
        return {}
    
    requirements = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            original_line = line.rstrip()
            line = original_line.strip()
            
            # Ignorar comentários e linhas vazias
            if not line or line.startswith('#'):
                continue
            
            # Remover comentários inline
            if '#' in line:
                line = line.split('#')[0].strip()
            
            if line:
                # Extrair nome do pacote
                package_name = line.split('>=')[0].split('==')[0].split('<=')[0].split('~=')[0].split('!=')[0].strip()
                if package_name:
                    requirements[package_name.lower()] = original_line
    
    return requirements


def sync_requirements(check_only: bool = False) -> int:
    """Sincroniza requirements.txt da raiz com backend/requirements.txt."""
    
    if not BACKEND_REQUIREMENTS.exists():
        print(f"❌ Arquivo não encontrado: {BACKEND_REQUIREMENTS}")
        return 1
    
    # Ler requirements do backend
    backend_packages = parse_requirements(BACKEND_REQUIREMENTS)
    backend_requirements = get_requirements_with_versions(BACKEND_REQUIREMENTS)
    
    # Ler requirements da raiz
    root_packages = parse_requirements(ROOT_REQUIREMENTS)
    root_requirements = get_requirements_with_versions(ROOT_REQUIREMENTS)
    
    # Encontrar pacotes faltando na raiz
    missing_packages = backend_packages - root_packages
    
    if not missing_packages:
        print("✅ Todos os pacotes de backend/requirements.txt estão em requirements.txt da raiz")
        return 0
    
    print(f"⚠️  Encontrados {len(missing_packages)} pacote(s) faltando em requirements.txt da raiz:")
    for pkg in sorted(missing_packages):
        if pkg in backend_requirements:
            print(f"   - {backend_requirements[pkg]}")
        else:
            print(f"   - {pkg}")
    
    if check_only:
        print("\n💡 Execute sem --check para sincronizar automaticamente")
        return 1
    
    # Adicionar pacotes faltantes
    print(f"\n📝 Adicionando pacotes faltantes ao {ROOT_REQUIREMENTS}...")
    
    # Ler conteúdo atual
    root_lines = []
    if ROOT_REQUIREMENTS.exists():
        with open(ROOT_REQUIREMENTS, 'r', encoding='utf-8') as f:
            root_lines = [line.rstrip() for line in f]
    
    # Adicionar pacotes faltantes (ordenados alfabeticamente)
    added_lines = []
    for pkg in sorted(missing_packages):
        if pkg in backend_requirements:
            line_to_add = backend_requirements[pkg]
            # Verificar se já não está (pode ter diferença de case)
            if not any(pkg.lower() in line.lower() for line in root_lines):
                root_lines.append(line_to_add)
                added_lines.append(line_to_add)
    
    # Ordenar linhas (comentários e vazias no topo, depois pacotes ordenados)
    sorted_lines = []
    packages_lines = []
    
    for line in root_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            sorted_lines.append(line)
        else:
            packages_lines.append(line)
    
    # Ordenar pacotes alfabeticamente
    packages_lines.sort(key=lambda x: x.lower().split('>=')[0].split('==')[0].split('<=')[0].strip())
    
    # Escrever arquivo atualizado
    with open(ROOT_REQUIREMENTS, 'w', encoding='utf-8') as f:
        for line in sorted_lines:
            f.write(line + '\n')
        if sorted_lines and packages_lines:
            f.write('\n')
        for line in packages_lines:
            f.write(line + '\n')
    
    print(f"✅ Adicionados {len(added_lines)} pacote(s):")
    for line in added_lines:
        print(f"   + {line}")
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Sincroniza requirements.txt da raiz com backend/requirements.txt"
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='Apenas verifica, não modifica arquivos'
    )
    
    args = parser.parse_args()
    
    exit_code = sync_requirements(check_only=args.check)
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
