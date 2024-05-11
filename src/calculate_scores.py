import pandas as pd

from collections import defaultdict
from datetime import datetime
import pytz

import constants as c
from support_functions import calculate_form, calculate_form_score, load_data

today = datetime.now().replace(tzinfo=pytz.UTC).strftime('%Y-%m-%d %H:%M:%S%z')

def fetch_process_data(league):

    matches_df = load_data(league)

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

leagues = ['DED']

fixtures_with_combined_form = []

for league in leagues:
    fixtures_with_combined_form.append(fetch_process_data(league))

# TODO: Add a 'combined' wins column to the sort in case there is a draw on the combined form column
data = pd.concat(fixtures_with_combined_form)

data = (
    data
    .assign(
        area_code = data.area_code.replace(c.AREA_CODES),
        date = pd.to_datetime(data.date).dt.strftime('%d-%m-%Y %H:%M'),
        combined_form = data.combined_form.astype(int)
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
<html data-bs-theme="dark">
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
file_name = "/Users/andreipascanean/Documents/GitHub/game-hunter/docs/index.html"

# Writing the HTML content to a file
with open(file_name, 'w') as html_file:
    html_file.write(html_content)

print(f"HTML file '{file_name}' has been created successfully.")