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

def mean_shift_step(points, bandwidth=1.0):
    X = normalize_points(points)
    n_samples = len(X)
    
    if n_samples == 0:
        return []
        
    # Start with each point being its own cluster center candidate
    centroids = np.copy(X)
    history = []
    
    max_iters = 100
    stop_thresh = 1e-3 * bandwidth
    
    for it in range(max_iters):
        new_centroids = np.zeros_like(centroids)
        
        # Save state before shift
        # To visualize, we assign each original point to its closest CURRENT centroid
        # But since centroids == points count initially, and they move... 
        # We group points by which final centroid they are converging to.
        # Simple viz: just show "shifting" centers isn't enough for the current UI.
        # Let's map original points to the index of the centroid they are tracking.
        # Actually, standard MeanShift groups points that converge to the SAME location.
        
        # For intermediate visualization:
        # We can try to cluster the current 'centroids' positions.
        # But easier: just record the centroids positions. The UI might need update to show them?
        # Re-using existing UI: 'centroids' field in history is used by K-Means.
        # We can pass 'centroids' to show the kernels moving.
        # 'labels' can be calculated by assigning each point X[i] to the nearest centroid[j].
        # Since centroid[i] "belongs" to X[i], this is trivial (label=i), which is rainbow chaos.
        
        # Better Viz Strategy:
        # 1. At each step, centroids move.
        # 2. We group centroids that are very close to each other.
        # 3. Assign label based on that group.
        
        # Quick grouping for visualization
        unique_centers = []
        labels = np.zeros(n_samples, dtype=int)
        
        # Simple rounding to group for viz (fast approx)
        # or just use first point as representative if close
        viz_centers = np.copy(centroids)
        active_indices = np.arange(n_samples) # All active initially
        
        # We won't do full grouping every frame, too slow.
        # Let's just output the current centroids positions.
        # We will assume every point i tracks centroid i.
        
        # To make it look like clustering, we need to detect convergence.
        
        step_data = {
            'centroids': [{'x': c[0], 'y': c[1]} for c in centroids],
            'labels': list(range(n_samples)) # Initially rainbow, will merge later?
            # Actually, without proper merging, it just looks like moving dots.
            # Let's implement real merging at the end, but for intermediate steps
            # we can show the "path".
        }
        # Ideally we want to show points merging.
        
        # Let's run the shift
        shift_happened = False
        for i in range(n_samples):
            # Find neighbors in bandwidth
            dists = np.linalg.norm(centroids - centroids[i], axis=1)
            weights = (dists <= bandwidth).astype(float) # Flat kernel
            # Gaussian kernel is better usually: exp(-d^2 / (2*bw^2))
            # But flat is standard "neighbors within radius" logic from presentation usually.
            # Let's use Flat kernel (like DBSCAN radius) for simplicity/speed.
            
            denom = np.sum(weights)
            if denom > 0:
                new_center = np.dot(weights, centroids) / denom
                new_centroids[i] = new_center
            else:
                new_centroids[i] = centroids[i]
                
            if np.linalg.norm(new_centroids[i] - centroids[i]) > stop_thresh:
                shift_happened = True
        
        centroids = np.copy(new_centroids)
        
        if not shift_happened:
            break

        # Post-processing for this step to create meaningful colors:
        # Group centroids that are within small distance
        # This is expensive O(N^2) every frame. Maybe just every 5 frames or at end?
        # Let's do it every step but simplified: round coordinates
        
        # We need meaningful labels for history.
        # Let's cluster the *current centroids* using a simple greedy approach
        rounded = np.round(centroids, decimals=1) 
        # Map rounded tuples to cluster IDs
        unique_pos = np.unique(rounded, axis=0)
        
        # Assign label based on nearest unique center
        # This gives the "merging" effect visually
        step_labels = []
        for c in centroids:
             # Find closest unique
             d = np.linalg.norm(unique_pos - c, axis=1)
             step_labels.append(int(np.argmin(d)))
             
        step_data['labels'] = step_labels
        step_data['centroids'] = [{'x': c[0], 'y': c[1]} for c in unique_pos] # Show merged centers
        
        history.append(step_data)

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
