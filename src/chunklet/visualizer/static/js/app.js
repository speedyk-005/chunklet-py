// Main application state
let state = {
    originalText: '',
    chunksData: [],
    overlaps: [],
    activeChunkId: null,
    highlightedChunks: new Set(),
    showOverlaps: false,
    uploadedFileName: '',
    currentMode: 'document'
};

// Toast timeout tracker
let toastTimeoutId = null;

// DOM Elements
const elements = {
    fileInput: document.getElementById('fileInput'),
    uploadArea: document.getElementById('uploadArea'),
    uploadContent: document.getElementById('uploadContent'),
    browseBtn: document.getElementById('browseBtn'),
    processBtn: document.getElementById('processBtn'),
    resultsSection: document.getElementById('resultsSection'),
    textDisplay: document.getElementById('textDisplay'),
    totalChunksElem: document.getElementById('totalChunks'),
    textLengthElem: document.getElementById('textLength'),
    toggleOverlapsBtn: document.getElementById('toggleOverlapsBtn'),
    buttonLabel: document.getElementById('buttonLabel'),
    metadataModal: document.getElementById('metadataModal'),
    closeModalBtn: document.getElementById('closeModalBtn'),
    modalBody: document.getElementById('modalBody'),
    toastNotification: document.getElementById('toastNotification'),
    toastMessage: document.getElementById('toastMessage'),
    generatedInfo: document.getElementById('generatedInfo'),
    generatedDate: document.getElementById('generatedDate'),
    downloadChunksBtn: document.getElementById('downloadChunksBtn'),
    clearUploadBtn: document.getElementById('clearUploadBtn'),
    
    modeSelect: document.getElementById('modeSelect'),
    documentParams: document.getElementById('documentParams'),
    codeParams: document.getElementById('codeParams'),
    
    max_sentences: document.getElementById('max_sentences'),
    max_tokens: document.getElementById('max_tokens'),
    max_tokens_hint: document.querySelector('#max_tokens + small'),
    max_section_breaks: document.getElementById('max_section_breaks'),
    overlap_percent: document.getElementById('overlap_percent'),
    overlapValue: document.getElementById('overlapValue'),
    offset: document.getElementById('offset'),
    
    max_tokens_code: document.getElementById('max_tokens_code'),
    max_tokens_code_hint: document.querySelector('#max_tokens_code + small'),
    max_lines: document.getElementById('max_lines'),
    max_functions: document.getElementById('max_functions'),
    strict: document.getElementById('strict')
};

/**
 * Initializes the application when the DOM is fully loaded.
 * Sets up initial UI states, event listeners, and fetches server configuration.
 */
function init() {
    const now = new Date();
    const formattedDate = now.toLocaleString("en-US", {
        month: "long",
        day: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        hour12: true
    });
    if (elements.generatedDate) {
        elements.generatedDate.textContent = ''; // Clear content initially
    }
    if (elements.generatedInfo) {
        elements.generatedInfo.style.display = 'none'; // Hide generated info initially
    }
    
    if (elements.overlap_percent && elements.overlapValue) {
        elements.overlap_percent.value = 20;
        elements.overlapValue.textContent = '20%';
    }
    
    setupEventListeners();
    updateModeUI('document');
    
    // Set initial text for process button
    if (elements.processBtn) {
        elements.processBtn.textContent = 'No file is uploaded yet';
    }
    
    console.log('Text Chunk Visualizer initialized');
    fetchConfigAndSetupUI();
}

/**
 * Fetches server configuration, specifically token counter availability, and updates the UI accordingly.
 */
async function fetchConfigAndSetupUI() {
    try {
        const response = await fetch('/api/token_counter_status');
        const config = await response.json();
        
        if (!config.token_counter_available) {
            if (elements.max_tokens) {
                elements.max_tokens.disabled = true;
                elements.max_tokens.value = '';
            }
            if (elements.max_tokens_hint) {
                elements.max_tokens_hint.textContent = 'Chunk by token count (token counter not available)';
                elements.max_tokens_hint.style.color = 'var(--error-color)';
            }
            
            if (elements.max_tokens_code) {
                elements.max_tokens_code.disabled = true;
                elements.max_tokens_code.value = '';
            }
            if (elements.max_tokens_code_hint) {
                elements.max_tokens_code_hint.textContent = 'Chunk by token count (token counter not available)';
                elements.max_tokens_code_hint.style.color = 'var(--error-color)';
            }
        } else {
            if (elements.max_tokens) {
                elements.max_tokens.disabled = false;
            }
            if (elements.max_tokens_hint) {
                elements.max_tokens_hint.textContent = 'Chunk by token count';
                elements.max_tokens_hint.style.color = 'var(--text-tertiary)';
            }
            if (elements.max_tokens_code) {
                elements.max_tokens_code.disabled = false;
            }
            if (elements.max_tokens_code_hint) {
                elements.max_tokens_code_hint.textContent = 'Chunk by token count';
                elements.max_tokens_code_hint.style.color = 'var(--text-tertiary)';
            }
        }
    } catch (error) {
        console.error('Error fetching config:', error);
        showToast('Failed to fetch server configuration.', 'error');
        // Default to disabling if config cannot be fetched
        if (elements.max_tokens) elements.max_tokens.disabled = true;
        if (elements.max_tokens_code) elements.max_tokens_code.disabled = true;
        if (elements.max_tokens_hint) elements.max_tokens_hint.textContent = 'Chunk by token count (config error)';
        if (elements.max_tokens_code_hint) elements.max_tokens_code_hint.textContent = 'Chunk by token count (config error)';
    }
}

/**
 * Sets up all global event listeners for user interactions.
 * This includes file input, drag-and-drop, mode selection, process button,
 * overlap toggling, and modal interactions.
 */
function setupEventListeners() {
    if (elements.browseBtn && elements.fileInput) {
        elements.browseBtn.addEventListener('click', () => elements.fileInput.click());
        elements.fileInput.addEventListener('change', handleFileSelect);
    }
    
    if (elements.uploadArea) {
        elements.uploadArea.addEventListener('dragover', handleDragOver);
        elements.uploadArea.addEventListener('dragleave', handleDragLeave);
        elements.uploadArea.addEventListener('drop', handleDrop);
    }
    
    if (elements.modeSelect) {
        elements.modeSelect.addEventListener('change', handleModeChange);
    }
    
    if (elements.processBtn) {
        elements.processBtn.addEventListener('click', (e) => {
            if (elements.processBtn.disabled) {
                e.preventDefault(); // Prevent the default action for disabled button
                showToast('Please upload a file first to enable processing.', 'warning');
            } else {
                processUploadedFile();
            }
        });
    }
    
    if (elements.toggleOverlapsBtn) {
        elements.toggleOverlapsBtn.addEventListener('click', toggleOverlaps);
    }
    
    if (elements.overlap_percent && elements.overlapValue) {
        elements.overlap_percent.addEventListener('input', function() {
            elements.overlapValue.textContent = this.value + '%';
        });
    }
    
    if (elements.closeModalBtn && elements.metadataModal) {
        elements.closeModalBtn.addEventListener('click', closeMetadataModal);
        elements.metadataModal.addEventListener('click', (e) => {
            if (e.target === elements.metadataModal) {
                closeMetadataModal();
            }
        });
    }
    
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && elements.metadataModal && 
            elements.metadataModal.classList.contains('active')) {
            closeMetadataModal();
        }
    });
    
    if (elements.downloadChunksBtn) {
        elements.downloadChunksBtn.addEventListener('click', downloadChunksAsJson);
    }

    if (elements.clearUploadBtn) {
        elements.clearUploadBtn.addEventListener('click', resetUploadArea);
    }
}

/**
 * Resets the upload area UI and application state related to file uploads.
 */
function resetUploadArea() {
    console.log('resetUploadArea called');
    if (!elements.uploadContent || !elements.fileInput || !elements.processBtn || !elements.resultsSection) return;

    // Explicitly remove the clear button if it exists
    const existingClearBtn = document.getElementById('clearUploadBtn');
    console.log('existingClearBtn:', existingClearBtn);
    if (existingClearBtn) {
        existingClearBtn.remove();
        console.log('uploadContent innerHTML after remove:', elements.uploadContent.innerHTML);
    }

    elements.uploadContent.innerHTML = `
        <div class="upload-icon">📁</div>
        <h3>Upload Text File</h3>
        <p>Drag & drop a text file here or click to browse</p>
        <p class="upload-hint">Any plain text file is supported.</p>
        <button class="control-btn" id="browseBtn">Browse Files</button>
    `;
    console.log('uploadContent innerHTML after reset:', elements.uploadContent.innerHTML);
    elements.fileInput.value = '';
    elements.processBtn.disabled = true;
    elements.processBtn.textContent = 'No file is uploaded yet';
    state.uploadedFileName = '';

    if (elements.downloadChunksBtn) {
        elements.downloadChunksBtn.disabled = true;
    }
    if (elements.generatedInfo) {
        elements.generatedInfo.style.display = 'none'; // Hide generated info
    }
    
    // Re-query browseBtn and re-attach event listener
    const newBrowseBtn = document.getElementById('browseBtn');
    if (newBrowseBtn && elements.fileInput) {
        newBrowseBtn.addEventListener('click', () => elements.fileInput.click());
    }
}

/**
 * Handles the selection of a file via the file input.
 * @param {Event} event - The change event from the file input.
 */
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        updateUploadUI(file.name);
    }
}

/**
 * Handles the 'dragover' event for the upload area, preventing default behavior and adding a visual cue.
 * @param {Event} event - The dragover event.
 */
function handleDragOver(event) {
    event.preventDefault();
    event.stopPropagation();
    if (elements.uploadArea) {
        elements.uploadArea.classList.add('drag-over');
    }
}

/**
 * Handles the 'dragleave' event for the upload area, removing the visual cue.
 * @param {Event} event - The dragleave event.
 */
function handleDragLeave(event) {
    event.preventDefault();
    event.stopPropagation();
    if (elements.uploadArea) {
        elements.uploadArea.classList.remove('drag-over');
    }
}

/**
 * Handles the 'drop' event for the upload area, processing the dropped file.
 * @param {Event} event - The drop event.
 */
function handleDrop(event) {
    event.preventDefault();
    event.stopPropagation();
    if (elements.uploadArea) {
        elements.uploadArea.classList.remove('drag-over');
    }
    
    const file = event.dataTransfer.files[0];
    if (file && elements.fileInput) {
        elements.fileInput.files = event.dataTransfer.files;
        updateUploadUI(file.name);
    }
}

/**
 * Updates the user interface of the upload area to reflect the selected file.
 * @param {string} fileName - The name of the uploaded file.
 */
function updateUploadUI(fileName) {
    if (!elements.uploadContent || !elements.processBtn) return;
    
    state.uploadedFileName = fileName;
    
    // Construct the new content without the clear button initially
    let newContentHtml = `
        <div class="upload-icon">✅</div>
        <h3>File Ready</h3>
        <p><strong>${fileName}</strong></p>
        <p>Click "Process Text" to analyze chunks</p>
    `;
    elements.uploadContent.innerHTML = newContentHtml;

    // Create and prepend the clear button
    let clearBtn = document.createElement('button');
    clearBtn.className = 'close-upload-btn';
    clearBtn.id = 'clearUploadBtn';
    clearBtn.innerHTML = '&times;';
    clearBtn.addEventListener('click', resetUploadArea);
    elements.uploadContent.prepend(clearBtn); // Add button as the first child

    elements.processBtn.disabled = false;
    elements.processBtn.textContent = state.currentMode === 'document' ? 'Process Document' : 'Process Code';
}

/**
 * Handles changes in the chunking mode (document or code).
 * @param {Event} event - The change event from the mode select dropdown.
 */
function handleModeChange(event) {
    const mode = event.target.value;
    state.currentMode = mode;
    updateModeUI(mode);
}

/**
 * Updates the UI elements based on the selected chunking mode.
 * @param {string} mode - The current chunking mode ('document' or 'code').
 */
function updateModeUI(mode) {
    if (elements.documentParams) {
        elements.documentParams.classList.toggle('active', mode === 'document');
    }
    if (elements.codeParams) {
        elements.codeParams.classList.toggle('active', mode === 'code');
    }
    
    if (elements.processBtn) {
        elements.processBtn.textContent = mode === 'document' ? 'Process Document' : 'Process Code';
    }
}

/**
 * Handles the processing of the uploaded file.
 * Sends the file and selected parameters to the backend API for chunking.
 * Updates the application state and UI with the chunked data.
 * Displays toast notifications for success or error messages.
 */
async function processUploadedFile() {
    const file = elements.fileInput ? elements.fileInput.files[0] : null;
    if (!file) {
        showToast('Please select a file first', 'error');
        return;
    }
    
    const params = getCurrentParameters();
    
    if (!hasRequiredConstraints(params, state.currentMode)) {
        showToast(`Please set at least one constraint for ${state.currentMode} mode`, 'error');
        return;
    }
    
    try {
        if (elements.processBtn) {
            elements.processBtn.disabled = true;
            elements.processBtn.textContent = 'Processing...';
        }
        
        // Create FormData with file and parameters as JSON
        const formData = new FormData();
        formData.append('file', file);
        formData.append('mode', state.currentMode);
        formData.append('params', JSON.stringify(params));

        // Send POST with FormData
        const response = await fetch('/api/chunk', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            let errorMessage = `Server error: ${response.status}`;
            try {
                const errorData = JSON.parse(errorText);
                errorMessage = errorData.detail || errorMessage;
            } catch {
                errorMessage = errorText || errorMessage;
            }
            throw new Error(errorMessage);
        }
        
        const data = await response.json();
        
        // Update state
        state.originalText = data.text;
        state.chunksData = data.chunks.map((chunk, index) => {
            const newFullMetadata = { ...chunk.metadata, source: state.uploadedFileName };
            return {
                chunk_id: index,
                chunk_num: chunk.metadata.chunk_num || index + 1,
                span: chunk.metadata.span || [0, 0],
                content: chunk.content,
                full_metadata: newFullMetadata
            };
        });
        state.overlaps = calculateOverlaps();
        state.activeChunkId = null;
        state.highlightedChunks.clear();
        state.showOverlaps = false;
        
        updateStats();
        renderTextWithSpans();
        
        if (elements.toggleOverlapsBtn) {
            elements.toggleOverlapsBtn.disabled = false;
        }
        if (elements.downloadChunksBtn) {
            elements.downloadChunksBtn.disabled = false;
        }
        
        const now = new Date();
        const formattedDate = now.toLocaleString("en-US", {
            month: "long",
            day: "2-digit",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
            hour12: true
        });
        if (elements.generatedDate) {
            elements.generatedDate.textContent = formattedDate;
        }
        if (elements.generatedInfo) {
            elements.generatedInfo.style.display = ''; // Show generated info
        }
        
        showToast(`Processed ${data.chunks.length} chunks from "${file.name}"`, 'success');
        
    } catch (error) {
        console.error('Error processing file:', error);
        if (elements.textDisplay) {
            elements.textDisplay.innerHTML = `
                <div class="placeholder-text" style="color: var(--error-color);">
                    <p>Error processing file: ${escapeHtml(error.message)}</p>
                    <p>Please check the file format and parameters.</p>
                </div>
            `;
        }

    } finally {
        if (elements.processBtn) {
            elements.processBtn.disabled = false;
            elements.processBtn.textContent = state.currentMode === 'document' ? 'Process Document' : 'Process Code';
        }
    }
}

function getCurrentParameters() {
    const params = {};
    
    if (state.currentMode === 'document') {
        if (elements.max_sentences?.value) params.max_sentences = elements.max_sentences.value;
        if (elements.max_tokens?.value) params.max_tokens = elements.max_tokens.value;
        if (elements.max_section_breaks?.value) params.max_section_breaks = elements.max_section_breaks.value;
        if (elements.overlap_percent?.value) params.overlap_percent = elements.overlap_percent.value;
        if (elements.offset?.value) params.offset = elements.offset.value;
    } else {
        if (elements.max_tokens_code?.value) params.max_tokens = elements.max_tokens_code.value;
        if (elements.max_lines?.value) params.max_lines = elements.max_lines.value;
        if (elements.max_functions?.value) params.max_functions = elements.max_functions.value;
        if (elements.strict) params.strict = elements.strict.checked;
    }
    
    return params;
}

function hasRequiredConstraints(params, mode) {
    if (mode === 'document') {
        return params.max_sentences || params.max_tokens || params.max_section_breaks;
    } else {
        return params.max_tokens || params.max_lines || params.max_functions;
    }
}

function renderTextWithSpans() {
    if (!elements.textDisplay) return;
    
    const positionMap = new Map();
    
    state.chunksData.forEach((chunk, chunkId) => {
        const [start, end] = chunk.span;
        for (let i = start; i < end; i++) {
            if (!positionMap.has(i)) {
                positionMap.set(i, []);
            }
            if (positionMap.get(i).length < 2) {
                positionMap.get(i).push(chunkId);
            }
        }
    });
    
    let html = '';
    let i = 0;
    let currentChunks = new Set();
    let currentText = '';
    
    while (i < state.originalText.length) {
        const chunksAtPosition = positionMap.get(i) || [];
        
        const chunkSetChanged = chunksAtPosition.length !== currentChunks.size || 
            !chunksAtPosition.every(id => currentChunks.has(id));
        
        if (chunkSetChanged && currentText) {
            html += createSpanElement(currentText, currentChunks, i - currentText.length);
            currentText = '';
        }
        
        currentChunks = new Set(chunksAtPosition);
        currentText += state.originalText[i];
        i++;
    }
    
    if (currentText) {
        html += createSpanElement(currentText, currentChunks, i - currentText.length);
    }
    
    elements.textDisplay.innerHTML = html;
    
    elements.textDisplay.addEventListener('click', handleChunkClick);
    elements.textDisplay.addEventListener('dblclick', handleChunkDoubleClick);
}

function createSpanElement(text, chunkIds, startPos) {
    if (chunkIds.size === 0) return escapeHtml(text);
    
    const escapedText = escapeHtml(text);
    const chunkIdStr = Array.from(chunkIds).join(',');
    
    return `<span class="chunk-span" 
                  data-chunk-ids="${chunkIdStr}" 
                  data-start="${startPos}">${escapedText}</span>`;
}

function handleChunkClick(event) {
    const span = event.target.closest('.chunk-span');
    if (!span) return;
    
    const chunkIds = span.dataset.chunkIds.split(',').map(id => parseInt(id));
    if (chunkIds.length > 0) {
        state.highlightedChunks.clear();
        toggleChunkHighlight(chunkIds[0]);
    }
}

function handleChunkDoubleClick(event) {
    const span = event.target.closest('.chunk-span');
    if (!span) return;
    
    const chunkIds = span.dataset.chunkIds.split(',').map(id => parseInt(id));
    if (chunkIds.length > 0) {
        showMetadata(chunkIds[0]);
    }
}

function toggleChunkHighlight(chunkId) {
    if (state.highlightedChunks.has(chunkId)) {
        state.highlightedChunks.delete(chunkId);
        state.activeChunkId = null;
        showToast(`Chunk ${chunkId + 1} unhighlighted`, 'info');
    } else {
        state.highlightedChunks.add(chunkId);
        state.activeChunkId = chunkId;
        
        const chunk = state.chunksData[chunkId];
        const [start, end] = chunk.span;
        const chunkLength = end - start;
        const chunkNum = chunk.chunk_num || chunkId + 1;
        
        showToast(`Chunk ${chunkNum} selected (${chunkLength} characters)`, 'success');
    }
    
    updateAllHighlights();
}

function updateAllHighlights() {
    if (!elements.textDisplay) return;
    
    const spans = elements.textDisplay.querySelectorAll('.chunk-span');
    spans.forEach(span => {
        const chunkIds = span.dataset.chunkIds.split(',').map(id => parseInt(id));
        span.classList.remove('highlighted', 'selected', 'overlap');
        
        const hasHighlighted = chunkIds.some(id => state.highlightedChunks.has(id));
        const hasSelected = chunkIds.includes(state.activeChunkId);
        
        if (hasHighlighted) span.classList.add('highlighted');
        if (hasSelected) span.classList.add('selected');
        
        if (state.activeChunkId !== null && state.showOverlaps) {
            const chunkOverlaps = getOverlapsForChunk(state.activeChunkId);
            const spanStart = parseInt(span.dataset.start);
            const spanEnd = spanStart + span.textContent.length;
            
            chunkOverlaps.forEach(overlap => {
                if (spanStart < overlap.end && spanEnd > overlap.start) {
                    span.classList.add('overlap');
                }
            });
        }
    });
}

function calculateOverlaps() {
    const overlaps = [];
    
    const sortedChunks = state.chunksData
        .map((chunk, index) => ({ ...chunk, originalIndex: index }))
        .sort((a, b) => a.span[0] - b.span[0]);
    
    for (let i = 0; i < sortedChunks.length - 1; i++) {
        const currentChunk = sortedChunks[i];
        const nextChunk = sortedChunks[i + 1];
        
        const [currStart, currEnd] = currentChunk.span;
        const [nextStart, nextEnd] = nextChunk.span;
        
        if (nextStart < currEnd) {
            const overlapStart = Math.max(currStart, nextStart);
            const overlapEnd = Math.min(currEnd, nextEnd);
            
            if (overlapStart < overlapEnd) {
                overlaps.push({
                    start: overlapStart,
                    end: overlapEnd,
                    leftChunk: currentChunk.originalIndex,
                    rightChunk: nextChunk.originalIndex,
                    size: overlapEnd - overlapStart
                });
            }
        }
    }
    
    return overlaps;
}

function getOverlapsForChunk(chunkId) {
    return state.overlaps.filter(overlap => 
        overlap.leftChunk === chunkId || overlap.rightChunk === chunkId
    );
}

function toggleOverlaps() {
    state.showOverlaps = !state.showOverlaps;
    if (elements.toggleOverlapsBtn) {
        elements.toggleOverlapsBtn.classList.toggle('active', state.showOverlaps);
        elements.toggleOverlapsBtn.textContent = state.showOverlaps ? 'Hide Overlaps' : 'Reveal Overlaps';
    }
    updateAllHighlights();
    updateStats();
}

function showMetadata(chunkId) {
    const chunk = state.chunksData[chunkId];
    const [start, end] = chunk.span;
    const chunkText = state.originalText.substring(start, end);
    const charCount = end - start;
    
    const previewLength = Math.min(200, chunkText.length);
    const previewText = chunkText.substring(0, previewLength);
    
    const chunkOverlaps = getOverlapsForChunk(chunkId);

    // Prepare metadata for display - only show what's explicitly in chunk.metadata
    const displayMetadata = { ...chunk.full_metadata };
    
    let html = `
        <div class="chunk-text">
            <strong>Content Preview (${charCount} characters):</strong><br>
            "${escapeHtml(previewText)}${chunkText.length > 200 ? '...' : ''}"
        </div>`;
    
    if (chunkOverlaps.length > 0) {
        html += `<div><strong>Overlaps:</strong></div>`;
        chunkOverlaps.forEach(overlap => {
            const otherChunkId = overlap.leftChunk === chunkId ? overlap.rightChunk : overlap.leftChunk;
            const otherChunk = state.chunksData[otherChunkId];
            const overlapText = state.originalText.substring(overlap.start, overlap.end);
            html += `
            <div style="margin-top: 5px; padding: 8px; background: var(--overlap-color); border-radius: 4px;">
                <strong>With Chunk ${otherChunkId + 1}:</strong> 
                ${overlap.size} characters overlap<br>
                "${escapeHtml(overlapText.substring(0, 100))}${overlapText.length > 100 ? '...' : ''}"
            </div>`;
        });
    }
    
    html += `
        <div style="margin-top: 15px;"><strong>Chunk Metadata:</strong></div>
        <div class="metadata-display-container">
            ${renderMetadataTable(displayMetadata)}
        </div>
    `;
    
    if (elements.modalBody) {
        elements.modalBody.innerHTML = html;
    }
    
    document.body.style.overflow = 'hidden';
    if (elements.metadataModal) {
        elements.metadataModal.classList.add('active');
    }
}

function closeMetadataModal() {
    document.body.style.overflow = '';
    if (elements.metadataModal) {
        elements.metadataModal.classList.remove('active');
    }
}

// Handle scroll hint visibility
function setupScrollHint() {
    if (elements.modalBody) {
        elements.modalBody.addEventListener('scroll', function() {
            const scrollHint = document.querySelector('.scroll-hint');
            if (scrollHint && this.scrollTop > 10) {
                scrollHint.style.opacity = '0';
                scrollHint.style.pointerEvents = 'none';
                // Remove the event listener after first scroll to avoid unnecessary calls
                this.removeEventListener('scroll', arguments.callee);
            }
        });
    }
}

function updateStats() {
    if (elements.totalChunksElem) {
        elements.totalChunksElem.textContent = `Chunks: ${state.chunksData.length}`;
    }
    if (elements.textLengthElem) {
        elements.textLengthElem.textContent = `Text Length: ${state.originalText.length} chars`;
    }
}

function downloadChunksAsJson() {
    if (state.chunksData.length === 0) {
        showToast('No chunks to download', 'warning');
        return;
    }
    
    const data = {
        chunks: state.chunksData.map(chunk => {
            return {
                content: chunk.content,
                metadata: chunk.full_metadata
            };
        }),
        stats: {
            chunk_count: state.chunksData.length,
            overlap_count: state.overlaps.length,
            text_length: state.originalText.length,
            mode: state.currentMode,
            generated: new Date().toISOString()
        }
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chunks_${state.currentMode}_${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showToast('Chunks downloaded as JSON', 'success');
}

function showToast(message, type = 'info') {
    if (!elements.toastMessage || !elements.toastNotification) return;

    // Clear any existing timeout
    if (toastTimeoutId) {
        clearTimeout(toastTimeoutId);
    }

    elements.toastMessage.textContent = message;

    switch (type) {
        case 'error':
            elements.toastNotification.style.backgroundColor = 'var(--error-color)';
            break;
        case 'success':
            elements.toastNotification.style.backgroundColor = 'var(--success-color)';
            break;
        case 'warning':
            elements.toastNotification.style.backgroundColor = 'var(--warning-color)';
            break;
        default:
            elements.toastNotification.style.backgroundColor = 'var(--accent-color)';
    }

    elements.toastNotification.classList.add('show');

    toastTimeoutId = setTimeout(() => {
        elements.toastNotification.classList.remove('show');
        toastTimeoutId = null;
    }, 5000);
}

function escapeHtml(text) {
    if (text == null) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function renderMetadataTable(metadataObject) {
    let tableHtml = '<table class="metadata-table">';
    for (const key in metadataObject) {
        if (Object.hasOwnProperty.call(metadataObject, key)) {
            let value = metadataObject[key];
            
            // Handle arrays and objects for better display
            if (Array.isArray(value)) {
                value = `[${value.map(item => JSON.stringify(item)).join(', ')}]`;
            } else if (typeof value === 'object' && value !== null) {
                value = JSON.stringify(value, null, 2); // Pretty print nested objects
            }
            tableHtml += `
                <tr>
                    <td><strong>${escapeHtml(key)}:</strong></td>
                    <td>${escapeHtml(String(value))}</td>
                </tr>
            `;
        }
    }
    tableHtml += '</table>';
    return tableHtml;
}

document.addEventListener('DOMContentLoaded', init);
