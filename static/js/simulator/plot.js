const PLOT_ID = 'plot';

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

export function initPlot() {
    const plotDiv = document.getElementById(PLOT_ID);
    if (!plotDiv) return;
    
    Plotly.newPlot(PLOT_ID, [{
        x: [], y: [], mode: 'markers', type: 'scatter', hoverinfo: 'none'
    }], getBaseLayout(), { 
        displayModeBar: false, 
        responsive: true,
        staticPlot: false 
    });
}

export function drawPoints(points) {
    const trace = {
        x: points.map(p => p[0]),
        y: points.map(p => p[1]),
        mode: 'markers',
        type: 'scatter',
        marker: { size: 10, color: '#e2e8f0', line: { color: '#000', width: 1 } },
        name: 'Points',
        hoverinfo: 'none'
    };
    Plotly.react(PLOT_ID, [trace], getBaseLayout(), { displayModeBar: false });
}

export function drawStep(points, stepData) {
    if (!stepData) return;
    const traces = [];
    const colors = ['#ef4444', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899'];

    if (stepData.labels) {
        const maxLabel = Math.max(...stepData.labels);
        const clusters = Array.from({ length: maxLabel + 1 }, () => []);
        const noise = [];
        
        points.forEach((point, index) => {
            const label = stepData.labels[index];
            if (label === -1) {
                noise.push(point);
            } else if (clusters[label]) {
                clusters[label].push(point);
            }
        });

        // Noise
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

        // Clusters
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
    
    Plotly.react(PLOT_ID, traces, getBaseLayout(), { displayModeBar: false });
}

export function convertClickToPoint(event) {
    const plotDiv = document.getElementById(PLOT_ID);
    if (!plotDiv || !plotDiv._fullLayout) return null;

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
        return [xVal, yVal];
    }
    return null;
}
