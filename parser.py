import time

import requests
import json
from anticaptcha import Anticaptcha
import sql_adapter


class VinDcCheck:
    def __init__(self):
        self.captch_req_url = 'https://check.gibdd.ru/captcha'
        self.dc_check_url = 'https://xn--b1afk4ade.xn--90adear.xn--p1ai/proxy/check/auto/diagnostic'
        self.session = requests.Session()
        self.api_key = sql_adapter.get_setting('captcha_api_key')
        self.solver = Anticaptcha(token = self.api_key)

    def get_captcha(self):
        r = self.session.get(self.captch_req_url, verify=False)
        if r:
            result = r.json()
            #print(result.get('token'))
            res = self.resolve_captcha(result.get('base64jpg'))
            #print(js)
            result.update({'code': res})
        else:
            result = None
        #print(json.dumps(result, ensure_ascii=False, indent=2))
        return result

    def resolve_captcha(self, captcha_img_b64):
       # self.solver.normal()
        return self.solver.resolve_captcha(captcha_img_b64)

    def check_vin_code(self, vin_code):
        captcha = self.get_captcha()
        if captcha:
            c_token = captcha.get('token')
            try:
                c_code = int(captcha.get('code'))
            except:
                c_code = 0
            params = {
                'vin' : vin_code,
                'checkType' : 'diagnostic',
                'captchaWord' : c_code,
                'captchaToken' : c_token
            }
            self.session.headers.update({'Content-Type': 'application/x-www-form-urlencoded'})
            r = self.session.post(self.dc_check_url, data=params)
            #print(r.status_code)
            try:
                res = r.json()
                if res.get('code', 200) in ['201', 201]:
                    time.sleep(1)
                    print('Captcha error, retrying...')
                    self.check_vin_code(vin_code)
                    #return None
                #print(json.dumps(res,ensure_ascii=False,indent=2))
                res = res.get('RequestResult').get('diagnosticCards')
                res = sql_adapter.insert_vins(res)
                return res
            except Exception as e:
                print(e)
                res = None
                return res

    def process_vin(self, vin_code):
        vin = sql_adapter.check_vin(vin_code)
        if vin:
            return vin
        else:
            self.check_vin_code(vin_code)

if __name__ == '__main__':
    instance = VinDcCheck()
    dc = instance.process_vin('X9H47434A90000156')
    print(dc)