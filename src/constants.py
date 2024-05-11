import os
from dotenv import load_dotenv

load_dotenv()

AREA_CODES = {
    'NLD': '🇳🇱',
    'ENG': '🏴󠁧󠁢󠁥󠁮󠁧󠁿',
    'ESP': '🇪🇸',
    'FRA': '🇫🇷',
    'ITA': '🇮🇹',
    'DEU': '🇩🇪',
    'POR': '🇵🇹'
}

SUPPORTED_LEAGUES = ['DED', 'PL', 'PD', 'ELC', 'FL1', 'BL1', 'SA', 'PPL']

FOOTBALL_API_TOKEN = os.getenv('FOOTBALL_API_TOKEN')

FOOTBALL_API_URL = 'https://api.football-data.org/v4/competitions/'