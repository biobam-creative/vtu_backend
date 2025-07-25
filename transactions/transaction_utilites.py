import base64
import hashlib
import hmac
import json
from datetime import datetime
import requests


def compute_sha512(secret, data):
    data_string = json.dumps(data)
    body = json.loads(data_string)
    body_unicode = json.dumps(body, separators=(',', ':'))
    computed_hash = hmac.new(
        secret.encode('utf-8'),
        msg=body_unicode.encode('utf-8'),
        digestmod=hashlib.sha512
    ).hexdigest()
    return computed_hash


def monnify_encode_base64(api_key, secret_key):
    """
    Encode the API key, secret key into a base64 string.
    """
    data = f"{api_key}:{secret_key}"
    return f"Basic {base64.b64encode(data.encode('utf-8')).decode('ascii')}"


monnify_base_url = "https://sandbox.monnify.com"


class VTPassAPI:
    def __init__(self, api_key, public_key, secret_key):
        self.api_key = api_key
        self.public_key = public_key
        self.secret_key = secret_key
        self.base_url = 'https://sandbox.vtpass.com/api/'
        self.headers = {
            'api-key': self.api_key,
            'secret-key': self.secret_key,
            'public-key': self.public_key
        }

    def buy_service(self, service_id, amount, phone, variation_code=None, biller_code=None, type=None):
        now = datetime.now()
        request_id = now.strftime("%Y%m%d%H%M%S" + "necta")

        payload = {
            "request_id": request_id,
            "serviceID": service_id,
            "amount": amount,
            "phone": phone
        }
        if variation_code:
            payload["variation_code"] = variation_code
        if biller_code:
            payload["billerCode"] = biller_code
        if type:
            payload["type"] = type

        response = requests.post(
            f'{self.base_url}pay', headers=self.headers, data=payload)
        data = json.loads(response.text)
        print(data)
        return data

    def verify_mechant(self, billers_code, service_id):
        payload = {
            "billersCode": billers_code,
            "serviceID": service_id
        }
        response = requests.post(
            f'{self.base_url}verify', headers=self.headers, data=payload)
        data = json.loads(response.text)
        if data.get('status') == 'success':
            return data['data']
        else:
            raise Exception(f"Error: {data.get('message', 'Unknown error')}")

    def get_service_variations(self, service_id):
        response = requests.get(
            f'{self.base_url}service-variations?serviceID={service_id}', headers=self.headers)
        data = json.loads(response.text)
        if data.get('status') == 'success':
            return data['data']
        else:
            raise Exception(f"Error: {data.get('message', 'Unknown error')}")

    def query_transaction(self, request_id):
        payload = {
            "request_id": request_id
        }
        response = requests.post(
            f'{self.base_url}requery', headers=self.headers, data=payload)

        data = json.loads(response.text)

        return data
