"""Run the queue consumer unit test without pytest (avoids project conftest/plugins).

This directly calls the test function to validate behavior in CI-less environments.
"""

import sys


def main():
    try:
        # load test module directly to avoid pytest/packaging
        import importlib.util
        import pathlib
        import sys

        # ensure repo root on path
        repo_root = pathlib.Path(__file__).resolve().parents[1]
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))

        p = (
            pathlib.Path(__file__).resolve().parents[1]
            / "tests"
            / "test_switch_queue_consumer.py"
        )
        spec = importlib.util.spec_from_file_location(
            "test_switch_queue_consumer", str(p)
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.test_queue_consumer_processes_item()
        print("TEST PASS: queue_consumer_processes_item")
        return 0
    except AssertionError as e:
        print("TEST FAIL: AssertionError", e)
        return 2
    except Exception as e:
        print("TEST ERROR:", type(e), e)
        return 3


if __name__ == "__main__":
    sys.exit(main())
