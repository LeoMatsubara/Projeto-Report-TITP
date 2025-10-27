# Projeto de Automação de Relatórios TI/TP

Este projeto visa automatizar a geração e distribuição dos relatórios TI/TP, garantindo padronização, rastreabilidade e conformidade com critérios exigidos pelo MEC.

---

## 📌 Contexto

Atualmente, os relatórios TI/TP são elaborados manualmente, o que torna o processo moroso, suscetível a erros e sem padronização. Este projeto busca automatizar essa tarefa, garantindo confiabilidade nos dados apresentados e conformidade com os critérios do MEC.

---

## 👥 Stakeholders

- Reitoria
- Coordenação
- Docentes
- Secretaria Acadêmica

---

## 🚧 Status

[Em desenvolvimento... ↻...↺]
---

## ⚙️ Visão Geral do Projeto

### Para cada docente (campo `sis_user`):

1. Extrair respostas do questionário do Canvas (CSV ou JSON) via API.
2. Tratar e agregar os dados (por pergunta, percentuais, média, etc).
3. Renderizar um PDF estilizado (semelhante ao da CPA) — um por docente ou consolidado.
4. Salvar localmente e disponibilizar (upload via Canvas API ou envio por e-mail).
5. Executar automaticamente (em lote), com logs, retries e monitoramento.

### Para cada mês:

1. Renderizar um PDF macro consolidado mensal.
2. Salvar localmente e/ou em nuvem.
3. Executar após a execução granular.

---

## 🧰 Tecnologias

### Linguagem
- Python 3.10+

### Bibliotecas
- requests
- canvasapi (opcional)
- pandas
- numpy
- Jinja2
- WeasyPrint ou pdfkit/wkhtmltopdf ou ReportLab
- matplotlib
- openpyxl
- pytest
- loguru ou structlog / logging
- python-dotenv / dynaconf
- boto3 (se usar S3)
- sendgrid (se enviar por API)
- docker

### Infraestrutura / Serviços
- Servidor Linux com Docker ou AWS/GCP/Azure
- PostgreSQL (opcional) para histórico de execuções e metadados
- Redis + Celery (para processamento assíncrono em larga escala)
- GitHub/GitLab + CI (GitHub Actions)

---

## 🧱 Arquitetura e Fluxo

🔹 **Scheduler**: cron / GitHub Actions / Airflow  
🔹 **Extractor**: Canvas API → CSV/JSON → `/data/raw`  
🔹 **Transformer**: pandas → DataFrame normalizado  
🔹 **Renderer**: Jinja2 + gráficos → PDF  
🔹 **Uploader**: Canvas Files API ou e-mail  
🔹 **Recorder**: grava status em banco/log  
🔹 **Alert**: notificação via Slack/e-mail em caso de erro

---

## 🛠️ Instalação

Em breve será disponibilizado o passo a passo para instalação e execução local do projeto.

---

## ▶️ Como Usar

A documentação de uso será incluída após definição dos fluxos finais.

---

## 🤝 Contribuições

✖️❌✖️❌✖️
