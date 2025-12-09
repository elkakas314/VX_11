"""Test database synchronization"""

import pytest
import asyncio


@pytest.mark.asyncio
async def test_bidirectional_sync():
    """Test asset sync from VX11 to Shub"""
    from shubniggurath.integrations.db_sync import BidirectionalSync
    
    sync = BidirectionalSync(None, None)
    
    asset_data = {
        "tenant_id": "tenant-1",
        "project_id": "project-1",
        "file_path": "/audio/test.wav",
        "file_name": "test.wav",
        "file_hash": b"hash123",
        "file_size": 1024000,
    }
    
    result = await sync.sync_asset_to_shub("task-1", asset_data)
    assert result is True


@pytest.mark.asyncio
async def test_analysis_sync_to_vx11():
    """Test analysis sync from Shub to VX11"""
    from shubniggurath.integrations.db_sync import BidirectionalSync
    
    sync = BidirectionalSync(None, None)
    
    analysis_data = {
        "loudness_lufs": -23.5,
        "bpm": 120.0,
        "key": "A",
    }
    
    result = await sync.sync_analysis_to_vx11("asset-1", analysis_data)
    assert result is True


@pytest.mark.asyncio
async def test_sync_log():
    """Test sync logging"""
    from shubniggurath.integrations.db_sync import BidirectionalSync
    
    sync = BidirectionalSync(None, None)
    
    # Perform sync
    await sync.sync_asset_to_shub("task-1", {
        "tenant_id": "t1",
        "file_path": "/test",
    })
    
    log = sync.get_sync_log()
    assert len(log) > 0


@pytest.mark.asyncio
async def test_sync_scheduler():
    """Test sync scheduler"""
    from shubniggurath.integrations.db_sync import BidirectionalSync, SyncScheduler
    
    sync = BidirectionalSync(None, None)
    scheduler = SyncScheduler(sync, interval_seconds=1)
    
    # Run scheduler for brief time
    task = asyncio.create_task(scheduler.start())
    await asyncio.sleep(0.5)
    await scheduler.stop()
    
    assert scheduler.running is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
