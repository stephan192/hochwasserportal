import requests

resp = requests.get('https://www.hochwasserzentralen.de/webservices/get_lagepegel.php')
jsondata = resp.json()
pgnr = jsondata["PGNR"]
pgnr.sort()

f = open("pegel.md", "w", encoding="utf-8")

output = "| Pegel | Description |"
print(output)
print(output, file=f)
output = "|-------|-------------|"
print(output)
print(output, file=f)
for pegel in pgnr:
    resp = requests.post('https://www.hochwasserzentralen.de/webservices/get_infospegel.php', data={'pgnr': pegel})
    jsondata = resp.json()
    output = "| " + pegel + " | " + jsondata["PN"] + " / " + jsondata["GW"] + " |"
    print(output)
    print(output, file=f)

f.close()