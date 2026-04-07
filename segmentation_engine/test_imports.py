import sys
print("✓ Python works")
try:
    from src.clustering import SegmentationEngine
    print("✓ Clustering module loaded")
    from src.pipeline import DataPreprocessor
    print("✓ Pipeline module loaded")
    print("\n✅ All imports successful! Sprint 3 ready to test.")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
