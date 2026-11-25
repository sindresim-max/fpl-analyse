import requests
import pandas as pd

response = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/")

data = response.json()

players = data["elements"]


players_df = pd.DataFrame(players)

teams_df = pd.DataFrame(data["teams"])

teams_small = teams_df[["id", "name"]].rename(columns={"id": "team", "name": "team_name"})
players_df = players_df.merge(teams_small, on="team", how="left")

types_df = pd.DataFrame(data["element_types"])

types_small = types_df[["id", "singular_name_short"]].rename(columns={"id": "element_type", "singular_name_short": "position"})
players_df = players_df.merge(types_small, on="element_type", how="left")

players_df["price"] = players_df["now_cost"] / 10

columns = ["web_name", "team_name", "position", "price", "total_points", "minutes", "form", "points_per_game", "status"]
clean_df = players_df[columns]


clean_df["form"] = pd.to_numeric(clean_df["form"])
clean_df["points_per_game"] = pd.to_numeric(clean_df["points_per_game"])


filtered_df = clean_df[(clean_df["minutes"] >= 450) | (clean_df["form"] >= 4.0)]
print(filtered_df.shape)

filtered_df["points_per_million"] = filtered_df["total_points"] / filtered_df["price"]

top_value = filtered_df.sort_values("points_per_million", ascending=False)
print(top_value[["web_name", "team_name", "position", "price", "total_points", "points_per_million"]].head(10))

