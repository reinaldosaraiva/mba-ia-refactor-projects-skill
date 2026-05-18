"""Usuario orchestration."""
from src.errors import AuthError, NotFoundError
from src.models import usuario_model
from src.schemas import usuario_schema


def listar():
    return usuario_model.todos()


def detalhar(usuario_id):
    usuario = usuario_model.por_id(usuario_id)
    if not usuario:
        raise NotFoundError("Usuário não encontrado")
    return usuario


def criar(dados):
    clean = usuario_schema.validate_create(dados)
    usuario_id = usuario_model.criar(**clean)
    return {"id": usuario_id}


def login(dados):
    clean = usuario_schema.validate_login(dados)
    usuario = usuario_model.autenticar(clean["email"], clean["senha"])
    if not usuario:
        raise AuthError("Email ou senha inválidos")
    return usuario
