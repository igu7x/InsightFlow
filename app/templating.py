"""Objeto de templates compartilhado por toda a aplicação.

As rotas usavam Jinja2Templates(directory="app/templates"), um caminho
relativo ao diretório de onde o servidor foi iniciado. Isso quebrava as
páginas sempre que o uvicorn era executado de fora da raiz do projeto.
Aqui o caminho é resolvido a partir do próprio arquivo, e uma única
instância é reaproveitada em todas as rotas.
"""

from pathlib import Path

from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent

templates = Jinja2Templates(directory=BASE_DIR / "templates")
