export async function runKMeans(points, k) {
    const response = await fetch('/simulator/api/run-kmeans/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ points, k })
    });
    return await response.json();
}

export async function runDBSCAN(points, eps, minPts) {
    const response = await fetch('/simulator/api/run-dbscan/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ points, eps, min_pts: minPts })
    });
    return await response.json();
}

export async function runForel(points, r) {
    const response = await fetch('/simulator/api/run-forel/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ points, r })
    });
    return await response.json();
}

export async function runAgglomerative(points, n_clusters) {
    const response = await fetch('/simulator/api/run-agglomerative/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ points, n_clusters })
    });
    return await response.json();
}

export async function getDendrogram(points) {
    const response = await fetch('/simulator/api/get-dendrogram/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ points })
    });
    return await response.json();
}

export async function generatePreset(type, nSamples = 100) {
    const response = await fetch('/simulator/api/generate-preset/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type, n_samples: nSamples })
    });
    return await response.json();
}
