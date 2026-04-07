#!/usr/bin/env python3
"""Sprint 3: Clustering Runner

CLI interface for customer segmentation.
Takes preprocessed data from Sprint 2 and applies clustering algorithms.

Usage:
    python run_clustering.py --input preprocessed_data.csv --algorithm kmeans --clusters 3
    python run_clustering.py --input cleaned.csv --algorithm hierarchical --linkage ward
    python run_clustering.py --input clean.csv --algorithm dbscan --eps 0.5 --min-samples 5
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

import pandas as pd

from src.clustering import SegmentationEngine


def run_kmeans(engine: SegmentationEngine, data: pd.DataFrame, args: argparse.Namespace) -> dict:
    """Execute K-Means clustering."""
    print(f"🔵 Running K-Means (k={args.clusters})...")
    result = engine.segment_with_kmeans(
        data,
        n_clusters=args.clusters,
        random_state=42,
        n_init=10
    )
    
    # Add per-cluster statistics
    stats = engine.get_cluster_statistics(result['labels'])
    result['statistics'] = stats
    
    print(f"   ✓ Created {args.clusters} clusters")
    print(f"   ✓ Silhouette: {result['metrics'].get('silhouette', 'N/A'):.3f}")
    print(f"   ✓ Davies-Bouldin: {result['metrics'].get('davies_bouldin', 'N/A'):.3f}")
    
    return result


def run_hierarchical(engine: SegmentationEngine, data: pd.DataFrame, args: argparse.Namespace) -> dict:
    """Execute Hierarchical clustering."""
    linkage = getattr(args, 'linkage', 'ward')
    print(f"🟢 Running Hierarchical ({linkage} linkage, k={args.clusters})...")
    result = engine.segment_with_hierarchical(
        data,
        n_clusters=args.clusters,
        linkage=linkage
    )
    
    # Add per-cluster statistics
    stats = engine.get_cluster_statistics(result['labels'])
    result['statistics'] = stats
    
    print(f"   ✓ Created {args.clusters} clusters")
    print(f"   ✓ Silhouette: {result['metrics'].get('silhouette', 'N/A'):.3f}")
    print(f"   ✓ Davies-Bouldin: {result['metrics'].get('davies_bouldin', 'N/A'):.3f}")
    
    return result


def run_dbscan(engine: SegmentationEngine, data: pd.DataFrame, args: argparse.Namespace) -> dict:
    """Execute DBSCAN clustering."""
    eps = getattr(args, 'eps', 0.5)
    min_samples = getattr(args, 'min_samples', 5)
    print(f"🟠 Running DBSCAN (eps={eps}, min_samples={min_samples})...")
    result = engine.segment_with_dbscan(
        data,
        eps=eps,
        min_samples=min_samples
    )
    
    # Add per-cluster statistics
    stats = engine.get_cluster_statistics(result['labels'])
    result['statistics'] = stats
    
    print(f"   ✓ Discovered {result['n_clusters']} clusters")
    print(f"   ✓ Noise points: {result['n_noise_points']}")
    print(f"   ✓ Silhouette: {result['metrics'].get('silhouette', 'N/A')}")
    
    return result


def save_results(result: dict, output_file: str) -> None:
    """Save clustering results to JSON."""
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n✅ Results saved to {output_file}")


def export_segmented_data(data: pd.DataFrame, labels: list, output_file: str) -> None:
    """Export data with cluster assignments."""
    result_df = data.copy()
    result_df['cluster'] = labels
    result_df.to_csv(output_file, index=False)
    print(f"✅ Segmented data saved to {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Customer Segmentation using Clustering Algorithms",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_clustering.py --input data.csv --algorithm kmeans --clusters 3
  python run_clustering.py --input data.csv --algorithm hierarchical --clusters 3 --linkage ward
  python run_clustering.py --input data.csv --algorithm dbscan --eps 0.5 --min-samples 5
  python run_clustering.py --input data.csv --algorithm all  # Run all 3 algorithms
        """
    )
    
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Path to preprocessed CSV file'
    )
    
    parser.add_argument(
        '--algorithm', '-a',
        choices=['kmeans', 'hierarchical', 'dbscan', 'all'],
        default='kmeans',
        help='Clustering algorithm to use (default: kmeans)'
    )
    
    parser.add_argument(
        '--clusters', '-c',
        type=int,
        default=3,
        help='Number of clusters for K-Means/Hierarchical (default: 3)'
    )
    
    parser.add_argument(
        '--linkage', '-l',
        choices=['ward', 'complete', 'average', 'single'],
        default='ward',
        help='Linkage criterion for Hierarchical (default: ward)'
    )
    
    parser.add_argument(
        '--eps',
        type=float,
        default=0.5,
        help='Epsilon for DBSCAN (default: 0.5)'
    )
    
    parser.add_argument(
        '--min-samples',
        type=int,
        default=5,
        help='Min samples for DBSCAN (default: 5)'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Output JSON file (default: clustering_result.json)'
    )
    
    args = parser.parse_args()
    
    # Validate input file
    if not Path(args.input).exists():
        print(f"❌ Error: Input file '{args.input}' not found")
        sys.exit(1)
    
    # Load data
    print(f"\n📂 Loading {args.input}...")
    data = pd.read_csv(args.input)
    print(f"   ✓ Loaded {len(data)} rows × {len(data.columns)} columns")
    
    # Initialize clustering engine
    engine = SegmentationEngine()
    
    # Run clustering
    results = {
        'timestamp': datetime.now().isoformat(),
        'input_file': args.input,
        'data_shape': list(data.shape),
        'algorithms': {}
    }
    
    if args.algorithm in ['kmeans', 'all']:
        results['algorithms']['kmeans'] = run_kmeans(engine, data, args)
    
    if args.algorithm in ['hierarchical', 'all']:
        results['algorithms']['hierarchical'] = run_hierarchical(engine, data, args)
    
    if args.algorithm in ['dbscan', 'all']:
        results['algorithms']['dbscan'] = run_dbscan(engine, data, args)
    
    # Save results
    output_file = args.output or "clustering_result.json"
    save_results(results, output_file)
    
    # Export segmented data (using first algorithm run)
    first_algo = list(results['algorithms'].keys())[0]
    first_labels = results['algorithms'][first_algo]['labels']
    csv_output = output_file.replace('.json', '_segmented.csv')
    export_segmented_data(data, first_labels, csv_output)
    
    print("\n" + "="*60)
    print("CLUSTERING COMPLETE")
    print("="*60)


if __name__ == '__main__':
    main()
