/**
 * API Wrapper for Clustering Algorithms
 * Handles all HTTP requests to the Django backend
 */

const BASE_URL = '/simulator';

// Generic helper for POST requests
async function postData(endpoint, data) {
    const response = await fetch(`${BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    });
    return await response.json();
}

// Generic helper for GET requests
async function getData(endpoint, params = {}) {
    const query = new URLSearchParams(params).toString();
    const response = await fetch(`${BASE_URL}${endpoint}?${query}`);
    return await response.json();
}

/**
 * Run K-Means Algorithm
 * @param {Array} points - List of {x, y} objects
 * @param {Number} k - Number of clusters
 */
export const runKMeans = async (points, k) => {
    return await postData('/run/', {
        algorithm: 'kmeans',
        points: points,
        params: { k: k }
    });
};

/**
 * Run DBSCAN Algorithm
 * @param {Array} points - List of {x, y} objects
 * @param {Number} eps - Epsilon radius
 * @param {Number} minPts - Minimum points
 */
export const runDBSCAN = async (points, eps, minPts) => {
    return await postData('/run/', {
        algorithm: 'dbscan',
        points: points,
        params: { eps: eps, minPts: minPts }
    });
};

/**
 * Run FOREL Algorithm
 * @param {Array} points - List of {x, y} objects
 * @param {Number} radius - Sphere radius (R)
 */
export const runForel = async (points, radius) => {
    return await postData('/run/', {
        algorithm: 'forel',
        points: points,
        params: { radius: radius }
    });
};

/**
 * Run Agglomerative (Hierarchical) Algorithm
 * @param {Array} points - List of {x, y} objects
 * @param {Number} k - Number of clusters
 */
export const runAgglomerative = async (points, k) => {
    return await postData('/run/', {
        algorithm: 'agglomerative',
        points: points,
        params: { k: k }
    });
};

/**
 * Run MeanShift Algorithm
 * @param {Array} points - List of {x, y} objects
 * @param {Number} bandwidth - Bandwidth (radius)
 */
export const runMeanShift = async (points, bandwidth) => {
    return await postData('/run/', {
        algorithm: 'meanshift',
        points: points,
        params: { bandwidth: bandwidth }
    });
};

/**
 * Generate Preset Dataset
 * @param {String} name - Preset name (moons, blobs, circles)
 * @param {Number} samples - Number of points
 */
export const generatePreset = async (name, samples = 100) => {
    return await getData('/preset/', { name: name, samples: samples });
};

/**
 * Get Dendrogram Data
 * @param {Array} points - List of {x, y} objects
 */
export const getDendrogram = async (points) => {
    return await postData('/dendrogram/', {
        points: points
    });
};
