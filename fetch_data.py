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

position_summary = filtered_df.groupby("position")["points_per_million"].mean()
print(position_summary)

best_per_position = top_value.groupby("position").head(3)
best_per_position = best_per_position.sort_values(["position", "points_per_million"], ascending=[True, False])
print(best_per_position[["web_name", "team_name", "position", "price", "points_per_million"]])

bins = [0, 5, 6, 7, 8, 9, 20]
labels = ["under 5", "5-6", "6-7", "7-8", "8-9", "9+"]
filtered_df["price_band"] = pd.cut(filtered_df["price"], bins=bins, labels=labels, right=False)
print(filtered_df["price_band"].value_counts())

best_by_band = filtered_df.sort_values("points_per_million", ascending=False)
best_by_band = best_by_band.groupby(["position", "price_band"], observed=True).head(1)
best_by_band = best_by_band.sort_values(["position", "price_band"])
print(best_by_band[["position", "price_band", "web_name", "team_name", "price", "points_per_million"]])

