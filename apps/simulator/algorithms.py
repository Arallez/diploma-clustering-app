import numpy as np
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import pdist

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
    X = normalize_points(points)
    n = len(X)
    
    # Initially each point is a cluster
    clusters = {i: [i] for i in range(n)} # cluster_id -> list of point indices
    labels = np.arange(n)
    history = []
    
    # Save initial state
    history.append({'labels': labels.tolist()})
    
    current_n_clusters = n
    
    while current_n_clusters > n_clusters:
        min_dist = float('inf')
        merge_pair = (-1, -1)
        
        # Prepare centroids
        cluster_ids = list(clusters.keys())
        centroids = {}
        for cid in cluster_ids:
            # points indices in this cluster
            p_indices = clusters[cid]
            # coordinates
            pts_coords = X[p_indices]
            centroids[cid] = np.mean(pts_coords, axis=0)
            
        # Brute force search for min distance between centroids
        for i in range(len(cluster_ids)):
            for j in range(i + 1, len(cluster_ids)):
                cid1 = cluster_ids[i]
                cid2 = cluster_ids[j]
                dist = np.linalg.norm(centroids[cid1] - centroids[cid2])
                
                if dist < min_dist:
                    min_dist = dist
                    merge_pair = (cid1, cid2)
        
        if merge_pair == (-1, -1):
            break
            
        # Merge
        c1, c2 = merge_pair
        clusters[c1].extend(clusters[c2])
        del clusters[c2]
        
        # Update labels
        for p_idx in clusters[c1]:
            labels[p_idx] = c1 # Keep the ID of the first cluster
            
        history.append({'labels': labels.tolist()})
        current_n_clusters -= 1
        
    return history

def compute_dendrogram_data(points):
    X = normalize_points(points)
    if len(X) < 2:
        # Need at least 2 points for linkage
        raise ValueError("Need at least 2 points for dendrogram")
        
    # Ward linkage
    Z = linkage(X, method='ward')
    
    # Get dendrogram data for plotting
    ddata = dendrogram(Z, no_plot=True)
    
    return ddata
