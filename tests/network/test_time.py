"""Tests for hydroflow.network._time."""

import pytest

from hydroflow.network._time import format_time, parse_duration


class TestParseDuration:
    # ── Numeric passthrough ───────────────────────────────────────────
    def test_int_passthrough(self) -> None:
        assert parse_duration(3600) == 3600.0

    def test_float_passthrough(self) -> None:
        assert parse_duration(90.5) == 90.5

    def test_zero(self) -> None:
        assert parse_duration(0) == 0.0

    def test_negative_number_raises(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            parse_duration(-1)

    # ── String: seconds ───────────────────────────────────────────────
    def test_seconds_short(self) -> None:
        assert parse_duration("30s") == 30.0

    def test_seconds_long(self) -> None:
        assert parse_duration("30 seconds") == 30.0

    # ── String: minutes ───────────────────────────────────────────────
    def test_minutes_short(self) -> None:
        assert parse_duration("15min") == 900.0

    def test_minutes_long(self) -> None:
        assert parse_duration("15 minutes") == 900.0

    def test_minutes_m(self) -> None:
        assert parse_duration("5m") == 300.0

    # ── String: hours ─────────────────────────────────────────────────
    def test_hours_short(self) -> None:
        assert parse_duration("24h") == 86400.0

    def test_hours_long(self) -> None:
        assert parse_duration("1 hour") == 3600.0

    def test_hours_hr(self) -> None:
        assert parse_duration("2hr") == 7200.0

    # ── String: days ──────────────────────────────────────────────────
    def test_days_short(self) -> None:
        assert parse_duration("1d") == 86400.0

    def test_days_long(self) -> None:
        assert parse_duration("3 days") == 259200.0

    # ── Fractional ────────────────────────────────────────────────────
    def test_fractional_hours(self) -> None:
        assert parse_duration("1.5h") == 5400.0

    def test_fractional_days(self) -> None:
        assert parse_duration("0.5d") == 43200.0

    # ── Whitespace tolerance ──────────────────────────────────────────
    def test_leading_trailing_spaces(self) -> None:
        assert parse_duration("  24h  ") == 86400.0

    def test_space_between_value_and_unit(self) -> None:
        assert parse_duration("10 min") == 600.0

    # ── Clock-time format ─────────────────────────────────────────────
    def test_clock_time_22_00(self) -> None:
        assert parse_duration("22:00") == 79200.0

    def test_clock_time_6_30(self) -> None:
        assert parse_duration("6:30") == 23400.0

    def test_clock_time_00_00(self) -> None:
        assert parse_duration("00:00") == 0.0

    def test_clock_time_01_15(self) -> None:
        assert parse_duration("01:15") == 4500.0

    def test_clock_time_with_spaces(self) -> None:
        assert parse_duration("  12:00  ") == 43200.0

    def test_clock_time_invalid_hours_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid clock time"):
            parse_duration("25:00")

    def test_clock_time_invalid_minutes_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid clock time"):
            parse_duration("12:60")

    # ── Error cases ───────────────────────────────────────────────────
    def test_unknown_unit_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown time unit"):
            parse_duration("5 fortnights")

    def test_empty_string_raises(self) -> None:
        with pytest.raises(ValueError, match="Cannot parse"):
            parse_duration("")

    def test_no_value_raises(self) -> None:
        with pytest.raises(ValueError, match="Cannot parse"):
            parse_duration("hours")

    def test_garbage_raises(self) -> None:
        with pytest.raises(ValueError, match="Cannot parse"):
            parse_duration("abc123xyz")


class TestFormatTime:
    def test_zero(self) -> None:
        assert format_time(0) == "00:00"

    def test_one_hour(self) -> None:
        assert format_time(3600) == "01:00"

    def test_ninety_minutes(self) -> None:
        assert format_time(5400) == "01:30"

    def test_twenty_three_hours(self) -> None:
        assert format_time(23 * 3600) == "23:00"

    def test_one_day(self) -> None:
        assert format_time(86400) == "1d 00:00"

    def test_one_day_one_hour(self) -> None:
        assert format_time(90000) == "1d 01:00"

    def test_three_days(self) -> None:
        assert format_time(3 * 86400 + 12 * 3600 + 30 * 60) == "3d 12:30"

    def test_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="negative"):
            format_time(-1)
