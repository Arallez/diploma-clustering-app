export async function runKMeans(points, k) {
    const response = await fetch('/simulator/api/run-kmeans/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ points, k })
    });
    return await response.json();
}

export async function runDBSCAN(points, eps, min_pts) {
    const response = await fetch('/simulator/api/run-dbscan/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ points, eps, min_pts })
    });
    return await response.json();
}
