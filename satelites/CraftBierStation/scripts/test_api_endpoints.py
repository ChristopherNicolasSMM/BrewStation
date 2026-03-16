import requests
BASE = "http://127.0.0.1:5002/api"
def run():
    try:
        r = requests.get(f"{BASE}/sensors")
        print(f"Status API: {r.status_code}")
    except:
        print("Servidor offline")
if __name__ == "__main__": run()
