import requests
from django.conf import settings


class SpeedrunClient:
    url = settings.SPEEDRUN_URL
    MAX_ENTRIES = 5

    def __init__(self):
        self.headers = {
            'X-API-Key': settings.SPEEDRUN_API_KEY
        }

    def get_game_search_results(self, prompt: str) -> list:
        response = requests.request("GET", self.url + 'games', headers=self.headers, params={'name': prompt, 'max': self.MAX_ENTRIES})
        names = [game['names']['international'] for game in response.json()['data']]

        return names
