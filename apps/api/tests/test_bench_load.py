"""The load benchmark's percentile must be monotonic and interpolate correctly."""

from scripts.bench_load import percentile


def test_percentile_interpolates_between_samples() -> None:
    values = [10.0, 20.0, 30.0, 40.0, 50.0]

    assert percentile(values, 0.50) == 30.0
    assert percentile(values, 0.95) == 48.0
    assert percentile(values, 0.99) == 49.6


def test_percentile_handles_empty_and_single_samples() -> None:
    assert percentile([], 0.95) == 0.0
    assert percentile([12.5], 0.95) == 12.5
