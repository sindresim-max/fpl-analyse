import requests

response = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/")
print(response.status_code)

data = response.json()
print(data.keys())

players = data["elements"]
print(len(players))

first = players[0]
print(first["web_name"])
print(first["team"])
print(first["element_type"])
print(first["now_cost"])
print(first["total_points"])