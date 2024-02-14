import requests

import config
import sql_adapter

conf = config.DATABASE


def get_proxies_from_url(url=f"http://api-external.tm.8525.ru/proxies?token=5jossnicxhn75lht7aimal7r2ocvg6o7"):
    r = requests.get(url, verify=False)
    if r.status_code == 200:
        plist = r.json().get('results')
    else:
        plist = None
    return plist


def update_proxies():
    proxies = get_proxies_from_url()
    sql_adapter.update_proxies(proxies)


if __name__ == "__main__":
    update_proxies()
