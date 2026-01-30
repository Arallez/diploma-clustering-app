import numpy as np
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
from scipy.spatial.distance import pdist, cdist

def normalize_points(points):
    """
    Convert points from list of dicts [{'x': 1, 'y': 2}] or list of lists 
    to numpy array [[1, 2]].
    """
    if not points:
        return np.array([])
    
    # If already numpy array, just return
    if isinstance(points, np.ndarray):
        return points

    # Check first element to see format
    first = points[0]
    if isinstance(first, dict) and 'x' in first and 'y' in first:
        return np.array([[p['x'], p['y']] for p in points])
    elif isinstance(first, (list, tuple)):
        return np.array(points)
    
    return np.array(points)

def kmeans_step(points, k):
    X = normalize_points(points)
    if len(X) < k:
        return []
    
    # Randomly initialize centroids
    indices = np.random.choice(len(X), k, replace=False)
    centroids = X[indices]
    
    history = []
    max_iters = 100
    
    for _ in range(max_iters):
        # Calculate distances
        distances = np.linalg.norm(X[:, np.newaxis] - centroids, axis=2)
        labels = np.argmin(distances, axis=1)
        
        step_data = {
            'centroids': [{'x': c[0], 'y': c[1]} for c in centroids],
            'labels': labels.tolist()
        }
        history.append(step_data)
        
        new_centroids = np.array([X[labels == i].mean(axis=0) if np.sum(labels == i) > 0 else centroids[i] for i in range(k)])
        
        if np.allclose(centroids, new_centroids):
            break
            
        centroids = new_centroids
        
    return history

def dbscan_step(points, eps, min_pts):
    X = normalize_points(points)
    n = len(X)
    labels = -1 * np.ones(n, dtype=int)  # -1 = noise
    visited = np.zeros(n, dtype=bool)
    cluster_id = 0
    history = []

    def get_neighbors(idx):
        return np.where(np.linalg.norm(X - X[idx], axis=1) <= eps)[0]

    for i in range(n):
        if visited[i]:
            continue
            
        visited[i] = True
        neighbors = get_neighbors(i)
        
        # Snapshot for visualization (visiting point i)
        history.append({
            'labels': labels.tolist(),
            'current': int(i),
            'neighbors': neighbors.tolist()
        })

        if len(neighbors) < min_pts:
            labels[i] = -1 # Noise
        else:
            labels[i] = cluster_id
            seeds = list(neighbors)
            if i in seeds:
                seeds.remove(i)
            
            while seeds:
                curr_p = seeds.pop(0)
                if not visited[curr_p]:
                    visited[curr_p] = True
                    curr_neighbors = get_neighbors(curr_p)
                    if len(curr_neighbors) >= min_pts:
                        seeds.extend(curr_neighbors)
                
                if labels[curr_p] == -1:
                    labels[curr_p] = cluster_id
            
            cluster_id += 1
            
            # Snapshot after forming a cluster
            history.append({
                'labels': labels.tolist(),
                'current': None,
                'neighbors': []
            })
            
    # Final state
    history.append({
        'labels': labels.tolist(),
        'current': None,
        'neighbors': []
    })
    
    return history

def forel_step(points, r):
    X = normalize_points(points)
    n = len(X)
    labels = -1 * np.ones(n, dtype=int)
    remaining_indices = np.arange(n)
    cluster_id = 0
    history = []
    
    while len(remaining_indices) > 0:
        # Pick random point as start center
        current_idx = np.random.choice(remaining_indices)
        center = X[current_idx]
        
        while True:
            # Find neighbors in radius R
            dists = np.linalg.norm(X[remaining_indices] - center, axis=1)
            neighbors_mask = dists <= r
            neighbors_indices = remaining_indices[neighbors_mask]
            
            step_data = {
                'labels': labels.tolist(),
                'center': {'x': center[0], 'y': center[1]},
                'radius': r,
                'active_indices': neighbors_indices.tolist()
            }
            history.append(step_data)
            
            if len(neighbors_indices) == 0:
                break
                
            new_center = np.mean(X[neighbors_indices], axis=0)
            
            if np.linalg.norm(new_center - center) < 1e-4:
                # Stabilized
                labels[neighbors_indices] = cluster_id
                
                # Remove clustered points
                remaining_mask = np.ones(len(remaining_indices), dtype=bool)
                remaining_mask[neighbors_mask] = False
                remaining_indices = remaining_indices[remaining_mask]
                
                cluster_id += 1
                break
            
            center = new_center
            
    # Final state
    history.append({
        'labels': labels.tolist(),
        'center': None,
        'radius': r,
        'active_indices': []
    })
            
    return history

def agglomerative_step(points, n_clusters):
    """
    Optimized Agglomerative Clustering using Scipy Linkage.
    """
    X = normalize_points(points)
    n = len(X)
    
    if n < 2:
        return [{'labels': [0] * n}]

    # 1. Compute Linkage Matrix (The Hierarchy) - Fast O(N^2)
    Z = linkage(X, method='ward')
    
    history = []
    
    # 2. Reconstruct steps from start_k down to target_k
    start_k = min(n, 50) # Start showing animation from 50 clusters to target k
    target_k = max(1, n_clusters)
    
    # We iterate k from start_k down to target_k
    for k in range(start_k, target_k - 1, -1):
        labels = fcluster(Z, k, criterion='maxclust')
        # fcluster returns 1-based labels, convert to 0-based
        labels = labels - 1
        history.append({'labels': labels.tolist()})
        
    if not history:
        # If we didn't enter the loop (e.g. n < start_k), add final state
        labels = fcluster(Z, target_k, criterion='maxclust') - 1
        history.append({'labels': labels.tolist()})

    return history

def mean_shift_step(points, bandwidth=1.0):
    """
    Optimized MeanShift using Vectorization.
    """
    X = normalize_points(points)
    n_samples = len(X)
    
    if n_samples == 0:
        return []
        
    centroids = np.copy(X)
    history = []
    
    max_iters = 100
    stop_thresh = 1e-3 * bandwidth
    
    for it in range(max_iters):
        old_centroids = np.copy(centroids)
        
        # Vectorized distance calculation (N x N)
        dists = cdist(centroids, centroids)
        
        # Weights matrix (N x N)
        weights = (dists <= bandwidth).astype(float)
        
        # Sum of weights for each point (denominator)
        denoms = weights.sum(axis=1, keepdims=True)
        
        # Avoid division by zero
        denoms[denoms == 0] = 1.0
        
        # New centroids
        new_centroids = np.dot(weights, centroids) / denoms
        
        # Visualization: Group nearby centroids
        rounded = np.round(new_centroids, decimals=1)
        unique_pos, inverse_indices = np.unique(rounded, axis=0, return_inverse=True)
        
        step_data = {
            'centroids': [{'x': float(c[0]), 'y': float(c[1])} for c in unique_pos],
            'labels': inverse_indices.tolist()
        }
        history.append(step_data)
        
        # Check convergence
        shift = np.linalg.norm(new_centroids - old_centroids, axis=1)
        if np.max(shift) < stop_thresh:
            break
            
        centroids = new_centroids

    return history

def compute_dendrogram_data(points):
    """
    Compute dendrogram data and return JSON-serializable structure.
    """
    X = normalize_points(points)
    if len(X) < 2:
        return {'error': "Need at least 2 points"}
        
    Z = linkage(X, method='ward')
    ddata = dendrogram(Z, no_plot=True)
    
    # Fix JSON serialization error (numpy float32 is not JSON serializable)
    def clean_floats(obj):
        if isinstance(obj, list):
            return [clean_floats(x) for x in obj]
        elif isinstance(obj, dict):
            return {k: clean_floats(v) for k, v in obj.items()}
        elif hasattr(obj, 'item'): # numpy scalar
            return obj.item()
        return obj

    return clean_floats(ddata)
