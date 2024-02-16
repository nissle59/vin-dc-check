import threading
import time
import warnings
from itertools import cycle

import requests

import config
from anticaptcha import Anticaptcha

warnings.filterwarnings("ignore")

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

    def get_captcha(self, proxy=None):
        if proxy:
            r = self.session.get(self.captch_req_url, verify=False, proxies=proxy)
        else:
            r = self.session.get(self.captch_req_url, verify=False)
        if r:
            result = r.json()
            # config.logger.info(result.get('token'))
            res = self.resolve_captcha(result.get('base64jpg'))
            # config.logger.info(js)
            result.update({'code': res})
        else:
            result = None
        # config.logger.info(json.dumps(result, ensure_ascii=False, indent=2))
        return result

    def resolve_captcha(self, captcha_img_b64):
        # self.solver.normal()
        return self.solver.resolve_captcha(captcha_img_b64)

    def get_vin_code(self, vin_code, proxy=None):
        config.logger.debug(f'{vin_code} - Start')
        captcha = self.get_captcha(proxy)
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
            if proxy:
                r = self.session.post(self.dc_check_url, data=params, verify=False, proxies=proxy)
            else:
                r = self.session.post(self.dc_check_url, data=params, verify=False)
            try:
                # config.logger.info(r.text)
                res = r.json()

                if res.get('code', 200) in ['201', 201]:
                    time.sleep(1)
                    config.logger.debug(f'{vin_code} Captcha error, retrying...')
                    return self.get_vin_code(vin_code, proxy)

                result = res.get('RequestResult').get('diagnosticCards')
                for r in result:
                    r['vin'] = vin_code
                config.logger.info(f'{vin_code} - Success')

            except Exception as e:
                if res.get('code', 200) in ['201', 201]:
                    pass
                else:
                    config.logger.debug(e)
                    with open(f'responses/{vin_code}.txt', 'w') as f:
                        ex = ''
                        for arg in e.args:
                            ex += arg + '\n'
                        f.write(str(r.status_code) + '\n' + r.text + '\n\n' + str(ex))
                result = None
                config.logger.debug(f'{vin_code} - Failed')
            return result

    def get_vin_codes(self, vins: list, use_proxy=False):
        result = []
        for vin in vins:
            # self.get_vin_code(vin, proxy)
            c = 0
            prx = None
            while c <= config.tries:
                try:
                    if use_proxy:
                        prx = next(config.r_proxies)
                        config.logger.debug(f'Trying proxy {prx["http"]}')
                    vin = self.get_vin_code(vin, prx)
                    result.append(vin)
                    break
                except StopIteration:
                    if use_proxy:
                        config.r_proxies = cycle(config.proxies)
                        prx = next(config.r_proxies)
                    c += 1
                except Exception as e:
                    config.logger.info(e)
                    if use_proxy:
                        prx = next(config.r_proxies)
                    c += 1

    def multithreading_get_vins(self, vins, use_proxy=True):
        t_s = []
        tc = config.threads
        l_count, l_mod = divmod(len(vins), tc)
        l_mod = len(vins) % tc
        if l_mod != 0:

            l_mod = len(vins) % config.threads
            if l_mod == 0:
                tc = config.threads
                l_count = len(vins) // tc

            else:
                tc = config.threads - 1
                l_count = len(vins) // tc

        l_c = []
        for i in range(0, config.threads):
            config.logger.info(f'{i + 1} of {config.threads}')

            l_c.append(vins[l_count * i:l_count * i + l_count])

        for i in range(0, config.threads):
            t_s.append(
                threading.Thread(target=self.get_vin_codes, args=(l_c[i], use_proxy), daemon=True))
        for t in t_s:
            t.start()
            config.logger.info(f'Started thread #{t_s.index(t) + 1} of {len(t_s)} with {len(l_c[t_s.index(t)])} vins')

        for t in t_s:
            t.join()
            config.logger.info(f'Joined thread #{t_s.index(t) + 1} of {len(t_s)} with {len(l_c[t_s.index(t)])} vins')


if __name__ == '__main__':
    pass
