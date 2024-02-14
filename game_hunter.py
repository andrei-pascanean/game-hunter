import streamlit as st
import pandas as pd

import requests
from collections import defaultdict

from datetime import datetime
import pytz

utc = pytz.UTC
today = datetime.utcnow().replace(tzinfo=utc).strftime('%Y-%m-%d %H:%M:%S%z')

# Function to calculate form (last 5 matches)
def calculate_form(matches):
    if len(matches) < 5:
        return ''.join(matches)
    else:
        return ''.join(matches[-5:])
    
def calculate_form_score(form):
    return form.count('W')*3 + form.count('D') if isinstance(form, str) else None

# Assuming you have a function to fetch and process your data
def fetch_process_data():
    uri = 'https://api.football-data.org/v4/competitions/DED/matches'
    headers = { 'X-Auth-Token': '5ee7f2b5ace94caf9f8668333873a90f' }

    response = requests.get(uri, headers=headers)
    data = response.json()['matches']

    matches_df = pd.json_normalize(data)

    cols_to_keep = [
        'utcDate', 'status', 'matchday', 'season.currentMatchday', 
        'homeTeam.tla', 'homeTeam.name', 'homeTeam.crest',
        'awayTeam.tla', 'awayTeam.name', 'awayTeam.crest',
        'score.winner', 'score.fullTime.home', 'score.fullTime.away'
    ]

    matches_df = (
        matches_df
        .filter(cols_to_keep)
        .rename(columns = {
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

    # Reinitializing the team_stats dictionary to reset the stats
    team_stats = defaultdict(lambda: {'points': 0, 'goals_for': 0, 'goals_against': 0, 'matches': []})

    # Function to update team stats
    def update_team_stats(team, goals_for, goals_against, result):
        team_stats[team]['goals_for'] += goals_for
        team_stats[team]['goals_against'] += goals_against
        team_stats[team]['matches'].append(result)
        if result == 'W':
            team_stats[team]['points'] += 3
        elif result == 'D':
            team_stats[team]['points'] += 1

    # Adjusting the code to calculate features using only preceding results
    new_data_preceding = []

    for _, row in matches_df.iterrows():
        if row['matchday'] <= row['currentmatchday']:

            home_team = row['home_team_name']
            away_team = row['away_team_name']
            home_goals = row['fthg']
            away_goals = row['ftag']
            result = row['ftr']

            # Prepare team rankings based on stats before this match
            teams_ranked = sorted(team_stats.keys(), key=lambda x: (team_stats[x]['points'], 
                                                                    team_stats[x]['goals_for'] - team_stats[x]['goals_against'], 
                                                                    team_stats[x]['goals_for']), 
                                reverse=True)

            # Append the new stats to the list
            new_row_data_preceding = {
                'home_position': teams_ranked.index(home_team) + 1 if home_team in team_stats else None,
                'away_position': teams_ranked.index(away_team) + 1 if away_team in team_stats else None,
                'home_points': team_stats[home_team]['points'] if home_team in team_stats else None,
                'away_points': team_stats[away_team]['points'] if away_team in team_stats else None,
                'home_goals_for': team_stats[home_team]['goals_for'] if home_team in team_stats else None,
                'away_goals_for': team_stats[away_team]['goals_for'] if away_team in team_stats else None,
                'home_goals_against': team_stats[home_team]['goals_against'] if home_team in team_stats else None,
                'away_goals_against': team_stats[away_team]['goals_against'] if away_team in team_stats else None,
                'home_form': calculate_form(team_stats[home_team]['matches']) if home_team in team_stats else None,
                'away_form': calculate_form(team_stats[away_team]['matches']) if away_team in team_stats else None
            }
            new_data_preceding.append(new_row_data_preceding)

            # Determine match result for home and away teams for updating stats after appending
            home_result = 'D' if result == 'DRAW' else 'W' if result == 'HOME_TEAM' else 'L'
            away_result = 'D' if result == 'DRAW' else 'L' if result == 'HOME_TEAM' else 'W'

            # Update team stats after recording the current stats
            update_team_stats(home_team, home_goals, away_goals, home_result)
            update_team_stats(away_team, away_goals, home_goals, away_result)

    result_df_preceding = pd.concat([matches_df.reset_index(drop=True), pd.DataFrame(new_data_preceding)], axis=1)

    top_3 = (
        result_df_preceding
        .query('matchday <= currentmatchday')
        .query(f'date >= "{today}"')
        .filter(['date', 'status', 'matchday', 'currentmatchday', 'home_team_tla', 'away_team_tla', 'fthg', 'ftag', 'home_form', 'away_form'])
        .assign(
            score_home_form = lambda df: df.apply(lambda row: calculate_form_score(row.home_form), axis = 1),
            score_away_form = lambda df: df.apply(lambda row: calculate_form_score(row.away_form), axis = 1),
            combined_form = lambda df: df.score_home_form  + df.score_away_form,
        )
        .sort_values('combined_form', ascending = False)
        .head(3)
    )

    return top_3

# Fetch and process data
data = fetch_process_data()

# Filter for upcoming matches with calculated form

st.title(f'Games to watch this week')
st.subheader('Tasty fixtures in the Eredivisie 🇳🇱')

st.dataframe(data)


