import requests
import pandas as pd

response = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/")
print(response.status_code)

data = response.json()
print(data.keys())

players = data["elements"]
print(len(players))


players_df = pd.DataFrame(players)
print(players_df.shape)
print(players_df[["web_name", "team", "element_type", "now_cost", "total_points"]].head())

teams_df = pd.DataFrame(data["teams"])
print(teams_df[["id", "name", "short_name"]])

teams_small = teams_df[["id", "name"]].rename(columns={"id": "team", "name": "team_name"})
players_df = players_df.merge(teams_small, on="team", how="left")
print(players_df[["web_name", "team", "team_name"]].head())

types_df = pd.DataFrame(data["element_types"])
print(types_df[["id", "singular_name", "singular_name_short"]])

types_small = types_df[["id", "singular_name_short"]].rename(columns={"id": "element_type", "singular_name_short": "position"})
players_df = players_df.merge(types_small, on="element_type", how="left")
print(players_df[["web_name", "team_name", "position"]].head())

players_df["price"] = players_df["now_cost"] / 10
print(players_df[["web_name", "position", "now_cost", "price"]].head())

columns = ["web_name", "team_name", "position", "price", "total_points", "minutes", "form", "points_per_game", "status"]
clean_df = players_df[columns]
print(clean_df.shape)
print(clean_df.head())

clean_df["form"] = pd.to_numeric(clean_df["form"])
clean_df["points_per_game"] = pd.to_numeric(clean_df["points_per_game"])

print(clean_df.dtypes)

print(clean_df.isna().sum())

filtered_df = clean_df[(clean_df["minutes"] >= 450) | (clean_df["form"] >= 4.0)]
print(filtered_df.shape)


