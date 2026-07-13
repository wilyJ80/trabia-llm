const queryForm = document.querySelector("#query-form");
const extractForm = document.querySelector("#extract-form");
const questionInput = document.querySelector("#question");
const answerContent = document.querySelector("#answer-content");
const sourcesList = document.querySelector("#sources-list");
const sourceCount = document.querySelector("#source-count");
const queryStatus = document.querySelector("#query-status");
const extractStatus = document.querySelector("#extract-status");
const extractResult = document.querySelector("#extract-result");
const extractValidation = document.querySelector("#extract-validation");
const extractConfidence = document.querySelector("#extract-confidence");
const extractFile = document.querySelector("#extract-file");
const extractFileLabel = document.querySelector("#extract-file-label");
const workflowStatus = document.querySelector("#workflow-status");
const chunksCount = document.querySelector("#chunks-count");
const llmStatus = document.querySelector("#llm-status");
const refreshHealthButton = document.querySelector("#refresh-health");

function setStatus(node, message, isError = false) {
  node.textContent = message;
  node.classList.toggle("error", isError);
}

function setBusy(form, isBusy) {
  form.querySelectorAll("button, input, select, textarea").forEach((field) => {
    field.disabled = isBusy;
  });
}

function renderSources(sources) {
  sourcesList.replaceChildren();
  sourceCount.textContent = sources.length.toString();

  sources.forEach((source) => {
    const item = document.createElement("li");
    const page = document.createElement("span");
    const claim = document.createElement("p");

    page.className = "source-page";
    page.textContent = `Pagina ${source.page ?? "N/A"}`;

    claim.className = "source-claim";
    claim.textContent = source.claim || "Fonte citada sem descricao.";

    item.append(page, claim);
    sourcesList.append(item);
  });
}

function valueOrEmpty(value) {
  if (Array.isArray(value)) {
    return value.length ? value : ["Nao identificado."];
  }
  return value || "Nao identificado.";
}

function createField(title, value, className = "") {
  const field = document.createElement("section");
  const heading = document.createElement("h3");
  const content = valueOrEmpty(value);

  field.className = `extract-field ${className}`.trim();
  heading.textContent = title;
  field.append(heading);

  if (Array.isArray(content)) {
    const list = document.createElement("ul");
    content.forEach((item) => {
      const listItem = document.createElement("li");
      listItem.textContent = item;
      list.append(listItem);
    });
    field.append(list);
    return field;
  }

  const paragraph = document.createElement("p");
  paragraph.textContent = content;
  field.append(paragraph);
  return field;
}

function renderExtraction(data) {
  const extraction = data.extraction || {};
  const summary = document.createElement("dl");
  const fieldGrid = document.createElement("div");
  const sourceField = createField(
    "Fontes",
    (extraction.sources || []).map((source) => `Pagina ${source.page ?? "N/A"}: ${source.claim}`),
    "full",
  );

  extractResult.replaceChildren();
  extractResult.classList.remove("empty-state");
  extractValidation.textContent = extraction.validation_status || "--";
  extractConfidence.textContent = extraction.confidence ? `confianca ${extraction.confidence}` : "--";

  summary.className = "extract-summary";
  [
    ["Contexto", `${data.context_chunks_used ?? 0} chunks`],
    ["Embedder", data.embedder_used || "--"],
    ["Fontes", (data.params_used?.sources || []).join(", ") || "--"],
  ].forEach(([label, value]) => {
    const item = document.createElement("div");
    const term = document.createElement("dt");
    const description = document.createElement("dd");
    term.textContent = label;
    description.textContent = value;
    item.append(term, description);
    summary.append(item);
  });

  fieldGrid.className = "extract-field-grid";
  [
    ["Tipo", extraction.document_type],
    ["Titulo", extraction.title],
    ["Evento principal", extraction.main_event],
    ["Datas", extraction.dates],
    ["Atores", extraction.actors],
    ["Organizacoes", extraction.organizations],
    ["Fatos", extraction.facts],
    ["Evidencias", extraction.evidence],
    ["Categorias", extraction.categories],
  ].forEach(([title, value]) => {
    fieldGrid.append(createField(title, value, Array.isArray(value) ? "full" : ""));
  });

  extractResult.append(summary, fieldGrid, sourceField);

  if (extraction.validation_errors?.length) {
    extractResult.append(createField("Problemas de validacao", extraction.validation_errors, "full"));
    extractResult.lastElementChild.classList.add("validation-list");
  }
}

async function parseResponse(response) {
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = payload.detail || `Erro HTTP ${response.status}`;
    throw new Error(Array.isArray(detail) ? detail.map((item) => item.msg).join("; ") : detail);
  }
  return payload;
}

async function refreshHealth() {
  refreshHealthButton.disabled = true;
  try {
    const payload = await fetch("/api/health").then(parseResponse);
    chunksCount.textContent = String(payload.chunks_count ?? 0);
    llmStatus.textContent = payload.llm_connected ? "OK" : "Falha";
  } catch (error) {
    chunksCount.textContent = "--";
    llmStatus.textContent = "Falha";
  } finally {
    refreshHealthButton.disabled = false;
  }
}

queryForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const formData = new FormData(queryForm);
  const payload = {
    question: String(formData.get("question") || "").trim(),
    top_k: Number(formData.get("top_k") || 5),
    embedder: String(formData.get("embedder") || "openai"),
  };

  if (!payload.question) {
    setStatus(queryStatus, "Pergunta vazia", true);
    return;
  }

  setBusy(queryForm, true);
  setStatus(queryStatus, "Consultando");
  answerContent.textContent = "Buscando contexto e gerando resposta...";
  answerContent.classList.add("empty-state");
  renderSources([]);

  try {
    const data = await fetch("/api/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then(parseResponse);

    answerContent.textContent = data.answer?.content || "O modelo nao retornou conteudo.";
    answerContent.classList.remove("empty-state");
    renderSources(data.answer?.sources || []);
    setStatus(queryStatus, data.embedder_used || payload.embedder);
  } catch (error) {
    answerContent.textContent = error.message;
    answerContent.classList.add("empty-state");
    setStatus(queryStatus, "Erro", true);
  } finally {
    setBusy(queryForm, false);
  }
});

extractFile.addEventListener("change", () => {
  extractFileLabel.textContent = extractFile.files[0]?.name || "Selecionar PDF";
});

// Track which submit button was clicked (more reliable than event.submitter)
let formSubmitMode = "ingest_extract";

extractForm.querySelectorAll("button[name=mode]").forEach((btn) => {
  btn.addEventListener("click", () => {
    formSubmitMode = btn.value;
  });
});

extractForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const sourceData = new FormData(extractForm);
  const mode = formSubmitMode;
  const file = extractFile.files[0];
  const text = String(sourceData.get("text") || "").trim();
  const embedder = String(sourceData.get("embedder") || "openai");

  if (!file && !text) {
    setStatus(extractStatus, "Envio vazio", true);
    setStatus(workflowStatus, "Selecione um PDF ou informe texto bruto.", true);
    return;
  }

  const payload = new FormData();
  if (file) {
    payload.append("file", file);
  }
  payload.append("text", text);
  payload.append("top_k", String(sourceData.get("top_k") || 5));
  payload.append("embedder", embedder);

  setBusy(extractForm, true);
  setStatus(extractStatus, "Processando");
  setStatus(workflowStatus, "");
  extractValidation.textContent = "--";
  extractConfidence.textContent = "--";
  extractResult.textContent = "Preparando o fluxo do documento...";
  extractResult.classList.add("empty-state");

  try {
    if (mode === "ingest_extract" && file) {
      const ingestPayload = new FormData();
      ingestPayload.append("file", file);
      ingestPayload.append("embedder", embedder);

      setStatus(workflowStatus, "1/2 Ingerindo PDF na base vetorial...");
      await fetch("/api/ingest", {
        method: "POST",
        body: ingestPayload,
      }).then(parseResponse);

      await refreshHealth();
    } else if (mode === "ingest_extract" && !file) {
      setStatus(workflowStatus, "Texto bruto nao passa por ingestao; extraindo diretamente.");
    } else {
      setStatus(workflowStatus, "Extraindo sem nova ingestao.");
    }

    setStatus(workflowStatus, file && mode === "ingest_extract" ? "2/2 Extraindo campos..." : "Extraindo campos...");
    const data = await fetch("/api/extract", {
      method: "POST",
      body: payload,
    }).then(parseResponse);

    renderExtraction(data);
    setStatus(extractStatus, "Concluido");
    setStatus(workflowStatus, file && mode === "ingest_extract" ? "PDF ingerido e extraido." : "Extracao concluida.");
  } catch (error) {
    extractResult.textContent = error.message;
    extractResult.classList.add("empty-state");
    setStatus(extractStatus, "Erro", true);
    setStatus(workflowStatus, error.message, true);
  } finally {
    setBusy(extractForm, false);
  }
});

document.querySelectorAll("[data-example]").forEach((button) => {
  button.addEventListener("click", () => {
    questionInput.value = button.dataset.example;
    questionInput.focus();
  });
});

refreshHealthButton.addEventListener("click", refreshHealth);
refreshHealth();
