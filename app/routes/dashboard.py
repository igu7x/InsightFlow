from datetime import date

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import Select, case, func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Departamento, Registro
from app.templating import templates

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def aplicar_filtros(
    consulta: Select,
    data_inicial: date | None,
    data_final: date | None,
    departamento: str | None,
) -> Select:
    """Aplica os filtros da barra superior a qualquer consulta sobre Registro."""
    if data_inicial:
        consulta = consulta.where(Registro.data_abertura >= data_inicial)
    if data_final:
        consulta = consulta.where(Registro.data_abertura <= data_final)
    if departamento:
        consulta = consulta.where(Departamento.nome == departamento)
    return consulta


@router.get("")
def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    data_inicial: date | None = Query(default=None),
    data_final: date | None = Query(default=None),
    departamento: str | None = Query(default=None, max_length=100),
):
    departamento = (departamento or "").strip() or None
    if data_inicial and data_final and data_inicial > data_final:
        data_inicial, data_final = data_final, data_inicial

    def contar(*condicoes) -> int:
        consulta = select(func.count(Registro.id)).join(Departamento)
        consulta = aplicar_filtros(consulta, data_inicial, data_final, departamento)
        for condicao in condicoes:
            consulta = consulta.where(condicao)
        return db.scalar(consulta) or 0

    total = contar()
    concluidos = contar(Registro.status == "Concluído")
    atrasados = contar(Registro.status == "Atrasado")
    em_andamento = contar(Registro.status == "Em andamento")

    consulta_valor = select(func.coalesce(func.sum(Registro.valor), 0)).join(Departamento)
    valor_total = db.scalar(
        aplicar_filtros(consulta_valor, data_inicial, data_final, departamento)
    ) or 0

    taxa_conclusao = round((concluidos / total * 100), 1) if total else 0

    consulta_departamentos = (
        select(
            Departamento.nome,
            func.count(Registro.id).label("total"),
            func.sum(case((Registro.status == "Atrasado", 1), else_=0)).label("atrasados"),
        )
        .join(Registro)
        .group_by(Departamento.id, Departamento.nome)
        .order_by(func.count(Registro.id).desc())
    )
    por_departamento = db.execute(
        aplicar_filtros(consulta_departamentos, data_inicial, data_final, departamento)
    ).all()

    consulta_recentes = (
        select(Registro, Departamento.nome)
        .join(Departamento)
        .order_by(Registro.criado_em.desc())
        .limit(8)
    )
    recentes = db.execute(
        aplicar_filtros(consulta_recentes, data_inicial, data_final, departamento)
    ).all()

    # A lista do seletor mostra todos os departamentos, e não apenas os que
    # sobraram do filtro atual, para que sempre seja possível trocar a seleção.
    departamentos_disponiveis = db.scalars(
        select(Departamento.nome).order_by(Departamento.nome)
    ).all()

    filtros_ativos = bool(data_inicial or data_final or departamento)

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "page_title": "Dashboard executivo",
            "page_subtitle": "Acompanhe os principais indicadores da operação.",
            "total": total,
            "concluidos": concluidos,
            "atrasados": atrasados,
            "em_andamento": em_andamento,
            "valor_total": float(valor_total),
            "taxa_conclusao": taxa_conclusao,
            "por_departamento": por_departamento,
            "recentes": recentes,
            "departamentos_disponiveis": departamentos_disponiveis,
            "filtro_data_inicial": data_inicial.isoformat() if data_inicial else "",
            "filtro_data_final": data_final.isoformat() if data_final else "",
            "filtro_departamento": departamento or "",
            "filtros_ativos": filtros_ativos,
            "chart_departamentos": [item.nome for item in por_departamento],
            "chart_totais": [int(item.total or 0) for item in por_departamento],
            "chart_atrasados": [int(item.atrasados or 0) for item in por_departamento],
            "chart_status": [concluidos, em_andamento, atrasados],
        },
    )
