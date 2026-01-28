"""Dataset preset generators for clustering algorithms"""
import numpy as np
from sklearn.datasets import make_moons, make_circles, make_blobs

def generate_preset(preset_type: str, n_samples: int = 100):
    """
    Generate predefined datasets for clustering visualization.
    
    Args:
        preset_type: 'moons', 'circles', 'blobs', 'grid', 'hierarchy', 'dense_sparse'
        n_samples: Number of points to generate
    
    Returns:
        List of [x, y] coordinates scaled to [0, 10] range
    """
    if preset_type == 'moons':
        X, _ = make_moons(n_samples=n_samples, noise=0.08, random_state=42)
    elif preset_type == 'circles':
        X, _ = make_circles(n_samples=n_samples, noise=0.05, factor=0.5, random_state=42)
    elif preset_type == 'blobs':
        X, _ = make_blobs(n_samples=n_samples, centers=3, cluster_std=0.6, random_state=42)
    elif preset_type == 'grid':
        # Custom grid pattern
        side = int(np.sqrt(n_samples))
        x = np.linspace(0, 1, side)
        y = np.linspace(0, 1, side)
        xx, yy = np.meshgrid(x, y)
        X = np.column_stack([xx.ravel(), yy.ravel()])[:n_samples]
    elif preset_type == 'hierarchy':
        # Two large super-clusters, each containing 2 smaller clusters
        # Group 1
        X1, _ = make_blobs(n_samples=n_samples // 2, centers=[(0,0), (2,2)], cluster_std=0.4, random_state=1)
        # Group 2 (far away)
        X2, _ = make_blobs(n_samples=n_samples // 2, centers=[(8,8), (10,6)], cluster_std=0.4, random_state=2)
        X = np.vstack([X1, X2])
    elif preset_type == 'dense_sparse':
        # One very dense cluster and one sparse cluster
        X1, _ = make_blobs(n_samples=int(n_samples * 0.7), centers=[(0,0)], cluster_std=0.3, random_state=1)
        X2, _ = make_blobs(n_samples=int(n_samples * 0.3), centers=[(5,5)], cluster_std=1.5, random_state=2)
        X = np.vstack([X1, X2])
    else:
        raise ValueError(f"Unknown preset type: {preset_type}")
    
    # Normalize with Aspect Ratio Preservation
    X_min = X.min(axis=0)
    X_max = X.max(axis=0)
    
    # Calculate scale factor to fit in 8x8 box (leaving margin)
    ranges = X_max - X_min
    max_range = ranges.max()
    if max_range == 0:
        scale = 1
    else:
        scale = 8.0 / max_range
    
    # Center the data first (around 0) -> Scale -> Move to 5,5
    # Careful: If we just subtract X_min, we shift to corner.
    # Center of mass of bounding box:
    center = (X_max + X_min) / 2
    
    X_centered = (X - center) * scale # Now centered at 0,0 with size <= 8
    X_final = X_centered + 5.0 # Move to center of 10x10 field
    
    return X_final.tolist()
