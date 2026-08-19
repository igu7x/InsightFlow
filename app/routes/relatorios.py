from datetime import datetime
from pathlib import Path
import re

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import Relatorio
from app.schemas import RelatorioEntrada
from app.security import decrypt_text, encrypt_text
from app.services.audit_service import registrar_auditoria
from app.templating import templates

router = APIRouter(prefix="/relatorios", tags=["Relatórios"])

TEXTO_INDISPONIVEL = (
    "[Conteúdo indisponível: não foi possível descriptografar este relatório. "
    "Verifique se a DATA_ENCRYPTION_KEY do .env é a mesma usada quando ele foi gravado.]"
)


def nome_seguro(texto: str) -> str:
    texto = re.sub(r"[^a-zA-Z0-9áéíóúÁÉÍÓÚçÇ_-]+", "-", texto)
    return texto.strip("-").lower() or "relatorio"


def conteudo_legivel(relatorio: Relatorio) -> str:
    """Devolve o texto do relatório em claro, sem derrubar a página se a
    chave de criptografia não corresponder ao registro gravado."""
    if not relatorio.criptografado:
        return relatorio.conteudo
    try:
        return decrypt_text(relatorio.conteudo) or ""
    except RuntimeError:
        return TEXTO_INDISPONIVEL


@router.get("")
def pagina_relatorios(request: Request, db: Session = Depends(get_db)):
    registros = db.scalars(select(Relatorio).order_by(Relatorio.criado_em.desc())).all()
    relatorios = [
        {
            "titulo": relatorio.titulo,
            "conteudo": conteudo_legivel(relatorio),
            "criado_em": relatorio.criado_em,
        }
        for relatorio in registros
    ]
    return templates.TemplateResponse(
        "relatorios.html",
        {
            "request": request,
            "page_title": "Central de relatórios",
            "page_subtitle": "Consulte os conteúdos gerados pela inteligência artificial.",
            "relatorios": relatorios,
        },
    )


@router.post("/exportar")
def exportar_relatorio(
    entrada: RelatorioEntrada,
    request: Request,
    db: Session = Depends(get_db),
):
    settings = get_settings()
    pasta = Path(settings.obsidian_vault_path) / "Relatorios"
    agora = datetime.now()
    arquivo = pasta / f"{agora:%Y-%m-%d_%H-%M}_{nome_seguro(entrada.titulo)}.md"
    markdown = f'''---
titulo: "{entrada.titulo}"
data: "{agora:%Y-%m-%d %H:%M}"
tipo: relatorio
sistema: InsightFlow IA
---

# {entrada.titulo}

{entrada.conteudo}

## Links internos
- [[Dashboard Geral]]
- [[Indicadores]]
- [[Planos de Ação]]
'''
    try:
        pasta.mkdir(parents=True, exist_ok=True)
        arquivo.write_text(markdown, encoding="utf-8")
    except OSError as erro:
        raise HTTPException(500, f"Falha ao salvar no Obsidian: {erro}") from erro

    # O conteúdo vai criptografado para o banco, no mesmo padrão das conversas
    # do assistente. O arquivo Markdown do Vault permanece em texto legível,
    # porque é justamente o material que o usuário vai consultar no Obsidian.
    try:
        db.add(
            Relatorio(
                titulo=entrada.titulo,
                conteudo=encrypt_text(entrada.conteudo),
                arquivo_markdown=str(arquivo),
                criptografado=True,
            )
        )
        registrar_auditoria(db, request, "exportar_relatorio", entrada.titulo[:200])
        db.commit()
    except Exception as erro:
        db.rollback()
        arquivo.unlink(missing_ok=True)
        raise HTTPException(500, "Falha ao registrar o relatório no banco.") from erro

    return {"mensagem": "Relatório exportado.", "arquivo": str(arquivo)}
