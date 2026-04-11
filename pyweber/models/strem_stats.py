from dataclasses import dataclass, field
from time import time

@dataclass
class StreamStats: # pragma: no cover
    total_bytes: int = 0
    total_chunks: int = 0
    elapsed_ms: float = 0.0
    start_time: float = field(default_factory=time)

    @property
    def avg_throughput_kbps(self) -> float:
        """Velocidade média em KB/s"""
        elapsed_s = max(self.elapsed_ms / 1000, 1e-6)
        return (self.total_bytes / 1024) / elapsed_s

    @property
    def avg_chunk_size_kb(self) -> float:
        """Tamanho médio dos chunks em KB"""
        if self.total_chunks == 0:
            return 0.0
        return (self.total_bytes / 1024) / self.total_chunks

    @property
    def total_elapsed_s(self) -> float:
        """Tempo total decorrido em segundos"""
        return (time() - self.start_time)

    def summary(self) -> dict:
        return {
            'total_bytes': self.total_bytes,
            'total_kb': round(self.total_bytes / 1024, 2),
            'total_mb': round(self.total_bytes / (1024 ** 2), 4),
            'total_chunks': self.total_chunks,
            'avg_throughput_kbps': round(self.avg_throughput_kbps, 2),
            'avg_chunk_size_kb': round(self.avg_chunk_size_kb, 2),
            'elapsed_s': round(self.total_elapsed_s, 3)
        }


class AdaptiveController: # pragma: no cover
    """Controla chunk_size e interval dinamicamente"""

    def __init__(self, max_size: int):
        self.max_size = max_size
        self.chunk_size = 1024 * 64
        self.interval_ms = 50
        self._MIN_CHUNK = 1024
        self._MIN_INTERVAL = 10
        self._MAX_INTERVAL = 1000
        self.stats = StreamStats()  # ✅ estatísticas integradas

    def update(self, received_bytes: int, elapsed_ms: float):
        throughput = received_bytes / max(elapsed_ms, 1)  # bytes/ms

        # ajusta chunk
        ideal = int(throughput * self.interval_ms)
        self.chunk_size = max(self._MIN_CHUNK, min(ideal, self.max_size))

        # ajusta intervalo
        if elapsed_ms < self.interval_ms * 0.5:
            self.interval_ms = max(self._MIN_INTERVAL, int(self.interval_ms * 0.8))
        elif elapsed_ms > self.interval_ms * 1.5:
            self.interval_ms = min(self._MAX_INTERVAL, int(self.interval_ms * 1.2))

        # ✅ actualiza estatísticas
        self.stats.total_bytes += received_bytes
        self.stats.total_chunks += 1
        self.stats.elapsed_ms += elapsed_ms

    def progress(self, file_size: int) -> dict:
        """Progresso do download"""
        downloaded = self.stats.total_bytes
        percent = min((downloaded / max(file_size, 1)) * 100, 100)

        remaining_bytes = max(file_size - downloaded, 0)
        throughput_bps = max(self.stats.avg_throughput_kbps * 1024, 1)
        eta_s = remaining_bytes / throughput_bps

        return {
            'downloaded_bytes': downloaded,
            'downloaded_mb': round(downloaded / (1024 ** 2), 4),
            'file_size_mb': round(file_size / (1024 ** 2), 4),
            'percent': round(percent, 2),
            'eta_s': round(eta_s, 1),
            'speed_kbps': round(self.stats.avg_throughput_kbps, 2)
        }

    def reset_stats(self):
        """Reinicia estatísticas para novo stream"""
        self.stats = StreamStats()
