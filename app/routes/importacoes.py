from io import BytesIO

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import Departamento, Registro
from app.services.audit_service import registrar_auditoria
from app.templating import templates

router = APIRouter(prefix="/importacoes", tags=["Importações"])

COLUNAS = {
    "departamento", "responsavel", "descricao", "status", "prioridade",
    "data_abertura", "prazo", "data_conclusao", "valor",
}
TIPOS_PERMITIDOS = {
    "text/csv",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/octet-stream",
}
LIMITE_LINHAS = 50_000


def texto_seguro(valor, limite: int) -> str:
    texto = "" if pd.isna(valor) else str(valor).strip()
    if len(texto) > limite:
        raise ValueError(f"Campo excede o limite de {limite} caracteres.")
    return texto


def data_ou_none(valor):
    if pd.isna(valor) or str(valor).strip() == "":
        return None
    return pd.to_datetime(valor, errors="raise").date()


def valor_ou_zero(valor) -> float:
    if pd.isna(valor) or str(valor).strip() == "":
        return 0.0
    return float(valor)


@router.get("")
def pagina_importacao(request: Request):
    return templates.TemplateResponse(
        "importar.html",
        {"request": request, "page_title": "Importar dados", "page_subtitle": "Envie uma planilha CSV ou Excel para alimentar o sistema.", "mensagem": None},
    )


@router.post("")
async def importar(
    request: Request,
    arquivo: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    nome = (arquivo.filename or "").lower()

    if arquivo.content_type not in TIPOS_PERMITIDOS:
        raise HTTPException(415, "Tipo de arquivo não permitido.")

    conteudo = await arquivo.read(settings.max_upload_mb * 1024 * 1024 + 1)
    if len(conteudo) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"Arquivo maior que {settings.max_upload_mb} MB.")

    try:
        if nome.endswith(".csv"):
            df = pd.read_csv(BytesIO(conteudo))
        elif nome.endswith((".xlsx", ".xls")):
            df = pd.read_excel(BytesIO(conteudo))
        else:
            raise HTTPException(400, "Envie um arquivo CSV ou Excel.")
    except HTTPException:
        raise
    except Exception as erro:
        raise HTTPException(400, "Não foi possível ler o arquivo enviado.") from erro

    if len(df.index) > LIMITE_LINHAS:
        raise HTTPException(400, f"A planilha excede o limite de {LIMITE_LINHAS:,} linhas.".replace(",", "."))

    df.columns = [str(c).strip().lower() for c in df.columns]
    faltantes = COLUNAS - set(df.columns)
    if faltantes:
        raise HTTPException(400, "Colunas obrigatórias ausentes: " + ", ".join(sorted(faltantes)))

    if df.empty:
        raise HTTPException(400, "A planilha não contém nenhuma linha de dados.")

    try:
        # Os departamentos são resolvidos em memória. A versão anterior fazia um
        # SELECT por linha da planilha, o que significava dezenas de milhares de
        # consultas em uma importação grande.
        existentes = {
            nome_dep: id_dep
            for id_dep, nome_dep in db.execute(select(Departamento.id, Departamento.nome))
        }

        nomes_planilha = {
            texto_seguro(valor, 100) for valor in df["departamento"].tolist()
        }
        novos = sorted(nomes_planilha - existentes.keys())
        if novos:
            db.add_all([Departamento(nome=nome_dep) for nome_dep in novos])
            db.flush()
            existentes.update(
                {
                    nome_dep: id_dep
                    for id_dep, nome_dep in db.execute(
                        select(Departamento.id, Departamento.nome).where(
                            Departamento.nome.in_(novos)
                        )
                    )
                }
            )

        registros = [
            Registro(
                departamento_id=existentes[texto_seguro(linha["departamento"], 100)],
                responsavel=texto_seguro(linha["responsavel"], 150),
                descricao=texto_seguro(linha["descricao"], 5000),
                status=texto_seguro(linha["status"], 50),
                prioridade=texto_seguro(linha["prioridade"], 30) or "Média",
                data_abertura=data_ou_none(linha["data_abertura"]),
                prazo=data_ou_none(linha["prazo"]),
                data_conclusao=data_ou_none(linha["data_conclusao"]),
                valor=valor_ou_zero(linha["valor"]),
            )
            for _, linha in df.iterrows()
        ]
        db.add_all(registros)
        inseridos = len(registros)

        registrar_auditoria(
            db,
            request,
            "importar_planilha",
            nome or "arquivo_sem_nome",
            detalhes=f"registros={inseridos}",
        )
        db.commit()
    except Exception as erro:
        db.rollback()
        raise HTTPException(400, "Falha na validação ou gravação da planilha.") from erro

    return templates.TemplateResponse(
        "importar.html",
        {
            "request": request,
            "page_title": "Importar dados",
            "page_subtitle": "Envie uma planilha CSV ou Excel para alimentar o sistema.",
            "mensagem": f"{inseridos} registros importados com sucesso.",
        },
    )
