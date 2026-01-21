"""Dataset preset generators for clustering algorithms"""
import numpy as np
from sklearn.datasets import make_moons, make_circles, make_blobs

def generate_preset(preset_type: str, n_samples: int = 100):
    """
    Generate predefined datasets for clustering visualization.
    
    Args:
        preset_type: 'moons', 'circles', 'blobs', 'grid'
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
    else:
        raise ValueError(f"Unknown preset type: {preset_type}")
    
    # Normalize to [0, 10] range
    X_min, X_max = X.min(axis=0), X.max(axis=0)
    X_normalized = (X - X_min) / (X_max - X_min) * 9 + 0.5  # Scale to [0.5, 9.5]
    
    return X_normalized.tolist()
