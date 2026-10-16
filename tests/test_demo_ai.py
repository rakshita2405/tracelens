
from app.demo_ai import run_demo


def test_successful_run():
    trace = run_demo("What is Python?")

    assert trace["status"] == "success"
    assert trace["trace_id"]
    assert len(trace["steps"]) == 2
    assert all(
        step["status"] == "success"
        for step in trace["steps"]
    )


def test_failed_retrieval():
    trace = run_demo(
        "What is Python?",
        simulate_failure=True,
    )

    assert trace["status"] == "failed"
    assert trace["steps"][0]["status"] == "failed"
    assert trace["steps"][0]["error"]
    assert len(trace["steps"]) == 1


def test_latency_is_nonnegative():
    trace = run_demo("Test question")

    assert trace["latency_ms"] >= 0
