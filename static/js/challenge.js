// Редактор задач (островок Vue.js + Monaco + Pyodide)
// Будет подключен в challenge.html

const { createApp } = Vue;

function initChallenge(taskData) {
  return createApp({
    data() {
      return {
        task: taskData,
        editor: null,
        pyodide: null,
        output: '',
        isRunning: false,
        isChecking: false,
        result: null
      };
    },
    async mounted() {
      await this.initMonaco();
      await this.loadPyodide();
    },
    methods: {
      async initMonaco() {
        require.config({ paths: { vs: 'https://cdn.jsdelivr.net/npm/monaco-editor@0.45.0/min/vs' } });
        
        require(['vs/editor/editor.main'], () => {
          this.editor = monaco.editor.create(document.getElementById('code-editor'), {
            value: this.task.initial_code,
            language: 'python',
            theme: 'vs-dark',
            fontSize: 14,
            minimap: { enabled: false },
            automaticLayout: true
          });
        });
      },

      async loadPyodide() {
        this.output = '⏳ Загрузка Python-окружения...';
        this.pyodide = await loadPyodide();
        await this.pyodide.loadPackage('numpy');
        this.output = '✅ Python готов к работе!';
      },

      async runCode() {
        if (!this.pyodide) {
          alert('Pyodide ещё загружается...');
          return;
        }

        this.isRunning = true;
        this.output = '';
        this.result = null;

        try {
          const code = this.editor.getValue();
          const testCode = `
import json
${code}

# Запуск теста
test_input = ${JSON.stringify(this.task.test_input)}
result = ${this.task.function_name}(*test_input)
print(json.dumps(result))
`;

          this.pyodide.runPython(`
import sys
from io import StringIO
sys.stdout = StringIO()
`);

          this.pyodide.runPython(testCode);
          const stdout = this.pyodide.runPython('sys.stdout.getvalue()');
          this.output = stdout || '(программа ничего не вывела)';

          // Парсим результат для проверки
          const lines = stdout.trim().split('\n');
          const lastLine = lines[lines.length - 1];
          
          try {
            const userResult = JSON.parse(lastLine);
            await this.checkSolution(userResult);
          } catch {
            this.output += '\n⚠️ Результат не в формате JSON';
          }

        } catch (error) {
          this.output = `❌ Ошибка:\n${error.message}`;
        } finally {
          this.isRunning = false;
        }
      },

      async checkSolution(userResult) {
        this.isChecking = true;

        try {
          const response = await fetch('/simulator/api/check-solution/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              task_id: this.task.slug,
              result: userResult
            })
          });

          const data = await response.json();
          this.result = data;
          
          if (data.correct) {
            this.output += '\n\n✅ ' + data.message;
          } else {
            this.output += '\n\n❌ ' + data.message;
          }
        } catch (error) {
          this.output += '\n\n⚠️ Ошибка проверки: ' + error.message;
        } finally {
          this.isChecking = false;
        }
      }
    }
  });
}

window.initChallenge = initChallenge;