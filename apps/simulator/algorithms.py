"""Algorithm implementations for clustering simulation"""
import numpy as np
from typing import List, Tuple, Dict
from scipy.spatial.distance import pdist, squareform

def euclidean_distance(p1, p2):
    return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def kmeans_step(points: List[List[float]], k: int, max_iterations: int = 20) -> List[Dict]:
    """
    K-Means clustering with step-by-step history.
    Returns list of steps: [{centroids: [[x,y],...], labels: [0,1,2,...]}]
    """
    points = np.array(points)
    n = len(points)
    
    # Random initial centroids
    indices = np.random.choice(n, size=min(k, n), replace=False)
    centroids = points[indices].tolist()
    
    history = []
    
    for iteration in range(max_iterations):
        # Assign labels
        labels = []
        for point in points:
            distances = [euclidean_distance(point, c) for c in centroids]
            labels.append(int(np.argmin(distances)))
        
        history.append({'centroids': centroids.copy(), 'labels': labels.copy()})
        
        # Update centroids
        new_centroids = []
        for i in range(k):
            cluster_points = points[np.array(labels) == i]
            if len(cluster_points) > 0:
                new_centroids.append(cluster_points.mean(axis=0).tolist())
            else:
                new_centroids.append(centroids[i])  # Keep old if empty
        
        # Check convergence
        if np.allclose(centroids, new_centroids, atol=0.01):
            break
        centroids = new_centroids
    
    return history


def dbscan_step(points: List[List[float]], eps: float, min_pts: int) -> List[Dict]:
    """
    DBSCAN clustering with step visualization.
    Returns history showing cluster assignment progression.
    """
    points = np.array(points)
    n = len(points)
    labels = [-1] * n  # -1 = noise
    cluster_id = 0
    visited = [False] * n
    history = []
    
    def region_query(point_idx):
        neighbors = []
        for i in range(n):
            if euclidean_distance(points[point_idx], points[i]) <= eps:
                neighbors.append(i)
        return neighbors
    
    def expand_cluster(point_idx, neighbors, cluster_id):
        labels[point_idx] = cluster_id
        i = 0
        while i < len(neighbors):
            neighbor_idx = neighbors[i]
            if not visited[neighbor_idx]:
                visited[neighbor_idx] = True
                neighbor_neighbors = region_query(neighbor_idx)
                if len(neighbor_neighbors) >= min_pts:
                    neighbors.extend([n for n in neighbor_neighbors if n not in neighbors])
            if labels[neighbor_idx] == -1:
                labels[neighbor_idx] = cluster_id
            i += 1
        history.append({'labels': labels.copy()})
    
    for i in range(n):
        if visited[i]:
            continue
        visited[i] = True
        neighbors = region_query(i)
        
        if len(neighbors) < min_pts:
            labels[i] = -1  # Mark as noise
        else:
            expand_cluster(i, neighbors, cluster_id)
            cluster_id += 1
    
    # Add final state if no steps recorded
    if not history:
        history.append({'labels': labels})
    
    return history

def forel_step(points: List[List[float]], r: float) -> List[Dict]:
    """
    FOREL (FOrmal ELement) clustering algorithm.
    Soviet heuristic algorithm:
    1. Pick random point.
    2. Build sphere radius R.
    3. Find center of mass of points in sphere -> New center.
    4. Repeat until center stabilizes.
    5. Remove points, repeat.
    """
    points = np.array(points)
    n = len(points)
    labels = [-1] * n
    remaining_indices = list(range(n))
    cluster_id = 0
    history = []
    
    # Iterate until no points left
    while remaining_indices:
        # 1. Pick random point from remaining
        current_idx = np.random.choice(remaining_indices)
        center = points[current_idx]
        
        # Move center to stable position
        while True:
            # Find neighbors in radius R (among ALL points or Remaining? Usually remaining for removal, but density is global. 
            # Classic FOREL removes points from consideration. Let's strictly follow "remove them".)
            
            # Distance from current center to all REMAINING points
            distances = np.linalg.norm(points[remaining_indices] - center, axis=1)
            neighbors_mask = distances <= r
            neighbor_indices = [remaining_indices[i] for i in range(len(remaining_indices)) if neighbors_mask[i]]
            
            if not neighbor_indices:
                break
                
            # Calculate new center (center of mass)
            sphere_points = points[neighbor_indices]
            new_center = sphere_points.mean(axis=0)
            
            # Check convergence
            if np.allclose(center, new_center, atol=0.001):
                # Cluster found!
                # Mark points
                for idx in neighbor_indices:
                    labels[idx] = cluster_id
                
                # Record step
                history.append({'labels': labels.copy(), 'centroids': [new_center.tolist()]})
                
                # Remove points from remaining
                remaining_indices = [idx for idx in remaining_indices if idx not in neighbor_indices]
                cluster_id += 1
                break
            
            center = new_center
            # Optional: Visualize moving center? For now just visualize finalized clusters.
            
    if not history:
        history.append({'labels': labels})
        
    return history

def agglomerative_step(points: List[List[float]], n_clusters: int) -> List[Dict]:
    """
    Agglomerative Hierarchical Clustering (bottom-up).
    Start with N clusters, merge closest pair until K clusters remain.
    """
    points = np.array(points)
    n = len(points)
    
    # Initial: each point is a cluster
    labels = np.arange(n)
    history = [{'labels': labels.tolist()}]
    
    current_n_clusters = n
    
    while current_n_clusters > n_clusters:
        # Find closest pair of clusters (Single Linkage for simplicity/speed)
        min_dist = float('inf')
        merge_pair = (-1, -1)
        
        # This is O(N^3) naive, OK for N=100 in simulator
        # Better: Precompute distance matrix, but we need cluster distances.
        # Single Linkage: min distance between any two points in clusters A and B
        
        # Compute centroid distances for "Centroid Linkage" (easier to code efficiently)
        # OR Single Linkage: dist(A,B) = min(dist(a,b)) for a in A, b in B
        
        # Let's use Ward's method or Centroid for better visual results usually, 
        # but Single is standard "simplest". Let's do Centroid for now (points are their own centroids initially).
        
        # Construct clusters
        clusters = {}
        for idx, label in enumerate(labels):
            if label not in clusters: clusters[label] = []
            clusters[label].append(points[idx])
            
        cluster_ids = list(clusters.keys())
        
        # Calculate centroids of current clusters
        centroids = {cid: np.mean(pts, axis=0) for cid, pts in clusters.items()}
        
        # Find closest pair of CENTROIDS (Centroid Linkage-ish)
        for i in range(len(cluster_ids)):
            for j in range(i + 1, len(cluster_ids)):
                cid1 = cluster_ids[i]
                cid2 = cluster_ids[j]
                d = np.linalg.norm(centroids[cid1] - centroids[cid2])
                if d < min_dist:
                    min_dist = d
                    merge_pair = (cid1, cid2)
        
        if merge_pair == (-1, -1):
            break
            
        # Merge
        c1, c2 = merge_pair
        # Relabel c2 points to c1
        labels[labels == c2] = c1
        
        history.append({'labels': labels.tolist()})
        current_n_clusters -= 1
        
    return history
