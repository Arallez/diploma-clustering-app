"""Algorithm implementations for clustering simulation"""
import numpy as np
from typing import List, Tuple, Dict

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
    indices = np.random.choice(n, size=k, replace=False)
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
