from collections import defaultdict
from threading import Lock


class MetricsRegistry:
    def __init__(self) -> None:
        self._lock = Lock()
        self._requests: dict[tuple[str, str, int], int] = defaultdict(int)
        self._duration: dict[tuple[str, str], tuple[int, float]] = defaultdict(
            lambda: (0, 0.0)
        )

    def observe(
        self,
        method: str,
        route: str,
        status_code: int,
        duration_seconds: float,
    ) -> None:
        with self._lock:
            self._requests[(method, route, status_code)] += 1
            count, total = self._duration[(method, route)]
            self._duration[(method, route)] = (
                count + 1,
                total + duration_seconds,
            )

    def render(self) -> str:
        lines = [
            "# HELP quantprox_http_requests_total Total HTTP requests.",
            "# TYPE quantprox_http_requests_total counter",
        ]
        with self._lock:
            for (method, route, status_code), count in sorted(self._requests.items()):
                labels = (
                    f'method="{_escape(method)}",route="{_escape(route)}",'
                    f'status="{status_code}"'
                )
                lines.append(f"quantprox_http_requests_total{{{labels}}} {count}")
            lines.extend(
                [
                    "# HELP quantprox_http_request_duration_seconds "
                    "HTTP request duration.",
                    "# TYPE quantprox_http_request_duration_seconds summary",
                ]
            )
            for (method, route), (count, total) in sorted(self._duration.items()):
                labels = f'method="{_escape(method)}",route="{_escape(route)}"'
                lines.append(
                    "quantprox_http_request_duration_seconds_count"
                    f"{{{labels}}} {count}"
                )
                lines.append(
                    "quantprox_http_request_duration_seconds_sum"
                    f"{{{labels}}} {total:.6f}"
                )
        return "\n".join(lines) + "\n"

    def reset(self) -> None:
        with self._lock:
            self._requests.clear()
            self._duration.clear()


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


metrics = MetricsRegistry()
