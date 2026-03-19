"""
Advoga Fácil - Configurações e sessão do usuário logado
"""

# ─── Sessão global ────────────────────────────────────────────────────────────
usuario_logado = {
    "id":     None,
    "nome":   "",
    "email":  "",
    "perfil": "",
}


def iniciar_sessao(usuario: dict):
    usuario_logado.update(usuario)


def encerrar_sessao():
    for k in usuario_logado:
        usuario_logado[k] = None if k == "id" else ""


def pode(acao: str) -> bool:
    """Controle de permissão por perfil."""
    perfil = usuario_logado.get("perfil", "")
    permissoes = {
        "Administrador": [
            "gerenciar_usuarios", "excluir_processo", "excluir_cliente",
            "ver_relatorios", "ver_clientes", "ver_processos", "ver_prazos",
            "editar_cliente", "editar_processo", "adicionar_andamento",
        ],
        "Advogado": [
            "ver_clientes", "ver_processos", "ver_prazos", "ver_relatorios",
            "editar_cliente", "editar_processo", "adicionar_andamento",
        ],
        "Assistente": [
            "ver_clientes", "ver_processos", "ver_prazos",
            "editar_cliente", "editar_processo",
        ],
    }
    return acao in permissoes.get(perfil, [])


# ─── Tema e cores ─────────────────────────────────────────────────────────────
CORES = {
    "primaria":    "#1B3A6B",   # azul escuro
    "secundaria":  "#2E6DA4",   # azul médio
    "acento":      "#F0A500",   # âmbar
    "fundo":       "#F4F6F9",   # cinza claro
    "fundo2":      "#FFFFFF",
    "texto":       "#1A1A2E",
    "texto_claro": "#FFFFFF",
    "sucesso":     "#27AE60",
    "alerta":      "#E74C3C",
    "borda":       "#D0D7E3",
}

FONTE = "Segoe UI"
