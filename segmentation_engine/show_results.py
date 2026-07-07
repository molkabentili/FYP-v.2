import json
import pandas as pd

# Read metadata
with open('api_data/improved_segmentation_metadata.json', 'r') as f:
    metadata = json.load(f)

print('='*80)
print('IMPROVED SEGMENTATION RESULTS')
print('='*80)

print('\nSegment Profiles:')
for cid, profile in metadata['segment_profiles'].items():
    print(f'\nCluster {cid}:')
    print(f'  Size: {profile["size"]} ({profile["pct"]:.1f}%)')
    print(f'  ARPU: {profile["avg_arpu"]:.2f} TND')
    print(f'  Data: {profile["avg_data_gb"]:.2f} GB')
    print(f'  Voice: {profile["avg_voice_min"]:.0f} min')
    print(f'  Tenure: {profile["avg_tenure"]:.1f} months')
    print(f'  Churn Risk: {profile["churn_risk_pct"]:.1f}%')
    print(f'  Satisfaction: {profile["avg_satisfaction"]:.2f}/5')

print(f'\n\nSegment Names:')
for cid, name in metadata['segment_names'].items():
    print(f'  Cluster {cid}: {name}')

# Read CSV and show sample
df = pd.read_csv('api_data/segmented_improved_kmeans.csv')
print(f'\n\nDataset: {len(df)} rows')
print(f'Columns: {df.columns.tolist()}')
print(f'\nCluster distribution:')
print(df['cluster'].value_counts().sort_index())

print("\n" + "="*80)
print("COMPARISON VS ORIGINAL SEGMENTATION")
print("="*80)

# Load original
df_orig = pd.read_csv('api_data/segmented_kmeans_500.csv')

print(f"\nOriginal segmentation: {len(df_orig)} rows, {df_orig['cluster'].max() + 1} clusters")
print(f"Improved segmentation: {len(df)} rows, {df['cluster'].max() + 1} clusters")

print("\nOriginal cluster distribution:")
print(df_orig['cluster'].value_counts().sort_index())

print("\nImproved cluster distribution:")
print(df['cluster'].value_counts().sort_index())

# Compare key metrics
print("\n" + "-"*80)
print("METRIC COMPARISON: Original vs Improved")
print("-"*80)

orig_profiles = {}
for cluster_id in sorted(df_orig['cluster'].unique()):
    cluster_data = df_orig[df_orig['cluster'] == cluster_id]
    orig_profiles[cluster_id] = {
        'arpu': cluster_data['monthly_spend'].mean(),
        'data': cluster_data['data_consumption_gb'].mean(),
        'voice': cluster_data['voice_minutes'].mean(),
    }

print("\nOriginal:")
for cid, prof in orig_profiles.items():
    print(f"  Cluster {cid}: ARPU={prof['arpu']:.0f}, Data={prof['data']:.2f}, Voice={prof['voice']:.0f}")

print("\nImproved:")
for cid in sorted(metadata['segment_profiles'].keys()):
    prof = metadata['segment_profiles'][cid]
    print(f"  Cluster {cid}: ARPU={prof['avg_arpu']:.0f}, Data={prof['avg_data_gb']:.2f}, Voice={prof['avg_voice_min']:.0f}")
