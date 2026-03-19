"""
Advoga Fácil v1.0
Sistema de Gestão Jurídica para Escritórios de Advocacia
Autor: Cleber Santos de Lima
"""
import sys
import os

# Garante que o diretório do projeto esteja no path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import database as db
from views.login import TelaLogin
from views.main_window import JanelaPrincipal


def main():
    # 1. Inicializa banco de dados
    db.init_db()

    # 2. Tela de Login
    login = TelaLogin()
    login.mainloop()

    # 3. Se autenticado, abre janela principal
    if login.get_usuario():
        app = JanelaPrincipal()
        app.mainloop()


if __name__ == "__main__":
    main()
