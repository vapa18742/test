from datetime import datetime, timedelta


class Airport:
    def __init__(self, code: str, name: str, city: str):
        self.code = code.upper()
        self.name = name
        self.city = city

    def __repr__(self):
        return f"{self.city} ({self.code})"


class Flight:
    def __init__(self, flight_number: str, origin: Airport, destination: Airport,
                 departure_time: datetime, duration_minutes: int, amenities: dict = None):
        self.flight_number = flight_number
        self.origin = origin
        self.destination = destination
        self.departure_time = departure_time
        self.duration = timedelta(minutes=duration_minutes)
        # Специальные условия (питание, багаж и т.д.)
        self.amenities = amenities if amenities else {"meals": True, "extra_baggage": False}

        # Конфигурация мест: {'Бизнес': (ряды, кресла_в_ряду)}
        self.seat_config = {}
        # Текущая карта занятости мест: {'Бизнес': [[False, ...], ...]}
        self.seating_chart = {}

    def set_seat_configuration(self, config: dict):
        """Устанавливает конфигурацию салона. Формат: {'Класс': (ряды, кресла_в_ряду)}"""
        self.seat_config = config
        self.seating_chart = {}
        for service_class, (rows, cols) in config.items():
            # Создаем матрицу мест: False — свободно, True — занято
            self.seating_chart[service_class] = [[False for _ in range(cols)] for _ in range(rows)]

    def get_free_seats_count(self, service_class: str) -> int:
        """Возвращает количество свободных мест в классе."""
        if service_class not in self.seating_chart:
            return 0
        return sum(row.count(False) for row in self.seating_chart[service_class])

    def book_seat(self, service_class: str, row: int, col: int) -> bool:
        """Бронирует конкретное место (индексы с 0)."""
        if service_class not in self.seating_chart:
            return False

        try:
            if not self.seating_chart[service_class][row][col]:
                self.seating_chart[service_class][row][col] = True
                return True
        except IndexError:
            return False
        return False

    def has_adjacent_seats(self, service_class: str, count: int) -> bool:
        """Проверяет, есть ли N свободных мест подряд в одном ряду."""
        if service_class not in self.seating_chart:
            return False

        for row in self.seating_chart[service_class]:
            consecutive = 0
            for seat in row:
                if not seat:
                    consecutive += 1
                    if consecutive == count:
                        return True
                else:
                    consecutive = 0
        return False

    def print_seating_chart(self):
        """Печатает план салона самолета."""
        print(f"\n=== ПЛАН САЛОНА РЕЙСА {self.flight_number} ({self.origin.code} -> {self.destination.code}) ===")
        for service_class, matrix in self.seating_chart.items():
            print(f"\nКласс: {service_class}")
            for r_idx, row in enumerate(matrix):
                row_str = f"Ряд {r_idx + 1:02d}: "
                seats_str = " ".join(["[X]" if seat else "[ ]" for seat in row])
                print(row_str + seats_str)
        print("==================================================\n")


class AirlineSystem:
    def __init__(self):
        self.airports = {}
        self.flights = []

    def add_airport(self, code: str, name: str, city: str):
        airport = Airport(code, name, city)
        self.airports[airport.code] = airport
        return airport

    def add_flight(self, flight_number: str, origin_code: str, destination_code: str,
                   departure_str: str, duration_minutes: int, amenities: dict = None):
        """Добавляет рейс. Формат даты: 'YYYY-MM-DD HH:MM'"""
        origin = self.airports.get(origin_code.upper())
        destination = self.airports.get(destination_code.upper())

        if not origin or not destination:
            raise ValueError("Один из аэропортов не найден в системе!")

        departure_time = datetime.strptime(departure_str, "%Y-%m-%d %H:%M")
        flight = Flight(flight_number, origin, destination, departure_time, duration_minutes, amenities)
        self.flights.append(flight)
        return flight

    def find_nearest_flights(self, origin_code: str, destination_code: str,
                             start_from: datetime, service_class: str,
                             time_preference: str = None, min_adjacent_seats: int = 1):
        """
        Поиск подходящих рейсов по направлению и фильтрам.
        time_preference: 'morning' (06-12), 'afternoon' (12-18), 'evening' (18-24), 'night' (00-06)
        """
        suitable_flights = []

        for flight in self.flights:
            # 1. Проверка направления и времени вылета
            if flight.origin.code != origin_code.upper() or flight.destination.code != destination_code.upper():
                continue
            if flight.departure_time < start_from:
                continue

            # 2. Проверка наличия мест в классе
            if flight.get_free_seats_count(service_class) < min_adjacent_seats:
                continue

            # 3. Проверка мест рядом
            if min_adjacent_seats > 1 and not flight.has_adjacent_seats(service_class, min_adjacent_seats):
                continue

            # 4. Временные предпочтения
            if time_preference:
                hour = flight.departure_time.hour
                if time_preference == 'morning' and not (6 <= hour < 12):
                    continue
                elif time_preference == 'afternoon' and not (12 <= hour < 18):
                    continue
                elif time_preference == 'evening' and not (18 <= hour < 24):
                    continue
                elif time_preference == 'night' and not (0 <= hour < 6):
                    continue

            suitable_flights.append(flight)

        # Сортируем по хронологии
        suitable_flights.sort(key=lambda x: x.departure_time)
        return suitable_flights


# =====================================================================
# ДЕМОНСТРАЦИЯ РАБОТЫ СИСТЕМЫ
# =====================================================================
if __name__ == "__main__":
    # Инициализация системы
    system = AirlineSystem()

    print("1. Добавление аэропортов...")
    system.add_airport("SVO", "Шереметьево", "Москва")
    system.add_airport("LED", "Пулково", "Санкт-Петербург")
    system.add_airport("DXB", "Дубай", "Дубай")

    print("2. Добавление рейсов...")
    # Утренний рейс с питанием и багажом
    f1 = system.add_flight("SU-520", "SVO", "DXB", "2026-10-15 08:30", 330, {"meals": True, "extra_baggage": True})
    # Вечерний рейс с питанием, но без доп. багажа
    f2 = system.add_flight("SU-522", "SVO", "DXB", "2026-10-15 21:00", 330, {"meals": True, "extra_baggage": False})

    print("3. Настройка конфигурации салонов (Бизнес и Эконом)...")
    for flight in [f1, f2]:
        flight.set_seat_configuration({
            "Бизнес": (2, 2),  # 2 ряда по 2 кресла
            "Эконом": (3, 4)  # 3 ряда по 4 кресла
        })

    print("4. Бронирование нескольких мест на первом рейсе...")
    f1.book_seat("Эконом", 0, 0)  # Заняли Ряд 1, Место 1
    f1.book_seat("Эконом", 0, 1)  # Заняли Ряд 1, Место 2
    f1.book_seat("Бизнес", 1, 1)  # Заняли Ряд 2, Место 2 в Бизнесе

    # 5. Печать плана салона
    f1.print_seating_chart()

    # Точка отсчета для поиска рейсов
    search_time = datetime(2026, 10, 15, 0, 0)

    print("6. Тестирование поиска ближайшего утреннего рейса:")
    res_morning = system.find_nearest_flights("SVO", "DXB", search_time, "Эконом", time_preference="morning")
    for f in res_morning:
        print(f" -> Рейс: {f.flight_number}, Вылет: {f.departure_time}")
        print(f"    Питание: {f.amenities['meals']}, Доп. багаж: {f.amenities['extra_baggage']}")

    print("\n7. Тестирование поиска рейса с 3 местами РЯДОМ:")
    # На первом рейсе в первом ряду осталось только 2 места подряд, программа проверит остальные ряды
    res_adjacent = system.find_nearest_flights("SVO", "DXB", search_time, "Эконом", min_adjacent_seats=3)
    for f in res_adjacent:
        print(f" -> Рейс: {f.flight_number}, Вылет: {f.departure_time} (Доступно мест рядом: Да)")
