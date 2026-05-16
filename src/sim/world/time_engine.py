import time

class TimeEngine:
    def __init__(self):
        self.current_time = time.time()
        self.year = 0
        self.month = 0
        self.day = 0
        self.hour = 0
        self.minute = 0
        self.second = 0
        self.day_of_week = ""
        self.season = ""
        self.day_cycle = ""

    def tick(self):
        self.current_time = time.time()
        self.year = self.current_time // (60*60*24*365)
        self.month = self.current_time // (60*60*24*30)
        self.day = self.current_time // (60*60*24)
        self.hour = self.current_time // (60*60)
        self.minute = self.current_time // 60
        self.second = self.current_time
        self._update_day_of_week()
        self._update_season()
        self._update_day_cycle()

    def _update_day_of_week(self):
        days_of_week = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
        self.day_of_week = days_of_week[self.day % 7]

    def _update_season(self):
        if self.month == 3 or self.month == 4 or self.month == 5:
            self.season = "봄"
        elif self.month == 6 or self.month == 7 or self.month == 8:
            self.season = "여름"
        elif self.month == 9 or self.month == 10 or self.month == 11:
            self.season = "가을"
        else:
            self.season = "겨울"

    def _update_day_cycle(self):
        if self.hour >= 6 and self.hour < 18:
            self.day_cycle = "낮"
        else:
            self.day_cycle = "밤"

    def get_context(self):
        return f"""\
# 세계 시간 정보 (World Time Info)
- 현재 시간: {self.year}.{self.month}.{self.day} {self.hour}:{self.minute}:{self.second}
- 낮/밤: {self.day_cycle}
- 요일: {self.day_of_week}
- 계절: {self.season}"""