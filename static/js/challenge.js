// Редактор задач (Vue.js Island)
// Включает Monaco Editor + Pyodide для выполнения Python

const { createApp, onMounted, ref } = Vue;

function initChallengeApp(taskData) {
    return createApp({
        setup() {
            const isPyodideReady = ref(false);
            const isRunning = ref(false);
            const resultStatus = ref('');
            const resultMessage = ref('');
            const task = ref(taskData);
            let pyodide = null;
            let editor = null;

            const initEditor = () => {
                require.config({ 
                    paths: { 'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.44.0/min/vs' }
                });
                
                require(['vs/editor/editor.main'], function() {
                    editor = monaco.editor.create(document.getElementById('editor-container'), {
                        value: task.value.initial_code,
                        language: 'python',
                        theme: 'vs-dark',
                        minimap: { enabled: false },
                        fontSize: 14,
                        automaticLayout: true
                    });
                });
            };

            const initPyodide = async () => {
                try {
                    pyodide = await loadPyodide();
                    await pyodide.loadPackage('numpy');
                    isPyodideReady.value = true;
                } catch(e) {
                    console.error('Pyodide failed', e);
                }
            };

            const runCode = async () => {
                if (!pyodide) return;
                isRunning.value = true;
                resultStatus.value = '';
                resultMessage.value = '';

                const userCode = editor.getValue();
                
                const wrapper = `
import json
import numpy as np

out = None

# User Code
${userCode}

# Test execution
try:
    test_input = ${JSON.stringify(task.value.test_input)}
    
    if '${task.value.function_name}' not in locals():
        out = json.dumps({"ERROR_IN_PY": "Функция ${task.value.function_name} не найдена"})
    else:
        func = locals()['${task.value.function_name}']
        
        if isinstance(test_input, list):
             if '${task.value.function_name}' == 'dist':
                 result = func(*test_input)
             else:
                 result = func(test_input)
        elif isinstance(test_input, dict):
             result = func(**test_input)
        else:
             result = func(test_input)

        if hasattr(result, 'tolist'): result = result.tolist()
        if hasattr(result, 'item'): result = result.item() 
        
        out = json.dumps(result)
except Exception as e:
    out = json.dumps({"ERROR_IN_PY": str(e)})

out
`;

                try {
                    const jsonOutput = await pyodide.runPythonAsync(wrapper);
                    if (typeof jsonOutput !== 'string') throw new Error('Empty result');

                    const output = JSON.parse(jsonOutput);
                    if (output && output.ERROR_IN_PY) {
                        resultStatus.value = 'error';
                        resultMessage.value = 'Ошибка: ' + output.ERROR_IN_PY;
                        return;
                    }

                    const checkUrl = (document.getElementById('check-solution-url') && document.getElementById('check-solution-url').value) || '/tasks/api/check-solution/';
                    const response = await fetch(checkUrl, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ 
                            task_slug: task.value.slug, 
                            result: output,
                            code: userCode
                        })
                    });
                    
                    const serverResp = await response.json();
                    
                    if (serverResp.correct) {
                        resultStatus.value = 'success';
                        resultMessage.value = serverResp.message;
                    } else {
                        resultStatus.value = 'error';
                        resultMessage.value = serverResp.message;
                    }
                } catch (e) {
                    console.error(e);
                    resultStatus.value = 'error';
                    resultMessage.value = 'Ошибка: ' + e.message;
                } finally {
                    isRunning.value = false;
                }
            };
            
            const resetCode = () => {
                if(editor) editor.setValue(task.value.initial_code);
                resultStatus.value = '';
            };

            onMounted(() => {
                initEditor();
                initPyodide();
            });

            return {
                task,
                isPyodideReady, 
                isRunning, 
                runCode, 
                resetCode, 
                resultStatus, 
                resultMessage
            };
        }
    });
}

// Экспортируем
if (typeof window !== 'undefined') {
    window.initChallengeApp = initChallengeApp;
}