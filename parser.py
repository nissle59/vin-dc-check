import time

import requests

from anticaptcha import Anticaptcha


def get_proxies_from_url(url=f"http://api-external.tm.8525.ru/proxies?token=5jossnicxhn75lht7aimal7r2ocvg6o7"):
    r = requests.get(url, verify=False)
    if r.status_code == 200:
        plist = r.json().get('results')
    else:
        plist = None
    return plist


class VinDcCheck:
    def __init__(self):
        self.captch_req_url = 'https://check.gibdd.ru/captcha'
        self.dc_check_url = 'https://xn--b1afk4ade.xn--90adear.xn--p1ai/proxy/check/auto/diagnostic'
        self.session = requests.Session()
        # self.api_key = sql_adapter.get_setting('captcha_api_key')
        self.api_key = 'e9e783d3e52abd6101fc807ab1109400'
        self.solver = Anticaptcha(token=self.api_key)

    def get_captcha(self):
        r = self.session.get(self.captch_req_url, verify=False)
        if r:
            result = r.json()
            # print(result.get('token'))
            res = self.resolve_captcha(result.get('base64jpg'))
            # print(js)
            result.update({'code': res})
        else:
            result = None
        # print(json.dumps(result, ensure_ascii=False, indent=2))
        return result

    def resolve_captcha(self, captcha_img_b64):
        # self.solver.normal()
        return self.solver.resolve_captcha(captcha_img_b64)

    def get_vin_code(self, vin_code):
        captcha = self.get_captcha()
        if captcha:
            c_token = captcha.get('token')
            try:
                c_code = int(captcha.get('code'))
            except:
                c_code = 0
            params = {
                'vin': vin_code,
                'checkType': 'diagnostic',
                'captchaWord': c_code,
                'captchaToken': c_token
            }
            self.session.headers.update({'Content-Type': 'application/x-www-form-urlencoded'})
            r = self.session.post(self.dc_check_url, data=params)
            try:
                # print(r.text)
                res = r.json()
                try:
                    if res.get('code', 200) in ['201', 201]:
                        time.sleep(1)
                        print('Captcha error, retrying...')
                        self.get_vin_code(vin_code)
                except:
                    pass
                res = res.get('RequestResult').get('diagnosticCards')
                return res
            except Exception as e:
                print(e)
                res = None
                return res


if __name__ == '__main__':
    instance = VinDcCheck()
    dc = instance.process_vin('X9H47434A90000156')
    print(dc)
