class WeatherEngine:
    def __init__(self):
        self.weather_list = {
            "맑음": 60,
            "흐림": 20,
            "비": 10,
            "눈": 5,
            "천둥": 3,
            "번개": 2
        }
        self.weather = "맑음"

    def tick(self):
        self._update_weather()

    def _update_weather(self):
        self.weather = random.choices(list(self.weather_list.keys()), list(self.weather_list.values()))[0]

    def get_context(self):
        weather_description_dict = {
            "맑음": "하늘은 파랗고 구름 한 점 없이 맑습니다. 햇살이 따스하게 내리쬡니다.",
            "흐림": "하늘 전체가 두터운 회색 구름으로 덮여 있습니다. 빛이 약하게 들어옵니다.",
            "비": "톡톡 떨어지는 빗방울 소리가 들립니다. 공기 중에 물 향기가 감돕니다.",
            "눈": "하늘에서 하얀 눈송이가 소리 없이 내려앉고 있습니다. 주변이 고요합니다.",
            "천둥": "멀리서 낮게 '우르릉'거리는 소리가 들려옵니다. 곧 비가 올 것 같습니다.",
            "번개": "하늘이 번쩍이며 순간적으로 밝아졌다가 다시 어두워집니다. 곧 천둥이 칠 것입니다."
        }

        description = weather_description_dict.get(self.weather, self.weather)
        return f"""\
# 세계 날씨 정보 (World Weather Info)
- 현재 날씨: {self.weather}
- 날씨 설명: {description}"""
    
    