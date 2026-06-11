from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class Booking:
    room: str
    title: str
    start: datetime
    end: datetime


class SchedulingError(Exception):
    pass


class RoomScheduler:
    def __init__(self, opening: datetime, closing: datetime):
        if opening >= closing:
            raise ValueError("opening must be before closing")
        self.opening = opening
        self.closing = closing
        self._bookings: dict[str, list[Booking]] = {}

    def book(self, room: str, title: str, start: datetime, end: datetime) -> Booking:
        if start >= end:
            raise SchedulingError(f"invalid time range: {start} >= {end}")
        if start < self.opening or end > self.closing:
            raise SchedulingError("booking outside business hours")
        booking = Booking(room=room, title=title, start=start, end=end)
        self._bookings.setdefault(room, []).append(booking)
        return booking

    def cancel(self, booking: Booking) -> None:
        try:
            self._bookings[booking.room].remove(booking)
        except (KeyError, ValueError):
            raise SchedulingError(f"unknown booking: {booking.title}")

    def busy_periods(self, room: str) -> list[tuple[datetime, datetime]]:
        bookings = sorted(self._bookings.get(room, []), key=lambda b: b.start)
        merged: list[list[datetime]] = []
        for booking in bookings:
            if merged and booking.start <= merged[-1][1]:
                merged[-1][1] = booking.end
            else:
                merged.append([booking.start, booking.end])
        return [(start, end) for start, end in merged]

    def free_slots(
        self, room: str, min_duration: timedelta
    ) -> list[tuple[datetime, datetime]]:
        slots = []
        cursor = self.opening
        for start, end in self.busy_periods(room):
            if start - cursor >= min_duration:
                slots.append((cursor, start))
            cursor = max(cursor, end)
        if self.closing - cursor >= min_duration:
            slots.append((cursor, self.closing))
        return slots

    def suggest(
        self, rooms: list[str], duration: timedelta
    ) -> tuple[str, datetime, datetime]:
        best: tuple[str, datetime, datetime] | None = None
        for room in rooms:
            for start, end in self.free_slots(room, duration):
                candidate = (room, start, start + duration)
                if best is None or candidate[1] < best[1]:
                    best = candidate
        if best is None:
            raise SchedulingError("no slot available")
        return best

    def is_available(self, room: str, start: datetime, end: datetime) -> bool:
        for busy_start, busy_end in self.busy_periods(room):
            if start < busy_end and end > busy_start:
                return False
        return True
