# coding: utf-8

import datetime
from collections import defaultdict
from dataclasses import dataclass
from math import floor, ceil

from typing import Any, Dict, Iterator, List, Optional, Tuple


@dataclass
class PeriodResults:
    tally: int
    target: int
    status: int
    classes: List[str]


class Period:
    def __init__(self, name: str, window: int) -> None:
        self.name = name
        self.window = window

        self.count: Dict[datetime.date, int] = defaultdict(int)
        self.status: Dict[datetime.date, int] = defaultdict(int)

    def target(self, window: int, target: int) -> int:
        return int(floor(target * min(self.window, window) / 365))

    def tally(self, date: datetime.date, count: int) -> None:
        for i in range(self.window):
            self.count[date + datetime.timedelta(i)] += count

    def update_status(
        self, min_date: datetime.date, date: datetime.date, target: int, rate: int
    ) -> None:
        window = (date - min_date).days
        if self.count[date] > self.target(window, target):
            i = 0
            while (
                self.count[date + datetime.timedelta(i + 1)]
                >= self.target(window + i + 1, target)
            ) and i < 366:
                i += 1
            self.status[date] = i
        else:
            self.status[date] = ceil(
                (self.count[date] - self.target(window, target)) / rate
            )

    def required(
        self, min_date: datetime.date, date: datetime.date, target: int, acc: int
    ) -> int:
        window = (date - min_date).days
        return max(self.target(window, target) - self.count[date] - acc, 0)

    def results(
        self,
        min_date: datetime.date,
        date: datetime.date,
        target: int,
        today: datetime.date,
    ) -> PeriodResults:
        classes = []

        count = self.count[date]
        target2 = self.target((date - min_date).days, target)

        if count >= target2:
            classes.append("green")
        else:
            classes.append("red")

        age = (today - date).days
        if 0 <= age < self.window:
            classes.append("window")

        return PeriodResults(count, target2, self.status[date], classes)


@dataclass
class TallyResults:
    date: datetime.date
    ticked: bool
    total: int
    notes: str
    periods: List[PeriodResults]


class Tally:
    def __init__(self) -> None:
        self.min: Optional[datetime.date] = None
        self.max: Optional[datetime.date] = None
        self.total: Dict[datetime.date, int] = defaultdict(int)
        self.required: Dict[datetime.date, int] = defaultdict(int)
        self.frequency: Dict[int, int] = defaultdict(int)
        self.notes: Dict[datetime.date, List[str]] = defaultdict(list)

        self.periods: List[Period] = [
            Period("Year", 365),
            Period("Quarter", 90),
            Period("Month", 28),
            Period("Week", 7),
        ]

    @classmethod
    def from_reps(cls, reps: List[Any], target: int, today: datetime.date) -> "Tally":
        tally = cls()
        tally.tally(reps, target, today)
        return tally

    def tally(self, reps: List[Any], target: int, today: datetime.date) -> None:
        last_date = None

        for rep in reps:
            if last_date is not None:
                self.update_status(last_date, (rep.date - last_date).days, target)

            last_date = rep.date

            self.min = rep.date if self.min is None else min(self.min, rep.date)
            self.max = rep.date if self.max is None else max(self.max, rep.date)

            self.total[rep.date] += rep.count

            self.frequency[rep.count] += 1

            self.notes[rep.date].append(str(rep.count))

            if rep.notes is not None:
                self.notes[rep.date][-1] += f" <span>{rep.notes}</span>"

            for period in self.periods:
                period.tally(rep.date, rep.count)

        if last_date is not None:
            self.update_status(
                last_date, max(period.window for period in self.periods), target
            )

            self.update_required(
                last_date, max(period.window for period in self.periods), target, today
            )

    def update_status(self, date: datetime.date, window: int, target: int) -> None:
        assert self.min is not None
        rate = self.median_non_zero_count
        for i in range(window):
            for period in self.periods:
                period.update_status(
                    self.min, date + datetime.timedelta(i), target, rate
                )

    def update_required(
        self, date: datetime.date, window: int, target: int, today: datetime.date
    ) -> None:
        assert self.min is not None
        rate = self.median_non_zero_count
        acc = 0
        for i in range(window):
            date2 = date + datetime.timedelta(i)
            if date2 >= today:
                # only show required if no reps logged for day
                if self.total[date2]:
                    continue

                v = max(
                    period.required(self.min, date2, target, acc)
                    for period in self.periods
                )
                acc += v

                # if v > rate, try and distribute it back over
                # previous days to smooth it out
                if v > rate:
                    for j in reversed(range(i)):
                        date3 = date + datetime.timedelta(j)
                        if date3 >= today:
                            if self.total[date3]:
                                break

                            while v > rate and self.required[date3] < rate:
                                self.required[date3] += 1
                                v -= 1

                self.required[date2] = v

    def dates(self) -> Iterator[datetime.date]:
        if self.min is None:
            return
        assert self.max is not None
        for i in range(
            (self.max - self.min).days + max(period.window for period in self.periods)
        ):
            yield self.min + datetime.timedelta(i)

    @property
    def period_names(self) -> List[str]:
        return [period.name for period in self.periods]

    def results(
        self, dates: List[datetime.date], target: int, today: datetime.date
    ) -> Iterator[TallyResults]:
        for date in dates:
            notes = ", ".join(self.notes[date]) or (
                f"⇨ {self.required[date]}" if date in self.required else "0"
            )
            assert self.min is not None
            yield TallyResults(
                date,
                bool(self.total[date]),
                self.total[date] or self.required[date],
                notes,
                [
                    period.results(self.min, date, target, today)
                    for period in self.periods
                ],
            )

    def targets(self, target: int) -> List[Tuple[str, int]]:
        return [
            (period.name, period.target(period.window, target))
            for period in self.periods
        ]

    def status(self, date: datetime.date) -> List[Tuple[str, int]]:
        return [(period.name, period.status[date]) for period in self.periods]

    def status_v2(
        self, date: datetime.date, target: int
    ) -> List[Tuple[str, int, int, int]]:
        return [
            (
                period.name,
                period.status[date],
                period.count[date],
                period.target(period.window, target),
            )
            for period in self.periods
        ]

    @property
    def median_non_zero_count(self) -> int:
        percentile = sum(self.frequency.values()) * 0.5
        cumulative = 0
        for count, frequency in sorted(self.frequency.items()):
            cumulative += frequency
            if cumulative > percentile:
                break
        return count

    @property
    def max_total(self) -> float:
        return max(self.total.values()) if self.total else 0.0
