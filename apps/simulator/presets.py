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
    
    # Normalize with Aspect Ratio Preservation
    X_min = X.min(axis=0)
    X_max = X.max(axis=0)
    
    # Calculate scale factor to fit in 8x8 box (leaving margin)
    ranges = X_max - X_min
    max_range = ranges.max()
    scale = 8.0 / max_range
    
    # Center the data
    X_centered = X - X_min - (ranges / 2) # Center around 0
    
    # Scale and move to center of 10x10 grid (5, 5)
    X_final = X_centered * scale + 5.0
    
    return X_final.tolist()
