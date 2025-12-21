"""Test Manifestator Shub drift detection"""

import pytest


@pytest.mark.asyncio
async def test_drift_detector_initialization():
    """Test drift detector initialization"""
    from manifestator.manifestator_shub_bridge import ShubDriftDetector
    
    detector = ShubDriftDetector()
    assert len(detector.baseline_hashes) == 0


@pytest.mark.asyncio
async def test_drift_report_generation():
    """Test drift report generation"""
    from manifestator.manifestator_shub_bridge import ShubDriftDetector
    
    detector = ShubDriftDetector()
    report = detector.get_drift_report()
    
    assert "report_timestamp" in report
    assert "total_modules" in report
    assert "drift_events" in report


@pytest.mark.asyncio
async def test_manifestator_bridge():
    """Test Manifestator-Shub bridge"""
    from manifestator.manifestator_shub_bridge import ManifestatorShubBridge
    
    config = {
        "manifestator_url": "http://manifestator:8005",
        "token": "test_token",
    }
    
    bridge = ManifestatorShubBridge(config)
    assert bridge.detector is not None


@pytest.mark.asyncio
async def test_drift_report():
    """Test drift report generation via bridge"""
    from manifestator.manifestator_shub_bridge import ManifestatorShubBridge
    
    config = {"manifestator_url": "http://manifestator:8005", "token": "test"}
    bridge = ManifestatorShubBridge(config)
    
    report = bridge.detector.get_drift_report()
    
    assert "report_timestamp" in report


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
