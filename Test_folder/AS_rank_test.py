import requests
import json

url = "https://api.asrank.caida.org/v2/graphql"
query = """
{asnLinks(asn:"3356"){
  totalCount,
  pageInfo{first,offset},
  edges{node{
    relationship,
    asn1{asn,asnName},
    numberPaths
      }
}}}
"""
payload = {"query": query}
headers = {"Content-Type": "application/json"}

response = requests.post(url, json=payload, headers=headers)

if response.status_code == 200:
    data = response.json()
    print(json.dumps(data, indent=2))
else:
    print(f"Error: {response.status_code}")