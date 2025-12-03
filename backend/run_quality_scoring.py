"""
Script to compute and display cluster quality metrics.
"""
from backend.cluster_quality import compute_cluster_quality
import json


def main():
    """Compute and display cluster quality metrics."""
    print("=" * 70)
    print("CLUSTER QUALITY SCORING")
    print("=" * 70)
    print("\nComputing quality metrics for all cluster types...")
    print("This may take a few minutes...\n")
    
    results = compute_cluster_quality()
    
    print("\n" + "=" * 70)
    print("QUALITY METRICS SUMMARY")
    print("=" * 70)
    
    # Print formatted results
    print(json.dumps(results, indent=2))
    
    print("\n" + "=" * 70)
    print("INTERPRETATION")
    print("=" * 70)
    print("Quality Score:")
    print("  - high: Excellent cluster quality (high homogeneity, good separation)")
    print("  - medium: Good cluster quality (balanced)")
    print("  - low: Lower cluster quality (may need refinement)")
    print("\nIntra-cluster Similarity:")
    print("  - Higher values (closer to 1.0) = more homogeneous clusters")
    print("  - Lower values = more diverse tickets within clusters")
    print("\nInter-cluster Distance:")
    print("  - Higher values (closer to 2.0) = better separation between clusters")
    print("  - Lower values = clusters are more similar to each other")
    print("=" * 70)


if __name__ == "__main__":
    main()

