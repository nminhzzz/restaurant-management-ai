"""The benchmark's p95 is the nearest-rank percentile (NFR-01, NFR-03)."""

import pytest
from scripts.bench_reports import percentile


def test_p95_of_twenty_samples_is_the_nineteenth_fastest() -> None:
    samples = [float(n) for n in range(1, 21)]

    assert percentile(samples, 0.95) == 19.0


def test_a_single_slow_outlier_does_not_move_p95_of_a_large_sample() -> None:
    samples = [0.1] * 99 + [30.0]

    assert percentile(samples, 0.95) == 0.1
    assert percentile(samples, 1.0) == 30.0


def test_order_does_not_matter_and_empty_is_zero() -> None:
    assert percentile([3.0, 1.0, 2.0], 0.5) == 2.0
    assert percentile([], 0.95) == 0.0


@pytest.mark.parametrize("fraction", [0.0, 0.01])
def test_the_lowest_fraction_returns_the_fastest_sample(fraction: float) -> None:
    assert percentile([5.0, 2.0, 9.0], fraction) == 2.0
