import requests
from datetime import datetime, timedelta
from collections import defaultdict
from colorama import Fore, Style, init

init(autoreset=True)  # Auto-reset colors after each print

def get_games(start_date, end_date):
    url = (
        f"https://statsapi.mlb.com/api/v1/schedule?"
        f"sportId=1&startDate={start_date}&endDate={end_date}&hydrate=team,linescore"
    )
    response = requests.get(url)
    return response.json()["dates"]

def parse_series_data(dates):
    series = defaultdict(list)

    for day in dates:
        for game in day["games"]:
            home = game["teams"]["home"]["team"]["name"]
            away = game["teams"]["away"]["team"]["name"]
            game_id = game["gamePk"]
            status = game["status"]["abstractGameState"]

            key = tuple(sorted([home, away]))  # Normalize key
            series[key].append({
                "home": home,
                "away": away,
                "winner": None,
                "status": status,
                "game_id": game_id,
                "date": day["date"]
            })

            home_team_info = game["teams"]["home"]
            away_team_info = game["teams"]["away"]

            if "score" in home_team_info and "score" in away_team_info:
                home_score = home_team_info["score"]
                away_score = away_team_info["score"]

                if home_score > away_score:
                    series[key][-1]["winner"] = home
                else:
                    series[key][-1]["winner"] = away

    return series

def find_sweep_risks(series):
    sweep_risks = []

    for matchup, games in series.items():
        teams = set(matchup)
        results = defaultdict(int)
        total_games = len(games)
        final_games = [g for g in games if g["status"] == "Final"]
        remaining_games = total_games - len(final_games)

        if len(final_games) < 1 or remaining_games == 0:
            continue

        for g in final_games:
            if g["winner"]:
                results[g["winner"]] += 1

        for team in teams:
            if results[team] == 0:
                sweep_risks.append({
                    "team": team,
                    "opponent": list(teams - {team})[0],
                    "games_played": len(final_games),
                    "games_remaining": remaining_games
                })

    return sweep_risks

# ==== MAIN SCRIPT ====

today = datetime.now().date()
start = (today - timedelta(days=4)).isoformat()
end = (today + timedelta(days=1)).isoformat()

try:
    dates = get_games(start, end)
    series = parse_series_data(dates)
    risks = find_sweep_risks(series)

    print("\nTeams at risk of being swept:\n")

    if risks:
        for r in risks:
            team_risk = f"{Fore.RED}{r['team']}{Style.RESET_ALL}"
            opponent = r['opponent']
            print(f"{team_risk} vs {opponent}: Lost first {r['games_played']} game(s), {r['games_remaining']} left.")
    else:
        print("No teams currently at risk of being swept.")
except Exception as e:
    print(f"Error occurred: {e}")
