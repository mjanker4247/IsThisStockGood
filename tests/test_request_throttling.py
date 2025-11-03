import threading
from concurrent.futures import Future
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Optional

from isthisstockgood.DataFetcher import DataFetcher


class HookAwareFuture(Future):
    """A ``Future`` that invokes request hooks when completed."""

    def __init__(self, hooks: Optional[Mapping[str, Callable[..., Any]]]) -> None:
        super().__init__()
        self._hooks = hooks or {}

    def set_result(self, result: Any) -> None:  # type: ignore[override]
        super().set_result(result)
        callback = self._hooks.get("response")
        if callback:
            callback(result)


@dataclass
class RecordedRequest:
    url: str
    hooks: Optional[Mapping[str, Callable[..., Any]]]
    future: HookAwareFuture


class FakeSession:
    """Minimal session that records requests and returns controllable futures."""

    def __init__(self) -> None:
        self.requests: list[RecordedRequest] = []

    def get(self, url: str, *, hooks: Optional[Mapping[str, Callable[..., Any]]] = None, **_: Any) -> HookAwareFuture:
        future = HookAwareFuture(hooks)
        self.requests.append(RecordedRequest(url, hooks, future))
        return future


def test_data_fetcher_limits_simultaneous_requests() -> None:
    session = FakeSession()
    fetcher = DataFetcher("msft", session_factory=lambda: session, max_concurrent_requests=1)

    first_future = fetcher._schedule_request("https://example.com/first")

    gate = threading.Event()
    completed = threading.Event()

    def schedule_second() -> None:
        gate.set()
        fetcher._schedule_request("https://example.com/second")
        completed.set()

    worker = threading.Thread(target=schedule_second)
    worker.start()

    assert gate.wait(timeout=1), "Second scheduling attempt did not start"
    assert not completed.wait(timeout=0.1), "Second request should wait for the first to finish"

    first_future.set_result(object())

    worker.join(timeout=1)
    assert completed.is_set(), "Second request was not allowed to proceed after the first completed"
    assert not worker.is_alive(), "Background worker thread failed to exit"

    assert len(session.requests) == 2


def test_wait_for_completion_handles_chained_requests() -> None:
    session = FakeSession()
    fetcher = DataFetcher("msft", session_factory=lambda: session, max_concurrent_requests=1)

    def trigger_follow_up(_response: Any) -> None:
        fetcher._schedule_request("https://example.com/chained")

    first_future = fetcher._schedule_request(
        "https://example.com/initial",
        hooks={"response": trigger_follow_up},
    )

    first_future.set_result(object())

    assert len(session.requests) == 2
    session.requests[1].future.set_result(object())

    fetcher.wait_for_completion()

    assert all(request.future.done() for request in session.requests)
