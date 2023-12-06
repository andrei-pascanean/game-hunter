import streamlit as st
import pandas as pd
import numpy as np

st.title('Game Hunter')

st.header('Eredivisie Gameweek 15 Matches')

def adjusted_probs(home_odds, draw_odds, away_odds):

    keys = [f'implied_p_{i}' for i in ['home', 'draw', 'away']]
    values = [(1/odds) * 100 for odds in [home_odds, draw_odds, away_odds]]
    d = dict(zip(keys, values))

    return d

df = (
    pd.read_csv('data/N1-2.csv')
    .filter(['Div', 'Date', 'HomeTeam', 'AwayTeam', 'B365H', 'B365D', 'B365A'])
    .rename({
        'B365H': 'odds_home', 
        'B365D': 'odds_draw', 
        'B365A': 'odds_away'
    })
    .assign(Date=lambda x: pd.to_datetime(x['Date'], format='%d/%m/%Y'))
    .query('Date >= "2023-12-01"') # selecting the latest round of games
    .assign(
        adj_p_home = lambda df: df.apply(
            lambda row: row, 
            axis=1
        ),
    )
)