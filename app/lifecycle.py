"""CP4 — Graceful shutdown.

Khi bạn deploy phiên bản mới, orchestrator (Docker, Railway, Cloud Run, K8s)
gửi **SIGTERM** rồi đợi vài chục giây trước khi SIGKILL. Nếu app bỏ qua tín
hiệu đó, mọi request đang xử lý dở bị cắt giữa chừng — user thấy lỗi 502 mỗi
lần bạn deploy.

Ứng xử đúng: nhận SIGTERM → báo "tôi sắp tắt" qua health check để load
balancer ngừng đẩy traffic mới vào → xử lý nốt request đang chạy → thoát.
"""

from __future__ import annotations

import signal


class Lifecycle:
    """Giữ trạng thái vòng đời của process."""

    def __init__(self) -> None:
        self.shutting_down = False
        # Preserve Uvicorn's signal handlers so the server can finish shutdown.
        self._previous: dict = {}

    def request_shutdown(self, signum=None, frame=None) -> None:
        """Mark shutdown and pass the signal to the previous handler."""
        self.shutting_down = True

        previous = self._previous.get(signum)

        if callable(previous):
            previous(signum, frame)

    def install(self) -> None:
        """Register shutdown handlers while retaining existing handlers."""
        for sig in (signal.SIGTERM, signal.SIGINT):
            self._previous[sig] = signal.getsignal(sig)
            signal.signal(sig, self.request_shutdown)


# Share one lifecycle state across the app.
lifecycle = Lifecycle()
