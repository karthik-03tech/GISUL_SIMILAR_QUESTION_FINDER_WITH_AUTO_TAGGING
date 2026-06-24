import socket
import json
import urllib.request

old_getaddrinfo = socket.getaddrinfo

def new_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    if host == 'api-inference.huggingface.co':
        try:
            url = f"https://dns.google/resolve?name={host}&type=A"
            req = urllib.request.Request(url, headers={"Accept": "application/dns-json"})
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode("utf-8"))
                for answer in data.get("Answer", []):
                    if answer.get("type") == 1:
                        ip = answer.get("data")
                        print(f"Resolved {host} to {ip} via DoH")
                        return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', (ip, port))]
        except Exception as e:
            print("DoH failed:", e)
    return old_getaddrinfo(host, port, family, type, proto, flags)

socket.getaddrinfo = new_getaddrinfo

API_URL = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2"
try:
    req = urllib.request.Request(API_URL, headers={"Content-Type": "application/json"}, data=b'{"inputs":["Hello"],"options":{"wait_for_model":true}}')
    with urllib.request.urlopen(req) as response:
        print(response.status)
        print(response.read())
except Exception as e:
    print("Error:", e)
