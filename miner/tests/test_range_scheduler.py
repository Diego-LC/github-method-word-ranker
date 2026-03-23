"""Tests para el planificador de rangos de stars."""

from miner.range_scheduler import RangeScheduler


class TestRangeScheduler:
    """Tests para RangeScheduler."""

    def test_iter_ranges_returns_multiple(self) -> None:
        scheduler = RangeScheduler(min_stars=10)
        ranges = list(scheduler.iter_ranges())
        assert len(ranges) > 1

    def test_first_range_is_open(self) -> None:
        scheduler = RangeScheduler(min_stars=10)
        ranges = list(scheduler.iter_ranges())
        assert ranges[0].query.startswith(">")

    def test_subsequent_ranges_are_closed(self) -> None:
        scheduler = RangeScheduler(min_stars=10)
        ranges = list(scheduler.iter_ranges())
        for r in ranges[1:]:
            assert ".." in r.query

    def test_dedup_tracking(self) -> None:
        scheduler = RangeScheduler()
        assert not scheduler.is_processed("owner/repo")
        scheduler.mark_processed("owner/repo")
        assert scheduler.is_processed("owner/repo")

    def test_high_min_stars_reduces_ranges(self) -> None:
        scheduler_low = RangeScheduler(min_stars=10)
        scheduler_high = RangeScheduler(min_stars=10_000)
        ranges_low = list(scheduler_low.iter_ranges())
        ranges_high = list(scheduler_high.iter_ranges())
        assert len(ranges_high) < len(ranges_low)
