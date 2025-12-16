
# Projeto de Automação de Relatórios TI/TP

Automatiza a **extração**, **tratamento**, **renderização** e **entrega** de relatórios mensais de atividades de docentes nos regimes **Tempo Integral (TI)** e **Tempo Parcial (TP)**, padronizando o layout e garantindo rastreabilidade e compliance.

---

## 📌 Contexto

Os relatórios eram produzidos manualmente, consumindo tempo e aumentando a chance de erros. Este projeto automatiza o fluxo (Canvas → CSV → PDF), facilita auditorias e mantém conformidade com critérios institucionais e regulatórios.

---

## 👥 Stakeholders

- Reitoria, Coordenações, Docentes, Secretaria Acadêmica

---

## 🚧 Status

Próximos passos incluem execução com distribuição.  
Arquivos de orquestração, transformação e renderização foram testados com sucesso nas rotinas principais.

---

## ⚙️ Visão Geral

Para **cada docente** (uma linha por docente no CSV tratado):

1. **Extrair** respostas do questionário do Canvas via API (gera link de report e download). 
2. **Tratar** CSV → normalizar colunas, datas e nomes, salvar como `;`-separado.
3. **Renderizar** overlay PDF em A4 com duas colunas, altura sob demanda para Q10, sem sobreposição.
4. **Mesclar** overlay com **template PDF** (background) na 1ª página e salvar em `final/`.
5. **Executar** em lote e monitorar via logs; preparar distribuição (Canvas Files API/e-mail).

---

## 🧰 Tecnologias

- **Python 3.13+**  
- **requests**, **certifi**, **python-dotenv** (Canvas / SSL / env)
- **pandas** (ETL CSV)
- **ReportLab** (overlay PDF, milímetros, tipografia)  
- **PyPDF2** (merge overlay + template)
- **logging**

---

## 🧱 Arquitetura & Fluxo

- **Extractor (src/main.py)**  
  - Busca assignments no Canvas para um **ano** informado; lista e seleciona uma assignment; solicita geração de report (student analysis) e baixa o arquivo. Usa `CANVAS_API_URL`, `course_id`, `Authorization: Bearer <token>` carregado de um ENV.

- **Transformer (src/transformer.py)**  
  - Lê CSV bruto com pré-definidos; normaliza headers, datas e nomes; Disponibilizando um DataFrame para a próxima etapa.

- **Renderer (src/render_pdf.py)**  
  - Registra fontes **(/fonts)**; usa `Paragraph + Frame` para texto com quebra automática.  
  - Grade de 15 linhas (duas colunas), desenhada **do topo para a base** da página; **Q10** tem altura sob demanda, evitando sobreposição.    
  - Gera overlay para **cada docente**.  
  - Mescla **em lote** os overlays com o template, salvando localmente o arquivo ".PDF" renderizado.

- **Template A4**  
  - Estrutura com cabeçalho, bloco do docente, cabeçalhos “Questões/Respostas” e rodapé/assinatura. Testado com merge de overlays.
---

## 📂 Estrutura de Pastas (armazenamento)

- **.../data/processed**: Armazena todos os arquivos processados(DF).
  - **.../processed/overlay**: Armazena todas overlays geradas.
  - **.../processed/final**: Arquivos PDF's renderizados.
- **.../data/raw**: Todos os arquivo brutos adquiridos via API.

## 🔐 Configuração

1. Crie `.env` na raiz com:
2. Confirme o `course_id` e a URL Canvas no `main.py`.
3. Instale as fontes em `/fonts` (OpenSans Condensed) — usadas no overlay.

## ▶️ Como Executar

1. **Orquestrador (uma execução de ponta-a-ponta):**   
  `python src/main.py`
2. Informe o ano do report quando solicitado.
3. Selecione a assignment listado.
4. O sistema vai pedir ao Canvas para gerar o report, baixar o arquivo, tratar o CSV, gerar um overlay e por fim mesclar overlays com o template e salvar em data/processed/final.

## 📝 Logs & Monitoramento

Logging configurado em todos os módulos; mensagens de status, erros e caminhos de saída são impressos durante a execução.

## ⚠️ Limitações & Próximos Passos

- Distribuição (Canvas Files API/e-mail) ainda não integrada; rodar localmente e publicar manualmente
- Inferência de Mes/Ano — hoje é passada pelo orquestrador e/ou safe_name; pode ser ampliada para ler da própria submitted quando safe_name não seguir o padrão.
- Centralização horizontal/vertical das questões/respostas (opcional): pode ser habilitada medindo altura do Paragraph e ajustando o Frame dinamicamente (patch disponibilizado).
- Erros e retries: considerar backoff para requisições Canvas e confirmação do status de report.

# 🤝 Contribuições

Por ora, projeto interno. Sugestões de melhoria podem ser registradas em issues privadas e serão revisadas