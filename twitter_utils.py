import json
import os
from typing import Optional, Dict

import requests

from utils import log


def create_headers():
    return {"Authorization": "Bearer {}".format(os.environ['TWITTER_BEARER_TOKEN'])}


def set_rules(user: str) -> str:
    sample_rules = [
        {"value": f"from:{user}", "tag": "crypto_pump"},
    ]
    payload = {"add": sample_rules}
    response = requests.post(
        "https://api.twitter.com/2/tweets/search/stream/rules",
        headers=create_headers(),
        json=payload,
    )
    if response.status_code != 201:
        raise Exception(
            "Cannot add rules (HTTP {}): {}".format(response.status_code, response.text)
        )
    return json.dumps(response.json())


def delete_all_rules(rules: Dict) -> Optional[str]:
    if rules is None or "data" not in rules:
        return None

    ids = list(map(lambda rule: rule["id"], rules["data"]))
    payload = {"delete": {"ids": ids}}
    response = requests.post(
        "https://api.twitter.com/2/tweets/search/stream/rules",
        headers=create_headers(),
        json=payload
    )
    if response.status_code != 200:
        raise Exception(
            "Cannot delete rules (HTTP {}): {}".format(
                response.status_code, response.text
            )
        )
    return response.json()


def get_rules() -> Dict:
    response = requests.get(
        "https://api.twitter.com/2/tweets/search/stream/rules", headers=create_headers()
    )
    if response.status_code != 200:
        raise Exception(
            "Cannot get rules (HTTP {}): {}".format(response.status_code, response.text)
        )
    return response.json()


def reset_twitter_subscription_rules(user: str):
    rules = get_rules()
    log('Current twitter subscription rules', rules)
    delete_status = delete_all_rules(rules)
    log('Delete twitter subscription rules status', delete_status)
    log('Set twitter subscription rules status', set_rules(user))
