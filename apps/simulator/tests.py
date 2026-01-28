from django.test import TestCase
from .algorithms import forel_step, agglomerative_step, compute_dendrogram_data

class ClusteringAlgorithmsTestCase(TestCase):
    def setUp(self):
        # Sample points for testing: Two distinct groups
        # Group 1 (near 0,0)
        self.points_group1 = [
            {'x': 0, 'y': 0},
            {'x': 0.1, 'y': 0.1},
            {'x': 0, 'y': 0.1}
        ]
        # Group 2 (near 10,10)
        self.points_group2 = [
            {'x': 10, 'y': 10},
            {'x': 10.1, 'y': 10.1},
            {'x': 10, 'y': 10.1}
        ]
        self.all_points = self.points_group1 + self.points_group2

    # --- FOREL TESTS ---

    def test_forel_large_radius(self):
        """
        FOREL with a large radius (R=20) should group everything into 1 cluster.
        """
        r = 20.0
        history = forel_step(self.all_points, r)
        
        # Get the final frame labels
        final_labels = history[-1]['labels']
        unique_clusters = set(final_labels)
        
        # Should be exactly 1 cluster (label 0)
        self.assertEqual(len(unique_clusters), 1, "Large radius should result in 1 cluster")
        self.assertIn(0, unique_clusters)

    def test_forel_small_radius(self):
        """
        FOREL with a small radius (R=0.5) should separate the two distant groups.
        """
        r = 0.5
        history = forel_step(self.all_points, r)
        
        final_labels = history[-1]['labels']
        unique_clusters = set(final_labels)
        
        # Should be at least 2 clusters
        self.assertTrue(len(unique_clusters) >= 2, "Small radius should find at least 2 clusters")
        
        # Check that points in group 1 have same label
        group1_labels = final_labels[:3]
        self.assertEqual(len(set(group1_labels)), 1, "Group 1 points should be in same cluster")
        
        # Check that points in group 2 have same label
        group2_labels = final_labels[3:]
        self.assertEqual(len(set(group2_labels)), 1, "Group 2 points should be in same cluster")
        
        # Check that group 1 and group 2 have DIFFERENT labels
        self.assertNotEqual(group1_labels[0], group2_labels[0], "Distant groups should have different labels")

    # --- AGGLOMERATIVE TESTS ---

    def test_agglomerative_exact_clusters(self):
        """
        Agglomerative should stop exactly when n_clusters is reached.
        """
        target_k = 2
        history = agglomerative_step(self.all_points, n_clusters=target_k)
        
        final_labels = history[-1]['labels']
        unique_clusters = set(final_labels)
        
        self.assertEqual(len(unique_clusters), target_k, f"Should result in exactly {target_k} clusters")

    def test_agglomerative_logic(self):
        """
        Agglomerative: Distant points should end up in different clusters if K=2.
        """
        history = agglomerative_step(self.all_points, n_clusters=2)
        final_labels = history[-1]['labels']
        
        # Group 1 (indices 0,1,2) should differ from Group 2 (indices 3,4,5)
        self.assertEqual(final_labels[0], final_labels[1])
        self.assertEqual(final_labels[3], final_labels[4])
        self.assertNotEqual(final_labels[0], final_labels[3])

    # --- DENDROGRAM TESTS ---

    def test_dendrogram_structure(self):
        """
        Check if dendrogram returns correct dictionary structure for Plotly.
        """
        data = compute_dendrogram_data(self.all_points)
        
        self.assertIn('icoord', data)
        self.assertIn('dcoord', data)
        self.assertIn('ivl', data)
        self.assertIn('leaves', data)
        
        # Length of coordinate lists should match (number of merge steps)
        # For N points, there are N-1 merges
        n_merges = len(self.all_points) - 1
        self.assertEqual(len(data['icoord']), n_merges)
        self.assertEqual(len(data['dcoord']), n_merges)

    def test_dendrogram_empty(self):
        """Check behavior with too few points"""
        with self.assertRaises(ValueError):
            compute_dendrogram_data([{'x':0, 'y':0}]) # Only 1 point
