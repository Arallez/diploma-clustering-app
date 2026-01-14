// Симулятор K-Means (островок Vue.js)
// Будет подключен в index.html

const { createApp } = Vue;

function initSimulator() {
  return createApp({
    data() {
      return {
        points: [],
        k: 3,
        history: [],
        currentStep: 0,
        isRunning: false,
        selectedAlgorithm: 'kmeans'
      };
    },
    mounted() {
      this.initPlot();
      this.setupClickListener();
    },
    methods: {
      initPlot() {
        const layout = {
          autosize: true,
          paper_bgcolor: 'rgba(0,0,0,0)',
          plot_bgcolor: 'rgba(30,30,40,0.3)',
          font: { color: '#e0e0e0', family: 'Inter, sans-serif' },
          xaxis: {
            gridcolor: 'rgba(255,255,255,0.1)',
            zerolinecolor: 'rgba(255,255,255,0.2)',
            range: [0, 10],
            fixedrange: false
          },
          yaxis: {
            gridcolor: 'rgba(255,255,255,0.1)',
            zerolinecolor: 'rgba(255,255,255,0.2)',
            range: [0, 10],
            fixedrange: false
          },
          hovermode: 'closest',
          showlegend: false,
          margin: { t: 20, r: 20, b: 40, l: 40 }
        };

        const config = {
          responsive: true,
          displayModeBar: false
        };

        Plotly.newPlot('plotly-chart', [], layout, config);
      },

      setupClickListener() {
        const plotDiv = document.getElementById('plotly-chart');
        const canvas = plotDiv.querySelector('.nsewdrag');
        
        if (canvas) {
          canvas.addEventListener('click', (event) => {
            const rect = canvas.getBoundingClientRect();
            const x = event.clientX - rect.left;
            const y = event.clientY - rect.top;
            
            const xaxis = plotDiv._fullLayout.xaxis;
            const yaxis = plotDiv._fullLayout.yaxis;
            
            const dataX = xaxis.p2d(x);
            const dataY = yaxis.p2d(y);
            
            this.addPoint(dataX, dataY);
          });
        }
      },

      addPoint(x, y) {
        this.points.push([parseFloat(x.toFixed(2)), parseFloat(y.toFixed(2))]);
        this.updatePlot();
      },

      updatePlot() {
        const trace = {
          x: this.points.map(p => p[0]),
          y: this.points.map(p => p[1]),
          mode: 'markers',
          type: 'scatter',
          marker: {
            size: 10,
            color: '#60a5fa',
            line: { color: '#3b82f6', width: 2 }
          }
        };

        Plotly.react('plotly-chart', [trace]);
      },

      async runAlgorithm() {
        if (this.points.length < this.k) {
          alert(`Нужно минимум ${this.k} точек для K=${this.k}`);
          return;
        }

        this.isRunning = true;
        
        try {
          const response = await fetch('/simulator/api/run-kmeans/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              points: this.points,
              k: this.k
            })
          });

          const data = await response.json();
          
          if (data.success) {
            this.history = data.history;
            this.currentStep = 0;
            this.visualizeStep(0);
          }
        } catch (error) {
          console.error('Ошибка:', error);
          alert('Ошибка при выполнении алгоритма');
        } finally {
          this.isRunning = false;
        }
      },

      visualizeStep(stepIndex) {
        const step = this.history[stepIndex];
        if (!step) return;

        const colors = ['#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899'];
        const pointTraces = [];

        for (let cluster = 0; cluster < this.k; cluster++) {
          const clusterPoints = this.points.filter((_, i) => step.labels[i] === cluster);
          if (clusterPoints.length > 0) {
            pointTraces.push({
              x: clusterPoints.map(p => p[0]),
              y: clusterPoints.map(p => p[1]),
              mode: 'markers',
              type: 'scatter',
              marker: { size: 10, color: colors[cluster] },
              showlegend: false
            });
          }
        }

        const centroidTrace = {
          x: step.centroids.map(c => c[0]),
          y: step.centroids.map(c => c[1]),
          mode: 'markers',
          type: 'scatter',
          marker: {
            size: 18,
            color: 'white',
            symbol: 'x',
            line: { color: 'black', width: 2 }
          },
          showlegend: false
        };

        Plotly.react('plotly-chart', [...pointTraces, centroidTrace]);
      },

      nextStep() {
        if (this.currentStep < this.history.length - 1) {
          this.currentStep++;
          this.visualizeStep(this.currentStep);
        }
      },

      prevStep() {
        if (this.currentStep > 0) {
          this.currentStep--;
          this.visualizeStep(this.currentStep);
        }
      },

      clearBoard() {
        this.points = [];
        this.history = [];
        this.currentStep = 0;
        this.initPlot();
        this.setupClickListener();
      }
    }
  });
}

// Экспортируем для использования в шаблоне
window.initSimulator = initSimulator;