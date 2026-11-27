import requests
import pandas as pd
import matplotlib.pyplot as plt
from openpyxl.drawing.image import Image
from openpyxl.styles import Font
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.formatting.rule import ColorScaleRule

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

filtered_df["points_per_90"] = filtered_df["total_points"] / filtered_df["minutes"] * 90
top_quality = filtered_df[filtered_df["minutes"] >= 450].sort_values("points_per_90", ascending=False)
print(top_quality[["web_name", "team_name", "position", "price", "minutes", "points_per_90"]].head(10))

top10 = top_value.head(10)
plt.scatter(filtered_df["price"], filtered_df["total_points"], color="lightgray", label="All players")
plt.scatter(top10["price"], top10["total_points"], color="red", label="Top 10 value")
plt.xlabel("Price (million)")
plt.ylabel("Total points")
plt.title("Price vs total points")
plt.legend()
plt.savefig("price_vs_points.png")
plt.clf()
#plt.show()

top10_points = filtered_df.sort_values("total_points", ascending=False).head(10)
plt.barh(top10_points["web_name"], top10_points["total_points"])
plt.gca().invert_yaxis()
plt.xlabel("Total points")
plt.title("Top 10 players by total points")
plt.tight_layout()
plt.savefig("top_points.png")
#plt.show()

team_id = 6803366
entry_url = f"https://fantasy.premierleague.com/api/entry/{team_id}/"
entry_data = requests.get(entry_url).json()
print(entry_data.keys())
print(entry_data["name"], entry_data["current_event"])

gw = entry_data["current_event"]
picks_url = f"https://fantasy.premierleague.com/api/entry/{team_id}/event/{gw}/picks/"
picks_data = requests.get(picks_url).json()
my_team = pd.DataFrame(picks_data["picks"])
my_team = my_team.merge(players_df, left_on="element", right_on="id")
print(my_team[["web_name", "team_name", "position_y", "price", "total_points", "is_captain"]])

my_team = my_team.rename(columns={"position_y": "position"})
my_team["points_per_million"] = my_team["total_points"] / my_team["price"]
my_team["price_band"] = pd.cut(my_team["price"], bins=bins, labels=labels, right=False)
comparison = my_team.merge(best_by_band, on=["position", "price_band"], how="left", suffixes=("_mine", "_best"))
print(comparison[["web_name_mine", "position", "price_band", "points_per_million_mine", "web_name_best", "points_per_million_best"]])

bank = entry_data["last_deadline_bank"]
bank = bank / 10
print(bank)

fixtures_url = "https://fantasy.premierleague.com/api/fixtures/"
fixtures_df = pd.DataFrame(requests.get(fixtures_url).json())
next_fixtures = fixtures_df[(fixtures_df["event"] > gw) & (fixtures_df["event"] <= gw + 3)]
home = next_fixtures[["team_h", "team_h_difficulty"]].rename(columns={"team_h": "team", "team_h_difficulty": "difficulty"})
away = next_fixtures[["team_a", "team_a_difficulty"]].rename(columns={"team_a": "team", "team_a_difficulty": "difficulty"})
team_difficulty = pd.concat([home, away]).groupby("team")["difficulty"].mean()
team_map = players_df[["team", "team_name"]].drop_duplicates()
team_difficulty = team_difficulty.reset_index().merge(team_map, on="team")
print(team_difficulty.sort_values("difficulty"))

filtered_df = filtered_df.merge(team_difficulty[["team_name", "difficulty"]], on="team_name", how="left")
filtered_df = filtered_df.merge(players_df[["web_name", "team_name", "chance_of_playing_next_round", "news"]], on=["web_name", "team_name"], how="left")
filtered_df["chance_of_playing_next_round"] = filtered_df["chance_of_playing_next_round"].fillna(100)
print(filtered_df[["web_name", "team_name", "position", "price", "difficulty"]].sort_values("difficulty").head(10))
print(filtered_df["difficulty"].isna().sum())


def suggest_transfer(player_name):
    player = my_team[my_team["web_name"] == player_name].iloc[0]
    budget = player["price"] + bank
    full_teams = my_team[my_team["web_name"] != player_name]["team_name"].value_counts()[lambda counts: counts >= 3].index
    candidates = filtered_df[
        (filtered_df["position"] == player["position"])
        & (filtered_df["price"] <= budget)
        & (~filtered_df["web_name"].isin(my_team["web_name"]))
        & (~filtered_df["team_name"].isin(full_teams))
        & (filtered_df["chance_of_playing_next_round"] >= 75)
    ].copy()
    candidates["score"] = candidates["points_per_game"] / candidates["difficulty"]
    return candidates.sort_values(["score", "price"], ascending=[False, True]).head(3)

print(suggest_transfer("Vuskovic")[["web_name", "team_name", "price", "points_per_game", "difficulty", "score"]])

my_team = my_team.merge(team_difficulty[["team_name", "difficulty"]], on="team_name", how="left")
my_team["score"] = pd.to_numeric(my_team["points_per_game"]) / my_team["difficulty"]

suggestions = []
for name in my_team["web_name"]:
    best = suggest_transfer(name)
    if len(best) > 0:
        own_score = my_team[my_team["web_name"] == name]["score"].iloc[0]
        suggestions.append({"sell": name, "own_score": own_score, "buy": best["web_name"].iloc[0], "buy_price": best["price"].iloc[0], "buy_score": best["score"].iloc[0]})

suggestions_df = pd.DataFrame(suggestions)
suggestions_df["gain"] = suggestions_df["buy_score"] - suggestions_df["own_score"]
print(suggestions_df.sort_values("gain", ascending=False))

best_move = suggestions_df.sort_values("gain", ascending=False).iloc[0]
summary_df = pd.DataFrame({
    "Metric": ["Team", "Gameweek", "Total points", "Bank (million)", "Best transfer", "Gain in score"],
    "Value": [entry_data["name"], gw, entry_data["summary_overall_points"], bank, best_move["sell"] + " -> " + best_move["buy"], round(best_move["gain"], 2)],
})

starters = [pick["element"] for pick in picks_data["picks"] if pick["multiplier"] > 0]
captain_pool = my_team[["id", "web_name", "team_name", "position", "difficulty"]].merge(players_df[["web_name", "team_name", "expected_goal_involvements_per_90", "form", "chance_of_playing_next_round"]], on=["web_name", "team_name"], how="left")
captain_pool["chance_of_playing_next_round"] = captain_pool["chance_of_playing_next_round"].fillna(100)
captain_pool = captain_pool[(captain_pool["position"].isin(["MID", "FWD"])) & (captain_pool["chance_of_playing_next_round"] >= 75) & (captain_pool["id"].isin(starters))].copy()
captain_pool["xgi90"] = pd.to_numeric(captain_pool["expected_goal_involvements_per_90"])
captain_pool["form_num"] = pd.to_numeric(captain_pool["form"])
captain_pool["captain_score"] = (0.7 * captain_pool["xgi90"] * 5 + 0.3 * captain_pool["form_num"]) * (1 + (3 - captain_pool["difficulty"]) * 0.1)
captains = captain_pool.sort_values("captain_score", ascending=False).head(3)
print(captain_pool.sort_values("captain_score", ascending=False)[["web_name", "xgi90", "form_num", "difficulty", "captain_score"]])

captain_rows = pd.DataFrame({
    "Metric": ["Captain pick 1", "Captain pick 2", "Captain pick 3"],
    "Value": [f"{name} ({score:.2f})" for name, score in zip(captains["web_name"], captains["captain_score"])],
})
summary_df = pd.concat([summary_df, captain_rows], ignore_index=True)

not_owned = filtered_df[(~filtered_df["web_name"].isin(my_team["web_name"])) & (filtered_df["chance_of_playing_next_round"] >= 75)]
best_idx = not_owned.groupby(["position", "price_band"], observed=True)["points_per_million"].idxmax()
best_alt = not_owned.loc[best_idx, ["position", "price_band", "web_name", "points_per_million"]]
mine = filtered_df[filtered_df["web_name"].isin(my_team["web_name"])][["web_name", "position", "price_band", "points_per_million"]]
comparison = mine.merge(best_alt, on=["position", "price_band"], how="left", suffixes=("_mine", "_best")).sort_values(["position", "points_per_million_mine"], ascending=[True, False])

xgi_df = filtered_df[["web_name", "team_name", "position", "price"]].merge(players_df[["web_name", "team_name", "expected_goal_involvements_per_90"]], on=["web_name", "team_name"], how="left")
xgi_df["xgi90"] = pd.to_numeric(xgi_df["expected_goal_involvements_per_90"])
xgi_df["owned"] = xgi_df["web_name"].isin(my_team["web_name"]).map({True: "Yes", False: "No"})
top_xgi = xgi_df[xgi_df["position"].isin(["MID", "FWD"])].sort_values("xgi90", ascending=False).head(15)


report_sheets = {
    "Summary": summary_df,
        "Top xGI": top_xgi[["web_name", "team_name", "position", "price", "xgi90", "owned"]].rename(columns={
        "web_name": "Player", "team_name": "Team", "position": "Position", "price": "Price (m)", "xgi90": "xGI per 90", "owned": "Owned"}),
    "Transfers": suggestions_df.sort_values("gain", ascending=False).rename(columns={
        "sell": "Sell", "own_score": "Own score", "buy": "Buy", "buy_price": "Buy price (m)", "buy_score": "Buy score", "gain": "Gain"}),
    "My team": comparison[["web_name_mine", "position", "price_band", "points_per_million_mine", "web_name_best", "points_per_million_best"]].rename(columns={
        "web_name_mine": "Player", "position": "Position", "price_band": "Price band", "points_per_million_mine": "Points per million",
        "web_name_best": "Best alternative", "points_per_million_best": "Alternative points per million"}),
    "Best by price band": best_by_band[["position", "price_band", "web_name", "team_name", "price", "points_per_million"]].rename(columns={
        "position": "Position", "price_band": "Price band", "web_name": "Player", "team_name": "Team", "price": "Price (m)", "points_per_million": "Points per million"}),
    "Fixtures": team_difficulty.sort_values("difficulty")[["team_name", "difficulty"]].rename(columns={
        "team_name": "Team", "difficulty": "Average difficulty, next 3 rounds"}),
}
tab_colors = ["1F4E78", "2E75B6", "548235", "BF8F00", "C00000"]
green_to_red = ColorScaleRule(start_type="min", start_color="63BE7B", mid_type="percentile", mid_value=50, mid_color="FFFFFF", end_type="max", end_color="F8696B")
red_to_green = ColorScaleRule(start_type="min", start_color="F8696B", mid_type="num", mid_value=0, mid_color="FFFFFF", end_type="max", end_color="63BE7B")

with pd.ExcelWriter("fpl_report.xlsx", engine="openpyxl") as writer:
    for i, (name, df) in enumerate(report_sheets.items()):
        df.to_excel(writer, sheet_name=name, index=False, startrow=2)
        sheet = writer.sheets[name]
        sheet["A1"] = f"FPL report: {entry_data['name']}" if name == "Summary" else name
        sheet["A1"].font = Font(size=16, bold=True, color="1F4E78")
        sheet["A2"] = f"Gameweek {gw}. Data from the official FPL API."
        sheet["A2"].font = Font(italic=True, color="808080")
        sheet.sheet_view.showGridLines = False
        sheet.sheet_properties.tabColor = tab_colors[i]
        for column in sheet.iter_cols(min_row=3):
            longest = max(len(f"{cell.value:.2f}") if isinstance(cell.value, float) else len(str(cell.value)) for cell in column if cell.value is not None)
            sheet.column_dimensions[column[0].column_letter].width = longest + 4
            for cell in column[1:]:
                if isinstance(cell.value, float):
                    cell.number_format = "0.00"
        last_cell = sheet.cell(row=sheet.max_row, column=sheet.max_column).coordinate
        table = Table(displayName=f"Table{i}", ref=f"A3:{last_cell}")
        table.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
        sheet.add_table(table)
        sheet.freeze_panes = "A4"
    transfers = writer.sheets["Transfers"]
    transfers.conditional_formatting.add(f"F4:F{transfers.max_row}", red_to_green)
    fixtures = writer.sheets["Fixtures"]
    fixtures.conditional_formatting.add(f"B4:B{fixtures.max_row}", green_to_red)
print("Report saved: fpl_report.xlsx")

