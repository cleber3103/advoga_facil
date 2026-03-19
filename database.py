"""
Advoga Fácil - Módulo de Banco de Dados
Gerencia a conexão e estrutura do banco SQLite
"""
import sqlite3
import os
import hashlib
import secrets
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "advoga_facil.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def hash_senha(senha: str) -> str:
    salt = "advogafacil_salt_2025"
    return hashlib.sha256((senha + salt).encode()).hexdigest()


def init_db():
    """Inicializa o banco de dados e cria as tabelas."""
    conn = get_connection()
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            nome       TEXT    NOT NULL,
            email      TEXT    NOT NULL UNIQUE,
            senha_hash TEXT    NOT NULL,
            perfil     TEXT    NOT NULL CHECK(perfil IN ('Administrador','Advogado','Assistente')),
            ativo      INTEGER NOT NULL DEFAULT 1,
            criado_em  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS clientes (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            nome       TEXT NOT NULL,
            cpf_cnpj   TEXT NOT NULL UNIQUE,
            endereco   TEXT,
            telefone   TEXT,
            email      TEXT,
            obs        TEXT,
            ativo      INTEGER NOT NULL DEFAULT 1,
            criado_em  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS processos (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            numero        TEXT    NOT NULL UNIQUE,
            tipo          TEXT    NOT NULL,
            vara          TEXT,
            status        TEXT    NOT NULL DEFAULT 'Em andamento',
            cliente_id    INTEGER NOT NULL REFERENCES clientes(id),
            advogado_id   INTEGER REFERENCES usuarios(id),
            obs           TEXT,
            criado_em     TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS andamentos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            processo_id INTEGER NOT NULL REFERENCES processos(id) ON DELETE CASCADE,
            descricao   TEXT    NOT NULL,
            data        TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
            usuario_id  INTEGER REFERENCES usuarios(id)
        );

        CREATE TABLE IF NOT EXISTS prazos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            processo_id INTEGER NOT NULL REFERENCES processos(id) ON DELETE CASCADE,
            descricao   TEXT    NOT NULL,
            data_prazo  TEXT    NOT NULL,
            concluido   INTEGER NOT NULL DEFAULT 0,
            criado_em   TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS documentos (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            nome           TEXT    NOT NULL,
            caminho        TEXT    NOT NULL,
            tipo_ref       TEXT    NOT NULL CHECK(tipo_ref IN ('cliente','processo')),
            referencia_id  INTEGER NOT NULL,
            enviado_em     TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        );
    """)

    # Cria admin padrão se não existir
    admin = c.execute("SELECT id FROM usuarios WHERE perfil='Administrador' LIMIT 1").fetchone()
    if not admin:
        c.execute("""
            INSERT INTO usuarios (nome, email, senha_hash, perfil)
            VALUES (?, ?, ?, ?)
        """, ("Administrador", "admin@advogafacil.com", hash_senha("admin123"), "Administrador"))

    conn.commit()
    conn.close()


# ─── USUÁRIOS ────────────────────────────────────────────────────────────────

def autenticar(email: str, senha: str):
    conn = get_connection()
    usuario = conn.execute(
        "SELECT * FROM usuarios WHERE email=? AND senha_hash=? AND ativo=1",
        (email, hash_senha(senha))
    ).fetchone()
    conn.close()
    return dict(usuario) if usuario else None


def listar_usuarios():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM usuarios ORDER BY nome").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def salvar_usuario(dados: dict, uid=None):
    conn = get_connection()
    if uid:
        if dados.get("senha"):
            conn.execute(
                "UPDATE usuarios SET nome=?, email=?, senha_hash=?, perfil=?, ativo=? WHERE id=?",
                (dados["nome"], dados["email"], hash_senha(dados["senha"]),
                 dados["perfil"], dados.get("ativo", 1), uid)
            )
        else:
            conn.execute(
                "UPDATE usuarios SET nome=?, email=?, perfil=?, ativo=? WHERE id=?",
                (dados["nome"], dados["email"], dados["perfil"], dados.get("ativo", 1), uid)
            )
    else:
        conn.execute(
            "INSERT INTO usuarios (nome, email, senha_hash, perfil) VALUES (?,?,?,?)",
            (dados["nome"], dados["email"], hash_senha(dados["senha"]), dados["perfil"])
        )
    conn.commit()
    conn.close()


def excluir_usuario(uid: int):
    conn = get_connection()
    conn.execute("UPDATE usuarios SET ativo=0 WHERE id=?", (uid,))
    conn.commit()
    conn.close()


# ─── CLIENTES ────────────────────────────────────────────────────────────────

def listar_clientes(filtro=""):
    conn = get_connection()
    q = f"%{filtro}%"
    rows = conn.execute(
        "SELECT * FROM clientes WHERE ativo=1 AND (nome LIKE ? OR cpf_cnpj LIKE ?) ORDER BY nome",
        (q, q)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def buscar_cliente(cid: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM clientes WHERE id=?", (cid,)).fetchone()
    conn.close()
    return dict(row) if row else None


def salvar_cliente(dados: dict, cid=None):
    conn = get_connection()
    if cid:
        conn.execute(
            "UPDATE clientes SET nome=?,cpf_cnpj=?,endereco=?,telefone=?,email=?,obs=? WHERE id=?",
            (dados["nome"], dados["cpf_cnpj"], dados.get("endereco", ""),
             dados.get("telefone", ""), dados.get("email", ""), dados.get("obs", ""), cid)
        )
    else:
        conn.execute(
            "INSERT INTO clientes (nome,cpf_cnpj,endereco,telefone,email,obs) VALUES (?,?,?,?,?,?)",
            (dados["nome"], dados["cpf_cnpj"], dados.get("endereco", ""),
             dados.get("telefone", ""), dados.get("email", ""), dados.get("obs", ""))
        )
    conn.commit()
    conn.close()


def excluir_cliente(cid: int):
    conn = get_connection()
    conn.execute("UPDATE clientes SET ativo=0 WHERE id=?", (cid,))
    conn.commit()
    conn.close()


# ─── PROCESSOS ───────────────────────────────────────────────────────────────

def listar_processos(filtro="", status=""):
    conn = get_connection()
    q = f"%{filtro}%"
    query = """
        SELECT p.*, c.nome as cliente_nome, u.nome as advogado_nome
        FROM processos p
        LEFT JOIN clientes c ON c.id = p.cliente_id
        LEFT JOIN usuarios u ON u.id = p.advogado_id
        WHERE (p.numero LIKE ? OR c.nome LIKE ?)
    """
    params = [q, q]
    if status:
        query += " AND p.status=?"
        params.append(status)
    query += " ORDER BY p.criado_em DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def buscar_processo(pid: int):
    conn = get_connection()
    row = conn.execute(
        """SELECT p.*, c.nome as cliente_nome FROM processos p
           LEFT JOIN clientes c ON c.id=p.cliente_id WHERE p.id=?""", (pid,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def salvar_processo(dados: dict, pid=None):
    conn = get_connection()
    if pid:
        conn.execute(
            """UPDATE processos SET numero=?,tipo=?,vara=?,status=?,cliente_id=?,
               advogado_id=?,obs=? WHERE id=?""",
            (dados["numero"], dados["tipo"], dados.get("vara", ""), dados["status"],
             dados["cliente_id"], dados.get("advogado_id"), dados.get("obs", ""), pid)
        )
    else:
        conn.execute(
            """INSERT INTO processos (numero,tipo,vara,status,cliente_id,advogado_id,obs)
               VALUES (?,?,?,?,?,?,?)""",
            (dados["numero"], dados["tipo"], dados.get("vara", ""), dados["status"],
             dados["cliente_id"], dados.get("advogado_id"), dados.get("obs", ""))
        )
    conn.commit()
    conn.close()


def excluir_processo(pid: int):
    conn = get_connection()
    prazo = conn.execute(
        "SELECT id FROM prazos WHERE processo_id=? AND concluido=0", (pid,)
    ).fetchone()
    if prazo:
        conn.close()
        raise Exception("Processo possui prazos ativos. Conclua-os antes de excluir.")
    conn.execute("DELETE FROM processos WHERE id=?", (pid,))
    conn.commit()
    conn.close()


# ─── ANDAMENTOS ──────────────────────────────────────────────────────────────

def listar_andamentos(processo_id: int):
    conn = get_connection()
    rows = conn.execute(
        """SELECT a.*, u.nome as usuario_nome FROM andamentos a
           LEFT JOIN usuarios u ON u.id=a.usuario_id
           WHERE a.processo_id=? ORDER BY a.data DESC""",
        (processo_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def adicionar_andamento(processo_id: int, descricao: str, usuario_id: int):
    conn = get_connection()
    conn.execute(
        "INSERT INTO andamentos (processo_id,descricao,usuario_id) VALUES (?,?,?)",
        (processo_id, descricao, usuario_id)
    )
    conn.commit()
    conn.close()


# ─── PRAZOS ──────────────────────────────────────────────────────────────────

def listar_prazos(processo_id=None, apenas_ativos=True):
    conn = get_connection()
    query = """
        SELECT pr.*, p.numero as processo_num, c.nome as cliente_nome
        FROM prazos pr
        LEFT JOIN processos p ON p.id=pr.processo_id
        LEFT JOIN clientes c ON c.id=p.cliente_id
        WHERE 1=1
    """
    params = []
    if processo_id:
        query += " AND pr.processo_id=?"
        params.append(processo_id)
    if apenas_ativos:
        query += " AND pr.concluido=0"
    query += " ORDER BY pr.data_prazo ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def salvar_prazo(dados: dict, prid=None):
    conn = get_connection()
    if prid:
        conn.execute(
            "UPDATE prazos SET descricao=?,data_prazo=?,concluido=? WHERE id=?",
            (dados["descricao"], dados["data_prazo"], dados.get("concluido", 0), prid)
        )
    else:
        conn.execute(
            "INSERT INTO prazos (processo_id,descricao,data_prazo) VALUES (?,?,?)",
            (dados["processo_id"], dados["descricao"], dados["data_prazo"])
        )
    conn.commit()
    conn.close()


def concluir_prazo(prid: int):
    conn = get_connection()
    conn.execute("UPDATE prazos SET concluido=1 WHERE id=?", (prid,))
    conn.commit()
    conn.close()


# ─── DASHBOARD ───────────────────────────────────────────────────────────────

def estatisticas():
    conn = get_connection()
    total_clientes  = conn.execute("SELECT COUNT(*) FROM clientes WHERE ativo=1").fetchone()[0]
    total_processos = conn.execute("SELECT COUNT(*) FROM processos").fetchone()[0]
    em_andamento    = conn.execute("SELECT COUNT(*) FROM processos WHERE status='Em andamento'").fetchone()[0]
    prazos_hoje     = conn.execute(
        "SELECT COUNT(*) FROM prazos WHERE concluido=0 AND date(data_prazo)<=date('now','localtime')"
    ).fetchone()[0]
    conn.close()
    return {
        "total_clientes":  total_clientes,
        "total_processos": total_processos,
        "em_andamento":    em_andamento,
        "prazos_vencidos": prazos_hoje,
    }
