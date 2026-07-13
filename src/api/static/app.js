// ============================================
// Trabia LLM — Frontend Application
// ============================================

// --- DOM refs ---
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
const fileDropZone = document.querySelector("#file-drop-zone");
const workflowStatus = document.querySelector("#workflow-status");
const chunksOpenaiCount = document.querySelector("#chunks-openai-count");
const chunksSpacyCount = document.querySelector("#chunks-spacy-count");
const llmStatus = document.querySelector("#llm-status");
const refreshHealthButton = document.querySelector("#refresh-health");
const embedderSelects = document.querySelectorAll('select[name="embedder"]');
const healthDot = document.querySelector("#health-dot");
const healthTimestamp = document.querySelector("#health-timestamp");
const toastContainer = document.querySelector("#toast-container");
const extractStepper = document.querySelector("#extract-stepper");
const loadingSpinner = document.querySelector("#loading-spinner");
const primaryActionLabel = document.querySelector("#primary-action-label");
const inputModeToggle = document.querySelector(".input-mode-toggle");

// ============================================
// Input Mode Toggle (PDF / Texto)
// ============================================

let currentInputMode = "file";
const inputSections = document.querySelectorAll("[data-input-mode]");

function setInputMode(mode) {
  currentInputMode = mode;

  // Update toggle buttons
  inputModeToggle?.querySelectorAll(".toggle-btn").forEach((btn) => {
    const isActive = btn.dataset.mode === mode;
    btn.classList.toggle("active", isActive);
    btn.setAttribute("aria-checked", String(isActive));
  });

  // Show/hide input sections
  inputSections.forEach((section) => {
    if (section.dataset.inputMode === mode) {
      section.hidden = false;
      section.removeAttribute("hidden");
    } else {
      section.hidden = true;
    }
  });

  // Update primary action button text
  if (primaryActionLabel) {
    primaryActionLabel.textContent =
      mode === "file" ? "Ingerir e extrair PDF" : "Extrair texto";
  }
}

// Toggle button click handlers
inputModeToggle?.addEventListener("click", (event) => {
  const btn = event.target.closest(".toggle-btn");
  if (!btn || btn.classList.contains("active")) return;
  setInputMode(btn.dataset.mode);
});

// Also support keyboard (Enter/Space) on toggle buttons via role="radio"
inputModeToggle?.addEventListener("keydown", (event) => {
  const btn = event.target.closest(".toggle-btn");
  if (!btn || btn.classList.contains("active")) return;
  if (event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    setInputMode(btn.dataset.mode);
  }
});

// ============================================
// Toast Notifications
// ============================================

function showToast(message, type = "info", duration = 4000) {
  const icons = {
    success: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>`,
    error: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>`,
    info: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`,
  };

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span class="toast-icon">${icons[type] || icons.info}</span>
    <span class="toast-message">${message}</span>
    <button class="toast-close" aria-label="Fechar">&times;</button>
  `;

  toast.querySelector(".toast-close").addEventListener("click", () => {
    toast.classList.remove("show");
    setTimeout(() => toast.remove(), 280);
  });

  toastContainer.append(toast);

  requestAnimationFrame(() => {
    toast.classList.add("show");
  });

  if (duration > 0) {
    setTimeout(() => {
      toast.classList.remove("show");
      setTimeout(() => toast.remove(), 280);
    }, duration);
  }
}

// ============================================
// Progress Stepper
// ============================================

function setProgress(step) {
  if (!extractStepper) return;
  extractStepper.hidden = false;
  extractStepper.removeAttribute("aria-hidden");

  const steps = extractStepper.querySelectorAll(".stepper-step");
  const lines = extractStepper.querySelectorAll(".stepper-line");

  steps.forEach((s, i) => {
    const num = i + 1;
    s.classList.remove("active", "done");
    if (num < step) s.classList.add("done");
    else if (num === step) s.classList.add("active");
  });

  lines.forEach((line, i) => {
    line.classList.toggle("done", i + 1 < step);
  });
}

function resetStepper() {
  if (!extractStepper) return;
  extractStepper.hidden = true;
  extractStepper.setAttribute("aria-hidden", "true");
  extractStepper.querySelectorAll(".stepper-step, .stepper-line").forEach((el) => {
    el.classList.remove("active", "done");
  });
}

// ============================================
// Utility
// ============================================

function getSelectedEmbedder() {
  const value = document.querySelector('select[name="embedder"]')?.value || "openai";
  return value === "none" ? "openai" : value;
}

function syncEmbedders(value) {
  if (value === "none") return;
  embedderSelects.forEach((select) => {
    if (select.value === "none") return;
    select.value = value;
  });
}

function setStatus(node, message, isError = false) {
  node.textContent = message;
  node.classList.toggle("error", isError);
}

function setBusy(form, isBusy) {
  form.querySelectorAll("button, input, select, textarea").forEach((field) => {
    field.disabled = isBusy;
  });
}

// ============================================
// Source list rendering
// ============================================

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

// ============================================
// Extract result rendering
// ============================================

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

  if (extraction.inferred_fields?.length) {
    extractResult.append(
      createField("Campos inferidos por regra", extraction.inferred_fields, "full"),
    );
  }

  if (extraction.validation_errors?.length) {
    extractResult.append(createField("Problemas de validacao", extraction.validation_errors, "full"));
    extractResult.lastElementChild.classList.add("validation-list");
  }
}

// ============================================
// Parse HTTP response
// ============================================

async function parseResponse(response) {
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = payload.detail || `Erro HTTP ${response.status}`;
    throw new Error(Array.isArray(detail) ? detail.map((item) => item.msg).join("; ") : detail);
  }
  return payload;
}

// ============================================
// Health refresh
// ============================================

async function refreshHealth() {
  const embedder = getSelectedEmbedder();
  refreshHealthButton.disabled = true;
  try {
    const payload = await fetch(`/api/health?embedder=${encodeURIComponent(embedder)}`).then(
      parseResponse,
    );
    chunksOpenaiCount.textContent = String(payload.chunks_by_embedder?.openai ?? 0);
    chunksSpacyCount.textContent = String(payload.chunks_by_embedder?.spacy ?? 0);
    llmStatus.textContent = payload.llm_connected ? "OK" : "Falha";
    llmStatus.style.color = payload.llm_connected ? "var(--green)" : "var(--red)";

    if (healthDot) {
      healthDot.className = "health-dot";
      healthDot.classList.add(payload.llm_connected ? "online" : "offline");
    }

    if (healthTimestamp) {
      healthTimestamp.textContent = `Atualizado ${new Date().toLocaleTimeString("pt-BR")}`;
    }

    return payload;
  } catch (error) {
    chunksOpenaiCount.textContent = "--";
    chunksSpacyCount.textContent = "--";
    llmStatus.textContent = "Falha";
    llmStatus.style.color = "var(--red)";
    if (healthDot) {
      healthDot.className = "health-dot offline";
    }
    return null;
  } finally {
    refreshHealthButton.disabled = false;
  }
}

// ============================================
// Query form submit
// ============================================

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
    showToast("Digite uma pergunta antes de consultar.", "error");
    return;
  }

  setBusy(queryForm, true);
  setStatus(queryStatus, "Consultando");
  answerContent.textContent = "Buscando contexto e gerando resposta...";
  answerContent.classList.add("empty-state");
  renderSources([]);

  if (loadingSpinner) loadingSpinner.hidden = false;

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
    showToast("Consulta concluida com sucesso.", "success");
  } catch (error) {
    answerContent.textContent = error.message;
    answerContent.classList.add("empty-state");
    setStatus(queryStatus, "Erro", true);
    showToast(error.message, "error", 6000);
  } finally {
    setBusy(queryForm, false);
    if (loadingSpinner) loadingSpinner.hidden = true;
  }
});

// ============================================
// File drop visual feedback
// ============================================

extractFile.addEventListener("change", () => {
  const file = extractFile.files[0];
  extractFileLabel.textContent = file?.name || "Selecionar PDF";
  fileDropZone?.classList.toggle("has-file", !!file);
});

fileDropZone?.addEventListener("dragover", (event) => {
  event.preventDefault();
  fileDropZone.classList.add("drag-over");
});

fileDropZone?.addEventListener("dragleave", () => {
  fileDropZone.classList.remove("drag-over");
});

fileDropZone?.addEventListener("drop", (event) => {
  event.preventDefault();
  fileDropZone.classList.remove("drag-over");
  const files = event.dataTransfer?.files;
  if (files?.length) {
    extractFile.files = files;
    extractFile.dispatchEvent(new Event("change"));
  }
});

// ============================================
// Extract form — track submit mode
// ============================================

let formSubmitMode = "ingest_extract";

extractForm.querySelectorAll("button[name=mode]").forEach((btn) => {
  btn.addEventListener("click", () => {
    formSubmitMode = btn.value;
  });
});

// ============================================
// Extract form submit
// ============================================

extractForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const sourceData = new FormData(extractForm);
  const mode = formSubmitMode;
  const file = extractFile.files[0];
  const text = String(sourceData.get("text") || "").trim();
  const embedder = String(sourceData.get("embedder") || "openai");

  if (currentInputMode === "file" && !file && !text) {
    setStatus(extractStatus, "Envio vazio", true);
    setStatus(workflowStatus, "Selecione um PDF para ingerir.", true);
    showToast("Selecione um PDF para ingerir.", "error");
    return;
  }

  if (currentInputMode === "text" && !text) {
    setStatus(extractStatus, "Texto vazio", true);
    setStatus(workflowStatus, "Informe o texto bruto para extrair.", true);
    showToast("Cole o texto bruto para extrair.", "error");
    return;
  }

  const payload = new FormData();
  if (file) payload.append("file", file);
  payload.append("text", text);
  payload.append("top_k", String(sourceData.get("top_k") || 5));
  payload.append("embedder", embedder);

  setBusy(extractForm, true);
  setStatus(extractStatus, "Processando");
  setStatus(workflowStatus, "");
  extractValidation.textContent = "--";
  extractConfidence.textContent = "--";
  extractResult.textContent = "";
  extractResult.classList.add("empty-state");

  try {
    if (mode === "ingest_extract" && file) {
      // Step 1: Ingest
      setProgress(1);
      setStatus(workflowStatus, "Passo 1/2: Ingerindo PDF na base vetorial...");

      const ingestPayload = new FormData();
      ingestPayload.append("file", file);
      ingestPayload.append("embedder", embedder);
      ingestPayload.append("chunk_size", String(sourceData.get("chunk_size") || 2000));
      ingestPayload.append("chunk_overlap", String(sourceData.get("chunk_overlap") || 200));
      ingestPayload.append(
        "reset_collection",
        sourceData.get("reset_collection") === "on" ? "true" : "false",
      );

      await fetch("/api/ingest", {
        method: "POST",
        body: ingestPayload,
      }).then(parseResponse);

      setProgress(2);
      await refreshHealth();
      showToast("PDF ingerido com sucesso!", "success");
    } else if (mode === "ingest_extract" && !file) {
      setProgress(2);
      setStatus(workflowStatus, "Texto bruto nao passa por ingestao; extraindo diretamente.");
    } else {
      setProgress(2);
      setStatus(workflowStatus, "Extraindo sem nova ingestao.");
    }

    setStatus(workflowStatus, file && mode === "ingest_extract"
      ? "Passo 2/2: Extraindo campos do documento..."
      : "Extraindo campos...");

    const data = await fetch("/api/extract", {
      method: "POST",
      body: payload,
    }).then(parseResponse);

    renderExtraction(data);
    setProgress(3);
    setStatus(extractStatus, "Concluido");
    setStatus(workflowStatus, file && mode === "ingest_extract"
      ? "PDF ingerido e extraido com sucesso."
      : "Extracao concluida.");
    showToast("Documento extraido com sucesso!", "success");
  } catch (error) {
    extractResult.textContent = error.message;
    extractResult.classList.add("empty-state");
    setStatus(extractStatus, "Erro", true);
    setStatus(workflowStatus, error.message, true);
    showToast(error.message, "error", 6000);
    resetStepper();
  } finally {
    setBusy(extractForm, false);
  }
});

// ============================================
// Example prompt buttons
// ============================================

document.querySelectorAll("[data-example]").forEach((button) => {
  button.addEventListener("click", () => {
    questionInput.value = button.dataset.example;
    questionInput.focus();
  });
});

// ============================================
// Embedder sync & health refresh
// ============================================

refreshHealthButton.addEventListener("click", refreshHealth);

embedderSelects.forEach((select) => {
  select.addEventListener("change", () => {
    syncEmbedders(select.value);
    refreshHealth();
  });
});

// Initial health load
refreshHealth();
