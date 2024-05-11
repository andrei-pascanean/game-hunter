import pandas as pd

import requests
from collections import defaultdict

from datetime import datetime
import pytz

utc = pytz.UTC
today = datetime.utcnow().replace(tzinfo=utc).strftime('%Y-%m-%d %H:%M:%S%z')

area_codes = {
    'NLD': '🇳🇱',
    'ENG': '🏴󠁧󠁢󠁥󠁮󠁧󠁿',
    'ESP': '🇪🇸',
    'FRA': '🇫🇷',
    'ITA': '🇮🇹',
    'DEU': '🇩🇪',
    'POR': '🇵🇹'
}

# Function to calculate form (last 5 matches)
def calculate_form(matches):
    if len(matches) < 5:
        return ''.join(matches)
    else:
        return ''.join(matches[-5:])
    
def calculate_form_score(form):
    return form.count('W')*3 + form.count('D') if isinstance(form, str) else None

# Assuming you have a function to fetch and process your data
def fetch_process_data(league):

    # TODO: Move these data ingest + preprocessing steps out of the main loop
    uri = f'https://api.football-data.org/v4/competitions/{league}/matches'
    headers = { 'X-Auth-Token': '5ee7f2b5ace94caf9f8668333873a90f' }

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

    upcoming_matchdays = (
        matches_df
        .query('(matchday <= currentmatchday + 1) & (status != "FINISHED") & (status != "POSTPONED")')
    ).matchday.unique().tolist()

    if len(upcoming_matchdays) < 1:
        return

    active_matchday = upcoming_matchdays[0]

    for _, row in matches_df.iterrows():
        if row['matchday'] <= active_matchday:

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

    result = (
        result_df_preceding
        .query(f'currentmatchday <= matchday <= {active_matchday}')
        .query(f'date >= "{today}"')
        .assign(
            score_home_form = lambda df: df.apply(lambda row: calculate_form_score(row.home_form), axis = 1),
            score_away_form = lambda df: df.apply(lambda row: calculate_form_score(row.away_form), axis = 1),
            combined_form = lambda df: df.score_home_form  + df.score_away_form,
        )
        .filter(['area_code', 'competition_name', 'date', 'home_team_name', 'away_team_name', 'home_form', 'away_form', 'combined_form'])
    )

    return result

leagues = ['DED', 'PL', 'PD', 'ELC', 'FL1', 'BL1', 'SA', 'PPL']
# leagues = ['DED', 'PL', 'PD', 'FL1', 'BL1', 'SA']
# leagues = ['DED']

fixtures_with_combined_form = []

for league in leagues:
    fixtures_with_combined_form.append(fetch_process_data(league))

# TODO: Add a 'combined' wins column to the sort in case there is a draw on the combined form column
data = pd.concat(fixtures_with_combined_form)

data = (
    data
    .assign(
        area_code = data.area_code.replace(area_codes),
        date = pd.to_datetime(data.date).dt.strftime('%d-%m-%Y %H:%M')
    )
    .sort_values('combined_form', ascending=False)
    [["date", "area_code", "home_team_name", "away_team_name", "combined_form"]]
)

html_table = (
    data
    .rename(columns={col: col.replace('_', ' ').title() for col in data.columns})
    .rename(columns={'Area Code':'Competition', 'Home Team Name':'Home Team', 'Away Team Name':'Away Team'})
    .to_html(
        classes = "table table-striped custom-font-size",
        justify = "left",
        index = False,
        border = 0
    )
)

html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>This Week's Bangers</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH" crossorigin="anonymous">
    <style>
        /* Custom CSS styles */
        .custom-font-size {{
            font-size: 0.8rem;
        }}
    </style>
</head>
<body class="pt-4">
    <div class="container-fluid">
        <div class="row">
            <div class="col-2"></div>
            <div class="col-8 mb-3"><h1>This Week's Bangers</h1></div>
            <div class="col-2"></div>
        </div>
        <div class="row">
            <div class="col-2"></div>
            <div class="col-8">{html_table}</div>
            <div class="col-2"></div>
        </div>
    </div>
</body>
</html>
"""

# Specify the name of the HTML file
file_name = "/Users/andreipascanean/Documents/GitHub/game-hunter/example.html"

# Writing the HTML content to a file
with open(file_name, 'w') as html_file:
    html_file.write(html_content)

print(f"HTML file '{file_name}' has been created successfully.")

# TODO: Present the data in a nicer way
# TODO: Add filtering possibility to the data

# TODO: Add some text explaining what you are doing behind the scenes

