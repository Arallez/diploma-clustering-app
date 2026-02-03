/**
 * Challenge Page Logic
 * Handles Editor initialization, Quiz rendering, and Submission logic.
 */

// Global state
let editor;
let quizData = [];
let isMultiQuestionMode = false;

document.addEventListener('DOMContentLoaded', () => {
    const taskType = document.getElementById('task-type').value;

    if (taskType === 'code') {
        initCodeEditor();
    } else {
        initQuiz();
    }
});

/**
 * Initialize Monaco Editor for Code tasks
 */
function initCodeEditor() {
    require.config({ paths: { 'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.36.1/min/vs' }});
    require(['vs/editor/editor.main'], function() {
        editor = monaco.editor.create(document.getElementById('monaco-editor'), {
            value: document.getElementById('initial-code').value,
            language: 'python',
            theme: 'vs-dark',
            fontSize: 14,
            minimap: { enabled: false },
            automaticLayout: true
        });
    });

    // Attach click handler
    document.getElementById('runBtn').addEventListener('click', submitCode);
}

/**
 * Initialize Quiz Rendering
 */
function initQuiz() {
    try {
        const rawData = document.getElementById('quiz-data').textContent;
        quizData = parseQuizData(rawData);
        
        // Handle nested {"questions": [...]} wrapper
        if (quizData && !Array.isArray(quizData) && quizData.questions && Array.isArray(quizData.questions)) {
            quizData = quizData.questions;
        }

        // Normalize single object to array
        if (!Array.isArray(quizData)) {
            if (typeof quizData === 'object' && quizData !== null) quizData = Object.values(quizData);
            else quizData = [quizData];
        }

        const container = document.getElementById('quiz-container');
        container.innerHTML = '';

        // Detect Multi-Question Mode
        const hasQuestions = quizData.some(item => typeof item === 'object' && item.options && Array.isArray(item.options));
        isMultiQuestionMode = hasQuestions;

        if (hasQuestions) {
            renderMultiQuestionQuiz(container, quizData);
        } else {
            renderSingleQuestionQuiz(container, quizData);
        }
        
        // Attach Submit Handler
        document.getElementById('submitQuizBtn').addEventListener('click', submitQuiz);

    } catch (e) {
        console.error("Quiz Init Error:", e);
        document.getElementById('quiz-container').innerHTML = `<p style="color:#f87171">Ошибка отображения теста: ${e.message}</p>`;
    }
}

/**
 * Robust JSON Parser
 */
function parseQuizData(jsonString) {
    let data = JSON.parse(jsonString);
    let attempts = 5;
    
    // Aggressively unwrap double-encoded strings
    while (typeof data === 'string' && attempts > 0) {
        try {
            data = JSON.parse(data);
        } catch (e) {
            // Clean common dirty chars (NBSP, single quotes)
            const clean = data.replace(/\u00A0/g, ' ').replace(/'/g, '"');
            try { data = JSON.parse(clean); } catch (e2) { break; }
        }
        attempts--;
    }
    return data;
}

/**
 * Render Multi-Question Format
 */
function renderMultiQuestionQuiz(container, questions) {
    questions.forEach((q, qIdx) => {
        if (typeof q !== 'object') return;

        const block = document.createElement('div');
        block.className = 'quiz-question-block';
        block.dataset.type = 'question';
        block.dataset.index = qIdx;

        const title = document.createElement('div');
        title.className = 'quiz-question-text';
        title.innerHTML = q.text || `Вопрос ${qIdx + 1}`;
        block.appendChild(title);

        const optsGroup = document.createElement('div');
        optsGroup.className = 'quiz-options-group';

        const options = q.options || [];
        options.forEach((opt, oIdx) => {
            const div = document.createElement('div');
            div.className = 'quiz-option';
            const inputId = `q${qIdx}_o${oIdx}`;
            
            div.innerHTML = `
                <input type="radio" name="q_${qIdx}" value="${opt}" id="${inputId}">
                <label for="${inputId}" style="flex:1; cursor:pointer;">${opt}</label>
            `;
            
            div.onclick = (e) => {
                if(e.target.tagName !== 'INPUT') {
                    div.querySelector('input').checked = true;
                }
                optsGroup.querySelectorAll('.quiz-option').forEach(el => el.classList.remove('selected'));
                div.classList.add('selected');
            };
            
            optsGroup.appendChild(div);
        });
        
        block.appendChild(optsGroup);
        container.appendChild(block);
    });
}

/**
 * Render Single-Question Format (Legacy)
 */
function renderSingleQuestionQuiz(container, options) {
    const optsGroup = document.createElement('div');
    optsGroup.className = 'quiz-options-group';

    options.forEach((opt, idx) => {
        let text = opt;
        let val = opt;
        
        if (typeof opt === 'object' && opt !== null) {
            text = opt.text || opt.label || opt.value || JSON.stringify(opt);
            val = opt.value || text;
            if (typeof val === 'object') val = JSON.stringify(val);
        }

        const div = document.createElement('div');
        div.className = 'quiz-option';
        const inputId = `opt_${idx}`;
        
        div.innerHTML = `
            <input type="checkbox" name="quiz_option" value='${val}' id="${inputId}">
            <label for="${inputId}" style="flex:1; cursor:pointer;">${text}</label>
        `;
        
        div.onclick = (e) => {
            if(e.target.tagName !== 'INPUT') {
                const cb = div.querySelector('input');
                cb.checked = !cb.checked;
            }
            if(div.querySelector('input').checked) div.classList.add('selected');
            else div.classList.remove('selected');
        };
        
        optsGroup.appendChild(div);
    });
    
    container.appendChild(optsGroup);
}

/**
 * Submit Code Logic
 */
async function submitCode() {
    const code = editor.getValue();
    const slug = document.getElementById('task-slug').value;
    const outputDiv = document.getElementById('output');
    
    outputDiv.innerHTML = "⏳ Проверка на сервере...";
    
    try {
        const result = await postSolution(slug, code);
        
        if (result.success) {
            outputDiv.innerHTML = `<div class="output-success">✅ ${result.message}</div>`;
        } else {
            outputDiv.innerHTML = `<div class="output-error">❌ Ошибка: ${result.error || 'Неизвестная ошибка'}</div>`;
        }
    } catch (e) {
        outputDiv.innerHTML = `<div class="output-error">Network/Server Error: ${e.message}</div>`;
    }
}

/**
 * Submit Quiz Logic
 */
async function submitQuiz() {
    const slug = document.getElementById('task-slug').value;
    const resultDiv = document.getElementById('quiz-result');
    let payload = null;
    
    // Gather answers
    if (isMultiQuestionMode) {
        const blocks = document.querySelectorAll('.quiz-question-block');
        payload = [];
        let allAnswered = true;

        blocks.forEach((block, idx) => {
            const checked = block.querySelector('input[type="radio"]:checked');
            if (checked) payload.push(checked.value);
            else {
                allAnswered = false;
                payload.push(null);
            }
        });

        if (!allAnswered) {
            resultDiv.innerHTML = `<span style="color:#fbbf24">⚠️ Пожалуйста, ответьте на все вопросы</span>`;
            return;
        }
    } else {
        payload = Array.from(document.querySelectorAll('input[name="quiz_option"]:checked'))
                       .map(cb => cb.value);
        
        if (payload.length === 0) {
            resultDiv.innerHTML = `<span style="color:#fbbf24">⚠️ Выберите хотя бы один вариант</span>`;
            return;
        }
    }

    // Send
    try {
        const result = await postSolution(slug, payload);
        
        // Update Visuals (Green/Red borders)
        updateQuizVisuals(result.quiz_results, result.success);

        if (result.success) {
            resultDiv.innerHTML = `<span style="color:#4ade80">✅ ${result.message}</span>`;
        } else {
            if (result.quiz_results) {
                resultDiv.innerHTML = `<span style="color:#f87171">❌ Некоторые ответы неверны (см. красные блоки)</span>`;
            } else {
                resultDiv.innerHTML = `<span style="color:#f87171">❌ ${result.error}</span>`;
            }
        }
    } catch (e) {
        resultDiv.innerText = "Error: " + e.message;
    }
}

/**
 * Helper to POST data
 */
async function postSolution(slug, codeOrAnswers) {
    const csrfToken = document.cookie.match(/csrftoken=([^;]+)/)?.[1];
    
    const response = await fetch('/simulator/api/check-solution/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ slug, code: codeOrAnswers })
    });
    
    const text = await response.text();
    try {
        return JSON.parse(text);
    } catch (e) {
        throw new Error("Invalid Server Response (HTML): " + text.substring(0, 100));
    }
}

/**
 * Update Quiz Borders based on results
 */
function updateQuizVisuals(resultsArray, isSuccess) {
    const blocks = document.querySelectorAll('.quiz-question-block');
    
    if (Array.isArray(resultsArray) && blocks.length > 0) {
        resultsArray.forEach((isRight, idx) => {
            if (blocks[idx]) {
                blocks[idx].style.borderColor = isRight ? '#4ade80' : '#f87171';
                blocks[idx].style.borderWidth = isRight ? '1px' : '2px';
                blocks[idx].style.boxShadow = isRight ? 'none' : '0 0 10px rgba(248, 113, 113, 0.2)';
            }
        });
    }
}
