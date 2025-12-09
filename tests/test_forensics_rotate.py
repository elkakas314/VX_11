from config.forensics import rotate_crashes, prune_snapshots, forensic_usage_summary


def test_forensics_helpers_run():
    removed = rotate_crashes(retain=5)
    # function should return a list (possibly empty)
    assert isinstance(removed, list)
    removed2 = prune_snapshots(limit=2)
    assert isinstance(removed2, list)
    summ = forensic_usage_summary()
    assert isinstance(summ, dict)
