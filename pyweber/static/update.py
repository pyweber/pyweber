#!/usr/bin/env python
import subprocess
import sys
import time
import os

def main():
    print("Iniciando atualização do {framework}...")
    time.sleep(1)  # Esperar o processo original terminar

    try:
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '{framework}', '--upgrade'],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        print("Framework atualizado com sucesso!")
        print("Execute o comando novamente para usar a versão atualizada.")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao atualizar: {e}")
        print(f"Detalhes: {e.stderr}")

    # Manter a janela aberta no Windows
    if sys.platform == 'win32':
        os.system('pause')

if __name__ == "__main__":
    main()