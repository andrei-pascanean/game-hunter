# game-hunter
Find exciting football games

# Initial Approach
The goal is to find interesting games. A game is interesting when the outcome is far from clear. The more uncertain the outcome, the higher chance that the game will be interesting.

Betting odds can eb used to measure how uncertain the crowd is about the outcome of a game.

Interesting info from Buraimo & Simmons (2008):

The sum of unadjusted (home win, away win, and draw) probabilities routinely exceeds unity due to the bookmaker’s margin. This margin, or ‘over- round’, was around 12% over our sample period. The adjusted probabilities are derived by dividing each of the probabilities by the sum of unadjusted probabilities. By doing so, the adjusted values sum to 1. 

(1/ decimal odds) * 100 = implied probability

The values of OUTCOME UNCERTAINTY, the absolute difference in home and away team probabilities, for televised games range from 0 to 0.712. A value of 0 represents matches with the highest degree of uncertainty, while high values represent those matches with a low degree of uncertainty. The values of uncertainty of outcome show that there is a high variation, given that the theoretical range is between 0 and 1. Hence, there is enough variation to capture any effect of uncertainty of outcome on audience rating. A shortcoming of this measure is that the draw probability is assumed constant. This is a reasonable assumption, since there is only a slight variation in the draw probabilities across matches. However, as a robustness check and to deal explicitly with the draw probability, an alternative measure of outcome uncertainty, the Theil measure, is also used (Buraimo and Simmons 2008; Czarnitzki and Stadtmann 2002; Peel and Thomas 1992). The Theil measure makes use of the probabilities of all three match outcomes and is derived as:

SUM(p_i * ln(1/p_i))

where Pi is the probability of outcome i, which is any one of the three possible results. It is highly likely that the results, qualitatively, would be similar, as the correlation coefficient between OUTCOME UNCERTAINTY and the Theil measure is –0.944.

The Theil measure is highest when all three probabilities are equal (win, draw and lose).

Our first approach will be to scrape betting odds and calculating this metric for each matchup. Matches with a high Theil score are deemed more uncertain and will rank as more 'interesting'.

# Day 1 Answer

Before we go into things that are too complicated, let's just focus on delivering a simple answer. Like using current leaderboard ranking, recent form and historical rivalries.

# Tech Backlog
- Add pre-commit hooks to codebase
- Remove data
- Use pyenv for creating the python environment
- Add setup docs

# Business Backlog
- All European leagues
    - Each league gets its own page
    - A page where you can compare all games across all leagues
- More info about why each game was selected
- A text summary on the landing page with the top-3 European leagues wide
    - We should be answering the question 'what game should I watch this week?'
- Continental UEFA leagues
  - Can be based off european ELO rating?
- Broadcaster info
    - Where can I watch this in country x?
- Free-to-watch games filter
- ELO rating of teams involved
- Favourite team according to betting odds
- UEFA Rank

# Roadmap

We need something that will create a moat. Currently our only moat is time and interest. The backend API is free and can be used by anyone, so our data is not unique.

- **Unsupervised Learning**: This can also be framed as an unsupervised learning problem, where descriptive statistics of each game can be used by a clustering algorithm to identify 'groups' of games. Ideally you would start with 2 groups that you hope the model learns as 'interesting' and 'not interesting'.

- **Supervised Learning**: To make this a supervised learning problem, you need a target variable. The way to find a target is by taking your end-goal and using it as a KPI that is estimated through other metrics. In our example how 'interesting' a game is can be partially measured by interest after the game. A proxy for this would be number of views on a highlights reel. Maybe viewership during a game would also work, as it allows you to find the natural most-viewed games by people who are non-neutral. 