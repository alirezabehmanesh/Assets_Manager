import requests

resp = requests.post("https://www.bonbast.com/json")
print(resp.json())
