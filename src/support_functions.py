import pandas as pd

import requests
from typing import Optional

import constants as c

def calculate_form(matches: pd.Series) -> str:
    if len(matches) < 5:
        return ''.join(matches)
    else:
        return ''.join(matches[-5:])
    
def calculate_form_score(form: str) -> Optional[int]:
    return form.count('W')*3 + form.count('D') if isinstance(form, str) else None

def load_data(league: str):
    uri = c.FOOTBALL_API_URL + league + '/matches'
    headers = {'X-Auth-Token': c.FOOTBALL_API_TOKEN}

    response = requests.get(uri, headers=headers)
    data = response.json()['matches']

    matches_df = pd.json_normalize(data)

    cols_to_keep = [
        'area.code','competition.name',
        'utcDate', 'status', 'matchday', 'season.currentMatchday', 
        'homeTeam.tla', 'homeTeam.name', 'homeTeam.crest',
        'awayTeam.tla', 'awayTeam.name', 'awayTeam.crest',
        'score.winner', 'score.fullTime.home', 'score.fullTime.away'
    ]

    matches_df = (
        matches_df
        .filter(cols_to_keep)
        .rename(columns = {
            'area.code': 'area_code',
            'competition.name': 'competition_name',
            'utcDate': 'date', 
            'season.currentMatchday':'currentMatchday',
            'homeTeam.tla':'home_team_tla',
            'homeTeam.name': 'home_team_name', 
            'homeTeam.crest': 'home_team_crest',
            'awayTeam.tla': 'away_team_tla', 
            'awayTeam.name': 'away_team_name', 
            'awayTeam.crest': 'away_team_crest',
            'score.winner': 'ftr', 
            'score.fullTime.home': 'fthg', 
            'score.fullTime.away': 'ftag'
        })
        .rename(columns=str.lower)
    )

    # Convert 'date' to datetime and sort the dataframe
    matches_df['date'] = pd.to_datetime(matches_df['date'], utc = True)
    matches_df.sort_values(by=['date'], inplace=True)
    
    return matches_df