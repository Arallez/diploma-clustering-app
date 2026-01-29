import { runKMeans, runDBSCAN, runForel, runAgglomerative, runMeanShift, generatePreset, getDendrogram } from './api.js?v=5.0';
import { initPlot, drawPoints, drawStep, convertClickToPoint } from './plot.js?v=5.0';

const { createApp, ref, onMounted, watch } = Vue;

const app = createApp({
    setup() {
        // State
        const algorithm = ref('kmeans');
        const k = ref(3);
        const eps = ref(1.0);
        const minPts = ref(3);
        const radius = ref(1.0); // FOREL radius
        const bandwidth = ref(1.0); // MeanShift bandwidth
        const points = ref([]);
        const history = ref([]);
        const currentStep = ref(0);
        const isRunning = ref(false);
        const selectedPreset = ref('');
        const showDendrogram = ref(false);

        // Actions
        const handleCanvasClick = (event) => {
            if (history.value.length > 0) return;
            const point = convertClickToPoint(event);
            if (point) {
                points.value.push(point);
                drawPoints(points.value);
            }
        };

        const loadPreset = async () => {
            if (!selectedPreset.value) return;
            isRunning.value = true;
            try {
                const data = await generatePreset(selectedPreset.value, 100);
                if (data.success) {
                    points.value = data.points;
                    history.value = [];
                    currentStep.value = 0;
                    drawPoints(points.value);
                } else {
                    alert('Ошибка загрузки: ' + data.error);
                }
            } catch (e) {
                console.error(e);
                alert('Ошибка сервера');
            } finally {
                isRunning.value = false;
            }
        };

        const runAlgorithm = async () => {
            isRunning.value = true;
            try {
                let data;
                if (algorithm.value === 'kmeans') {
                    data = await runKMeans(points.value, k.value);
                } else if (algorithm.value === 'dbscan') {
                    data = await runDBSCAN(points.value, parseFloat(eps.value), minPts.value);
                } else if (algorithm.value === 'forel') {
                    data = await runForel(points.value, parseFloat(radius.value));
                } else if (algorithm.value === 'agglomerative') {
                    data = await runAgglomerative(points.value, k.value);
                } else if (algorithm.value === 'meanshift') {
                    data = await runMeanShift(points.value, parseFloat(bandwidth.value));
                }

                if (data && data.success) {
                    history.value = data.history;
                    // Auto-jump to the last step
                    currentStep.value = history.value.length - 1;
                    drawStep(points.value, history.value[currentStep.value]);
                } else {
                    alert('Ошибка: ' + (data ? data.error : 'Неизвестная ошибка'));
                }
            } catch (e) {
                console.error(e);
                alert('Ошибка сервера');
            } finally {
                isRunning.value = false;
            }
        };

        const viewDendrogram = async () => {
            if (points.value.length < 2) {
                alert('Нужно минимум 2 точки для дендрограммы');
                return;
            }
            isRunning.value = true;
            try {
                const data = await getDendrogram(points.value);
                if (data.success) {
                    showDendrogram.value = true;
                    // Render dendrogram in modal
                    setTimeout(() => {
                        renderDendrogram(data.dendrogram);
                    }, 100);
                } else {
                    alert('Ошибка: ' + data.error);
                }
            } catch (e) {
                console.error(e);
                alert('Ошибка сервера');
            } finally {
                isRunning.value = false;
            }
        };

        const renderDendrogram = (dendroData) => {
            const { icoord, dcoord } = dendroData;
            
            const traces = [];

            // Draw lines (Dendrogram branches) only - cleaner look
            for (let i = 0; i < icoord.length; i++) {
                traces.push({
                    x: icoord[i],
                    y: dcoord[i],
                    mode: 'lines',
                    line: { color: '#3b82f6', width: 2 }, // Blue lines
                    showlegend: false,
                    hoverinfo: 'skip'
                });
            }

            const layout = {
                title: {
                    text: 'Дендрограмма',
                    font: { color: '#f1f5f9', size: 18 }
                },
                paper_bgcolor: '#1e293b',
                plot_bgcolor: '#1e293b',
                font: { color: '#94a3b8' },
                margin: { t: 50, b: 50, l: 60, r: 20 },
                xaxis: {
                    showgrid: false,
                    zeroline: false,
                    showticklabels: false,
                    title: { text: 'Точки (Образцы)', font: { color: '#94a3b8' } }
                },
                yaxis: {
                    showgrid: true,
                    gridcolor: '#334155',
                    zeroline: false,
                    title: { text: 'Расстояние', font: { color: '#94a3b8' } },
                    tickfont: { color: '#cbd5e1' }
                }
            };

            Plotly.newPlot('dendrogram-plot', traces, layout, { responsive: true, displayModeBar: false });
        };

        const closeDendrogram = () => {
            showDendrogram.value = false;
        };

        const clearPoints = () => {
            points.value = [];
            history.value = [];
            currentStep.value = 0;
            selectedPreset.value = '';
            initPlot();
        };

        // Navigation
        const nextStep = () => { if (currentStep.value < history.value.length - 1) currentStep.value++; };
        const prevStep = () => { if (currentStep.value > 0) currentStep.value--; };
        const setStep = (val) => { currentStep.value = val; };

        // Watchers
        watch(currentStep, (newVal) => { 
            if (history.value.length > 0) drawStep(points.value, history.value[newVal]); 
        });
        watch(algorithm, () => { clearPoints(); });
        watch(selectedPreset, () => { if (selectedPreset.value) loadPreset(); });

        onMounted(() => {
            setTimeout(initPlot, 100);
        });

        return {
            algorithm, k, eps, minPts, radius, bandwidth, points, history, currentStep, isRunning,
            selectedPreset, loadPreset, showDendrogram,
            runAlgorithm, nextStep, prevStep, setStep, clearPoints, handleCanvasClick,
            viewDendrogram, closeDendrogram
        };
    }
});

app.mount('#app');
