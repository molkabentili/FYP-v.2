from segmentation_engine.src.clustering import SegmentationEngine
from segmentation_engine.src.pipeline import DataPreprocessor


def test_core_modules_import():
    assert SegmentationEngine is not None
    assert DataPreprocessor is not None
