import ujson
import urequests
import config as cfg

API_URL = cfg.API_URL
API_KEY = cfg.API_KEY

def send_packet(packet):
    headers = { # Sends the type of communication and the api key to do it
        "Content-Type": "application/json",
        "x-api-key": API_KEY
    }

    response = None
    try:
        response = urequests.post(
            API_URL,
            data=ujson.dumps(packet), # Turns data into json
            headers=headers

        )
        print("HTTPS: Status:", response.status_code)
        print("HTTPS Response", response.text)
        return response.status_code == 200
    
    except Exception as e:
        print("POST Failed:", e)
        return False
    finally:
        if response:
            response.close()