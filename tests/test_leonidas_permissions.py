from switch.hermes.leonidas import check_permission


def test_leonidas_allows_safe_commands():
    ok, reason = check_permission("echo hello")
    assert ok
    ok2, _ = check_permission("date")
    assert ok2


def test_leonidas_denies_dangerous():
    ok, _ = check_permission("rm -rf /")
    assert not ok
    ok, _ = check_permission("sudo reboot")
    assert not ok
