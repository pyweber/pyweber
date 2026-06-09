from pyweber.models.strem_stats import StreamStats, AdaptiveController


def test_stream_stats_summary():
    stats = StreamStats(total_bytes=2048, total_chunks=2, elapsed_ms=1000)
    summary = stats.summary()
    assert summary['total_kb'] == 2.0
    assert stats.avg_throughput_kbps > 0
    assert stats.avg_chunk_size_kb > 0
    assert stats.total_elapsed_s >= 0


def test_adaptive_controller_update():
    ctrl = AdaptiveController(max_size=1024 * 128)
    ctrl.update(received_bytes=4096, elapsed_ms=50)
    assert ctrl.chunk_size >= ctrl._MIN_CHUNK
    assert ctrl.interval_ms >= ctrl._MIN_INTERVAL
    assert ctrl.stats.total_bytes == 4096
