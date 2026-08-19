# InsightFlow IA: análise automatizada de dados empresariais com inteligência artificial

Sistema web que transforma planilhas operacionais em indicadores, análises escritas por IA e relatórios arquivados, com controles de segurança e privacidade.

| | |
|---|---|
| **Versão do sistema** | 0.2.0 — MVP funcional |
| **Área** | Análise de dados e IA aplicada |
| **Natureza** | Pesquisa aplicada |
| **Data** | Agosto de 2026 |

---

## 2. Resumo

Micro e pequenas empresas registram sua rotina em planilhas, mas raramente conseguem extrair decisões desses arquivos: contar tarefas atrasadas por setor ou somar valores parados exige um trabalho manual que ninguém repete toda semana. O InsightFlow IA foi desenvolvido para resolver esse problema. Trata-se de um sistema web que recebe uma planilha em CSV ou Excel, valida e trata os dados com a biblioteca Pandas, armazena tudo em um banco MySQL, calcula indicadores de desempenho e os exibe em um painel com gráficos e filtros. A partir desses mesmos dados, o sistema envia um resumo agregado por departamento a um modelo de linguagem da OpenAI, que redige uma análise com pontos de atenção e recomendações; essa análise é então exportada como arquivo Markdown, formando uma base de conhecimento consultável. O desenvolvimento seguiu abordagem incremental em Python com o framework FastAPI, e incorporou desde o início controles técnicos de privacidade — criptografia dos textos armazenados, pseudonimização da trilha de auditoria, envio de dados apenas agregados à IA e política de retenção. O impacto esperado é reduzir o intervalo entre *ter o dado* e *entender o dado*, oferecendo a uma empresa de pequeno porte um recurso de análise que normalmente exigiria ferramentas caras de BI.

---

## 3. Objetivo Geral

Desenvolver um sistema web capaz de transformar planilhas operacionais de uma empresa em indicadores de desempenho e análises geradas por inteligência artificial, de forma automatizada e com controles de proteção de dados pessoais.

---

## 4. Objetivos Específicos

1. **Importar planilhas com validação.** Aceitar arquivos CSV, XLS e XLSX, conferindo tipo, tamanho, colunas obrigatórias e formato dos dados antes de gravar qualquer informação.
2. **Modelar e alimentar um banco de dados relacional.** Estruturar as informações em MySQL com relacionamento entre departamentos e registros, gravando cada importação em transação única.
3. **Calcular e exibir indicadores.** Apresentar total de registros, taxa de conclusão, quantidade de atrasos e valor acumulado, com gráficos por departamento e filtros por período e setor.
4. **Integrar um assistente de inteligência artificial.** Permitir perguntas em linguagem natural sobre os dados, enviando ao modelo apenas informações agregadas, sem dados que identifiquem pessoas.
5. **Exportar análises em formato aberto.** Gravar as respostas como arquivos Markdown compatíveis com o Obsidian, criando um histórico consultável.
6. **Implementar controles de segurança e privacidade.** Aplicar criptografia, pseudonimização, limite de requisições, cabeçalhos de segurança, usuário de banco com privilégios reduzidos e rotina de descarte por prazo.
7. **Documentar o sistema.** Produzir documentação de instalação, execução e segurança, além da documentação automática da API.

---

## 5. Justificativa

### O problema

A planilha é a ferramenta de gestão mais usada nas empresas pequenas, e também a mais limitada. Ela guarda bem, mas responde mal. Uma pergunta simples como "qual setor está acumulando mais atrasos?" exige filtrar, contar e comparar manualmente — um trabalho que precisa ser refeito a cada atualização do arquivo. Na prática, ele não é feito, e os dados acabam servindo apenas como registro histórico.

As ferramentas que resolveriam isso — plataformas de Business Intelligence — costumam ter custo de licença e exigir conhecimento técnico para configurar, o que as coloca fora do alcance de uma empresa de pequeno porte.

### A oportunidade

Dois fatores tornam viável hoje um sistema que antes seria caro: bibliotecas maduras e gratuitas de tratamento de dados em Python, e o acesso a modelos de linguagem por API, que permitem gerar análises escritas a partir de números sem que seja necessário programar cada regra de interpretação.

### Impacto esperado

- Reduzir de horas para segundos o tempo de apuração dos indicadores.
- Permitir que a análise seja repetida a cada atualização da planilha, e não apenas uma vez.
- Tornar o resultado compreensível para quem não trabalha com dados, por meio de texto em linguagem natural.
- Preservar o histórico das análises, permitindo comparar períodos.

### Benefícios acadêmicos

O projeto integra em um único produto conteúdos normalmente estudados de forma isolada: modelagem de banco de dados, desenvolvimento web, tratamento de dados, consumo de API externa, segurança da informação e legislação de proteção de dados. A necessidade de fazer essas peças conversarem entre si é o principal ganho de aprendizado.

---

## 6. Fundamentação Teórica

### Pipeline de dados (ETL)

O sistema segue a lógica clássica de Extração, Transformação e Carga: os dados são extraídos da planilha, transformados e validados pelo Pandas, e carregados no banco relacional. Essa separação em etapas é o que permite rejeitar dados inconsistentes antes que contaminem as análises seguintes.

### Indicadores de desempenho

O painel se apoia no conceito de KPI (*Key Performance Indicator*): poucas medidas escolhidas por sua capacidade de sinalizar o estado da operação. Foram adotados quatro — volume total, taxa de conclusão, volume de atrasos e valor acumulado — por serem suficientes para orientar decisão sem exigir interpretação especializada.

### Arquitetura web e ORM

A aplicação usa o framework FastAPI, baseado no padrão de rotas HTTP e na especificação OpenAPI, que gera documentação da interface automaticamente. O acesso ao banco é feito por meio de um ORM (SQLAlchemy), que representa tabelas como classes Python — reduzindo a escrita manual de SQL e, com isso, a superfície para erros e para injeção de comandos.

### Modelos de linguagem e ancoragem em dados

A análise textual é produzida por um LLM (*Large Language Model*). O risco conhecido desses modelos é a alucinação: a geração de informação plausível porém falsa. A técnica adotada para mitigá-lo é a ancoragem — o modelo recebe os dados junto com a pergunta e instruções explícitas para usar somente aquele conteúdo e declarar quando a informação for insuficiente.

### Proteção de dados e LGPD

A Lei nº 13.709/2018 orienta as decisões de projeto por meio de quatro princípios aplicados diretamente no código:

- **Minimização** — enviar ao serviço externo apenas o necessário, no caso, dados agregados.
- **Pseudonimização** — registrar o autor das ações como hash HMAC-SHA256, e não como endereço identificável.
- **Segurança** — cifrar em repouso os textos armazenados, usando criptografia simétrica Fernet.
- **Retenção limitada** — descartar registros após um prazo definido, em vez de mantê-los indefinidamente.

Complementa esses princípios o conceito de menor privilégio, da segurança da informação: a aplicação acessa o banco com um usuário que só pode manipular linhas, sem permissão para alterar a estrutura do banco.

### Base de conhecimento em Markdown

A exportação usa Markdown com metadados e links internos, formato adotado pelo Obsidian. A escolha segue a ideia de notas interligadas: em vez de relatórios isolados, as análises formam uma rede navegável, e permanecem legíveis em qualquer editor de texto por serem arquivos abertos.

---

## 7. Metodologia

### Abordagem

Pesquisa aplicada, de natureza predominantemente qualitativa quanto ao desenvolvimento, com verificação quantitativa dos resultados — os indicadores calculados pelo sistema são conferidos contra a contagem manual da planilha de origem.

O desenvolvimento foi incremental, organizado em versões funcionais: primeiro um fluxo mínimo completo (importar, armazenar, exibir), depois a integração com IA, e por fim a camada de segurança e privacidade. Cada etapa foi testada antes do início da seguinte.

### Ferramentas e tecnologias

| Camada | Tecnologia | Função |
|---|---|---|
| Linguagem | Python 3.11+ | Base de todo o backend |
| Servidor web | FastAPI + Uvicorn | Rotas, validação e documentação automática |
| Banco de dados | MySQL 8 | Armazenamento relacional |
| Acesso a dados | SQLAlchemy + PyMySQL | Mapeamento objeto-relacional |
| Tratamento de dados | Pandas + OpenPyXL | Leitura e validação das planilhas |
| Interface | Jinja2, Bootstrap, Chart.js | Páginas, layout e gráficos |
| Inteligência artificial | API da OpenAI | Geração das análises textuais |
| Segurança | Cryptography (Fernet), HMAC-SHA256 | Criptografia e pseudonimização |
| Saída | Markdown / Obsidian | Arquivamento das análises |

### Fontes de dados

O sistema não coleta dados de terceiros. Ele processa planilhas fornecidas pelo próprio usuário, com nove colunas obrigatórias: departamento, responsável, descrição, status, prioridade, data de abertura, prazo, data de conclusão e valor.

Para desenvolvimento e testes foram utilizadas **planilhas com dados fictícios**, incluindo um arquivo-modelo distribuído junto ao sistema e uma base gerada com cinco mil linhas para verificação de desempenho. Nenhum dado real de pessoa ou empresa foi utilizado.

### Cronograma

| Etapa | Atividades | Duração | Situação |
|---|---|---|---|
| 1. Levantamento | Definição do problema, escopo e tecnologias | 1 semana | Concluída |
| 2. Modelagem | Modelo de dados, criação do banco e estrutura do projeto | 1 semana | Concluída |
| 3. Importação | Upload, validação e gravação com Pandas | 2 semanas | Concluída |
| 4. Painel | Indicadores, gráficos e filtros | 2 semanas | Concluída |
| 5. Assistente de IA | Integração com a API, agregação e histórico | 2 semanas | Concluída |
| 6. Exportação | Geração dos arquivos Markdown | 1 semana | Concluída |
| 7. Segurança e LGPD | Criptografia, auditoria, retenção e privilégios do banco | 2 semanas | Concluída |
| 8. Testes e correções | Verificação do fluxo completo e correção de falhas | 1 semana | Concluída |
| 9. Documentação e entrega | Manuais, apresentação e revisão final | 1 semana | Em andamento |

---

## 8. Entregáveis

| Entregável | Descrição | Situação |
|---|---|---|
| Aplicação web | Sistema completo executável localmente, com cinco telas | Entregue |
| Banco de dados | Seis tabelas modeladas, com scripts de criação e migração | Entregue |
| Módulo de importação | Upload validado de CSV e Excel | Entregue |
| Painel de indicadores | KPIs, dois gráficos e filtros por data e departamento | Entregue |
| Assistente de IA | Interface de perguntas com histórico armazenado | Entregue |
| Exportação Markdown | Relatórios com metadados e links internos | Entregue |
| Camada de segurança | Criptografia, auditoria, retenção e canal do titular | Entregue |
| Documentação | README, guia de execução e documento de segurança e LGPD | Entregue |
| Documentação da API | Interface Swagger gerada automaticamente | Entregue |
| Apresentação final | Slides e demonstração ao vivo do sistema | Em preparação |

### Métricas de sucesso

- **Correção dos indicadores.** Os números do painel devem coincidir com a contagem manual da planilha importada.
- **Confiabilidade da importação.** Planilhas fora do padrão devem ser recusadas com mensagem clara, sem gravar dados parciais.
- **Desempenho.** Importar cinco mil linhas em menos de dez segundos e carregar o painel em menos de um segundo.
- **Fidelidade da análise.** A resposta da IA não deve conter números divergentes dos apresentados no painel.
- **Privacidade.** Nenhum dado que identifique pessoas deve ser enviado ao serviço externo.
- **Fluxo completo.** Percorrer importação, painel, análise e exportação sem erros.

> **Resultado da verificação:** nos testes realizados, a importação de cinco mil linhas levou 3,3 segundos e o painel carregou em 0,03 segundo — ambos dentro da meta. O fluxo completo foi percorrido sem erros, e os indicadores conferiram com a contagem manual.

---

## 9. Recursos Necessários

### Hardware

Um computador comum é suficiente. O sistema foi desenvolvido e testado em máquina com Windows 11, e não exige placa de vídeo dedicada nem servidor — o processamento pesado de IA ocorre na infraestrutura da OpenAI.

### Software e licenças

| Item | Licença | Custo |
|---|---|---|
| Python, FastAPI, SQLAlchemy, Pandas | Código aberto | Gratuito |
| MySQL Community Server | GPL | Gratuito |
| Bootstrap, Chart.js, SweetAlert2 | MIT | Gratuito |
| Visual Studio Code, Git | Gratuito | Gratuito |
| Obsidian | Uso pessoal gratuito | Gratuito |
| API da OpenAI | Serviço pago por uso | Variável |

### Orçamento

O único custo do projeto é a API da OpenAI, cobrada por volume de texto processado. Como o sistema envia apenas um resumo agregado — poucas linhas por pergunta — o consumo é baixo, na casa de poucos centavos por consulta. Para fins de demonstração acadêmica, o custo é desprezível, e o sistema também funciona sem a chave, exibindo os dados agregados sem a redação da análise.

---

## 10. Equipe

*(a preencher)*

---

## 11. Riscos e Desafios

| Risco | Consequência | Como foi tratado |
|---|---|---|
| Indisponibilidade ou custo da API de IA | Assistente deixa de responder | Modo demonstração: sem a chave, o sistema exibe o resumo dos dados e continua funcionando |
| Alucinação do modelo de linguagem | Análise com números inventados | Instruções restritivas no prompt e conferência possível contra o painel |
| Exposição de dados pessoais ao serviço externo | Violação de privacidade | Envio limitado a totais por departamento, sem nomes ou descrições |
| Planilha fora do padrão | Dados incorretos no banco | Validação de colunas, tipos e datas antes da gravação, com transação única |
| Perda da chave de criptografia | Conversas e relatórios ilegíveis de forma definitiva | Documentado como aviso crítico; a chave deve ser copiada e guardada fora do projeto |
| Atualização de bibliotecas quebrando o sistema | Aplicação deixa de iniciar | Versões com limite superior fixado no arquivo de dependências |
| Ausência de autenticação de usuários | Qualquer pessoa com acesso à máquina abre o sistema | Limitação reconhecida; mitigada por uso local e por chave administrativa nas rotinas sensíveis. Login previsto para a próxima versão |

### Principal desafio técnico

O ponto mais delicado do projeto foi conciliar duas exigências opostas: a IA precisa de contexto para produzir uma análise útil, mas quanto mais contexto recebe, mais dados saem do ambiente local. A solução adotada — agregar antes de enviar — preserva a utilidade da resposta, já que perguntas de gestão tratam de tendências por setor, e não de registros individuais.

---

## 12. Considerações Finais

O InsightFlow IA atingiu o objetivo proposto: existe hoje um sistema funcional que percorre todo o caminho entre a planilha e o relatório analisado, com os controles de privacidade implementados desde o início e não acrescentados ao final. Os testes de desempenho e de integridade dos indicadores confirmaram as metas estabelecidas.

O aprendizado central do projeto não esteve em nenhuma tecnologia isolada, mas na integração entre elas — e, sobretudo, na constatação de que decisões de privacidade precisam ser tomadas no momento do desenho da solução. A escolha de agregar os dados antes de enviá-los à IA, por exemplo, seria custosa de implementar depois de o sistema estar pronto.

### Possibilidades de continuidade

- **Autenticação e perfis de acesso**, com permissões distintas para administrador, gestor e usuário — a evolução mais necessária.
- **Testes automatizados** com Pytest, garantindo que alterações futuras não quebrem o que já funciona.
- **Migrações versionadas** com Alembic, para controlar a evolução do banco de dados.
- **Edição de registros pela interface**, sem necessidade de reimportar a planilha.
- **Comparação entre períodos**, permitindo à IA analisar a evolução dos indicadores ao longo do tempo.
- **Publicação em servidor** com HTTPS, backup automatizado e monitoramento.

> **Observação sobre conformidade:** os controles implementados são de natureza técnica. A adequação plena à LGPD exige também definição de base legal e finalidade, política de privacidade publicada, designação de encarregado e plano de resposta a incidentes — providências de caráter jurídico e organizacional, fora do escopo deste projeto.

---

*Documento elaborado a partir do sistema InsightFlow IA em sua versão 0.2.0. Os resultados de desempenho citados foram medidos em ambiente local com dados fictícios.*
