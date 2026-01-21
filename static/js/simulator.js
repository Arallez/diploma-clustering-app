// Simulator for K-Means & DBSCAN (Vue.js Island)
const { createApp, ref, onMounted, watch } = Vue;

function initSimulatorApp() {
    return createApp({
        setup() {
            // State
            const algorithm = ref('kmeans');
            const k = ref(3);
            const eps = ref(1.0);
            const minPts = ref(3);
            const points = ref([]);
            const history = ref([]);
            const currentStep = ref(0);
            const isRunning = ref(false);

            const getBaseLayout = () => ({
                title: false,
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: { color: '#94a3b8' },
                margin: { t: 20, b: 40, l: 40, r: 20 },
                xaxis: { range: [0, 10], gridcolor: '#334155', zerolinecolor: '#475569', fixedrange: true },
                yaxis: { range: [0, 10], gridcolor: '#334155', zerolinecolor: '#475569', fixedrange: true },
                showlegend: true,
                legend: { x: 0, y: 1, bgcolor: 'rgba(30,41,59,0.8)' },
                hovermode: false, 
                dragmode: false
            });

            const initPlot = () => {
                const plotDiv = document.getElementById('plot');
                if (!plotDiv) return;
                Plotly.newPlot('plot', [{ x: [], y: [], mode: 'markers', type: 'scatter', hoverinfo: 'none' }], 
                    getBaseLayout(), { displayModeBar: false, responsive: true, staticPlot: false });
            };

            const handleCanvasClick = (event) => {
                if (history.value.length > 0) return;
                const plotDiv = document.getElementById('plot');
                if (plotDiv && plotDiv._fullLayout) {
                    const xaxis = plotDiv._fullLayout.xaxis;
                    const yaxis = plotDiv._fullLayout.yaxis;
                    const rect = plotDiv.getBoundingClientRect();
                    const xPx = event.clientX - rect.left;
                    const yPx = event.clientY - rect.top;
                    const marginL = plotDiv._fullLayout.margin.l;
                    const marginT = plotDiv._fullLayout.margin.t;
                    let xVal = xaxis.p2d(xPx - marginL);
                    let yVal = yaxis.p2d(yPx - marginT);
                    if (xVal >= 0 && xVal <= 10 && yVal >= 0 && yVal <= 10) {
                        points.value.push([xVal, yVal]);
                        drawPoints();
                    }
                }
            };

            const drawPoints = () => {
                const trace = {
                    x: points.value.map(p => p[0]),
                    y: points.value.map(p => p[1]),
                    mode: 'markers',
                    type: 'scatter',
                    marker: { size: 10, color: '#e2e8f0', line: { color: '#000', width: 1 } },
                    name: 'Points',
                    hoverinfo: 'none'
                };
                Plotly.react('plot', [trace], getBaseLayout(), { displayModeBar: false });
            };

            const drawStep = (stepIndex) => {
                const stepData = history.value[stepIndex];
                if (!stepData) return;
                const traces = [];
                const colors = ['#ef4444', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899'];

                if (stepData.labels) {
                    const maxLabel = Math.max(...stepData.labels);
                    const clusters = Array.from({ length: maxLabel + 1 }, () => []);
                    const noise = [];
                    
                    points.value.forEach((point, index) => {
                        const label = stepData.labels[index];
                        if (label === -1) {
                            noise.push(point);
                        } else if (clusters[label]) {
                            clusters[label].push(point);
                        }
                    });

                    // Draw noise points (gray)
                    if (noise.length > 0) {
                        traces.push({
                            x: noise.map(p => p[0]),
                            y: noise.map(p => p[1]),
                            mode: 'markers',
                            type: 'scatter',
                            name: 'Noise',
                            marker: { size: 8, color: '#64748b', symbol: 'x' }
                        });
                    }

                    // Draw clusters
                    clusters.forEach((clusterPoints, i) => {
                        if (clusterPoints.length > 0) {
                            traces.push({
                                x: clusterPoints.map(p => p[0]),
                                y: clusterPoints.map(p => p[1]),
                                mode: 'markers',
                                type: 'scatter',
                                name: `Cluster ${i+1}`,
                                marker: { size: 10, color: colors[i % colors.length] }
                            });
                        }
                    });
                }

                if (stepData.centroids && stepData.centroids.length > 0) {
                    traces.push({
                        x: stepData.centroids.map(c => c[0]),
                        y: stepData.centroids.map(c => c[1]),
                        mode: 'markers',
                        type: 'scatter',
                        name: 'Centroids',
                        marker: { symbol: 'x', size: 14, color: '#fff', line: { width: 3 } }
                    });
                }
                
                Plotly.react('plot', traces, getBaseLayout(), { displayModeBar: false });
            };

            const runAlgorithm = async () => {
                isRunning.value = true;
                try {
                    const endpoint = algorithm.value === 'kmeans' ? '/simulator/api/run-kmeans/' : '/simulator/api/run-dbscan/';
                    const body = algorithm.value === 'kmeans' 
                        ? { points: points.value, k: k.value }
                        : { points: points.value, eps: parseFloat(eps.value), min_pts: minPts.value };
                    
                    const response = await fetch(endpoint, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(body)
                    });
                    const data = await response.json();
                    if (data.success) {
                        history.value = data.history;
                        currentStep.value = 0;
                        drawStep(0);
                    } else {
                        alert('Error: ' + data.error);
                    }
                } catch (e) {
                    console.error(e);
                    alert('Server error');
                } finally {
                    isRunning.value = false;
                }
            };

            const nextStep = () => { if (currentStep.value < history.value.length - 1) currentStep.value++; };
            const prevStep = () => { if (currentStep.value > 0) currentStep.value--; };
            const setStep = (val) => { currentStep.value = val; };
            const clearPoints = () => {
                points.value = [];
                history.value = [];
                currentStep.value = 0;
                initPlot();
            };

            watch(currentStep, (newVal) => { if (history.value.length > 0) drawStep(newVal); });
            watch(algorithm, () => { clearPoints(); });

            onMounted(() => { setTimeout(initPlot, 100); });

            return {
                algorithm, k, eps, minPts, points, history, currentStep, isRunning,
                runAlgorithm, nextStep, prevStep, setStep, clearPoints, handleCanvasClick
            };
        }
    });
}

if (typeof window !== 'undefined') {
    window.initSimulatorApp = initSimulatorApp;
}
