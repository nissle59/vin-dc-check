import asyncio
import datetime
import threading
import time
import warnings
from itertools import cycle

import requests

import config
import sql_adapter
from anticaptcha import Anticaptcha

warnings.filterwarnings("ignore")

def get_proxies_from_url(url=f"http://api-external.tm.8525.ru/proxies?token=5jossnicxhn75lht7aimal7r2ocvg6o7"):
    r = requests.get(url, verify=False)
    if r.status_code == 200:
        try:
            plist = r.json().get('results')
        except:
            plist = []
    else:
        plist = []
    return plist


def get_vins_from_url(url='http://api-external.tm.8525.ru/vins?token=5jossnicxhn75lht7aimal7r2ocvg6o7'):
    r = requests.get(url, verify=False)
    if r.status_code == 200:
        try:
            plist = r.json().get('results')
        except:
            plist = []
    else:
        plist = []
    return plist


class VinDcCheck:
    def __init__(self, proxy=None):
        self.results = []
        self.captch_req_url = 'https://check.gibdd.ru/captcha'
        self.dc_check_url = 'https://xn--b1afk4ade.xn--90adear.xn--p1ai/proxy/check/auto/diagnostic'
        self.session = requests.Session()
        # self.api_key = sql_adapter.get_setting('captcha_api_key')
        self.api_key = 'e9e783d3e52abd6101fc807ab1109400'
        self.solver = Anticaptcha(token=self.api_key)
        self.proxy = proxy
        self.captcha_iter = 0
        self.captcha = None

    def get_captcha(self):
        if self.proxy:
            try:
                r = self.session.get(self.captch_req_url, verify=False, proxies=self.proxy)
            except:
                self.proxy = next(config.r_proxies)
                return self.get_captcha()
        else:
            r = self.session.get(self.captch_req_url, verify=False)
        if r:
            try:
                result = r.json()
                res = self.resolve_captcha(result.get('base64jpg'))
                result.update({'code': res})
                self.captcha_iter += 1
            except:
                result = None
        else:
            result = None
        return result

    def resolve_captcha(self, captcha_img_b64):
        return self.solver.resolve_captcha(captcha_img_b64)

    def get_vin_code(self, vin_code):
        if not self.captcha:
            self.captcha = self.get_captcha()
        if self.captcha:
            try:
                c_token = self.captcha.get('token')
                c_code = int(self.captcha.get('code'))
            except:
                c_code = 0
                c_token = ''
            params = {
                'vin': vin_code,
                'checkType': 'diagnostic',
                'captchaWord': c_code,
                'captchaToken': c_token
            }
            self.session.headers.update({'Content-Type': 'application/x-www-form-urlencoded'})
            if self.proxy:
                try:
                    r = self.session.post(self.dc_check_url, data=params, verify=False, proxies=self.proxy)
                except requests.exceptions.SSLError as ssl_error:
                    self.proxy = next(config.r_proxies)
                    return self.get_vin_code(vin_code)
            else:
                r = self.session.post(self.dc_check_url, data=params, verify=False)
            try:
                res = r.json()

                if res.get('code', 200) in ['201', 201]:
                    time.sleep(1)
                    self.captcha = None
                    return self.get_vin_code(vin_code)
                res_status = res.get('RequestResult', {'status': 'ERROR'}).get('status', 'ERROR')
                if res_status in ['NO_DATA', 'ERROR']:
                    result = []
                    config.logger.info(f'[{self.captcha_iter} - {c_code}] {vin_code} - NO DIAGNOSTIC CARDS')
                    return result
                result = res.get('RequestResult').get('diagnosticCards')

                for r in result:
                    r['vin'] = vin_code
                config.logger.info(f'[{self.captcha_iter} - {c_code}] {vin_code} - {str(result[0]["dcNumber"])}')

            except Exception as e:
                config.logger.info(f'[{self.captcha_iter} - {c_code}] {vin_code} - NO DIAGNOSTIC CARDS')
                try:
                    if r.status_code('code', 200) in ['201', 201]:
                        print(r.content)
                    else:
                        with open(f'responses/{vin_code}.txt', 'w') as f:
                            ex = ''
                            for arg in e.args:
                                ex += arg + '\n'
                            f.write(str(r.status_code) + '\n' + r.text + '\n\n' + str(ex))
                    result = None
                except Exception as e:
                    config.logger.error(f'{vin_code} - Failed')
                    result = None
            return result


def process_thread(vins: list):
    try:
        prx = next(config.r_proxies)
    except:
        config.r_proxies = cycle(config.proxies)
        prx = next(config.r_proxies)
    v = VinDcCheck(prx)
    for vin in vins:
        c = 0
        while c <= config.tries:
            try:
                force = False
                if v.proxy:
                    config.logger.debug(f'Trying proxy {v.proxy["http"]}')
                if isinstance(vin, str) or not (vin.get('createdAt', None)):
                    force = True
                    vin = {'vin': vin}
                try:
                    asyncio.run(sql_adapter.touch_vin_at(vin['vin']))
                except Exception as e:
                    config.logger.error(e)
                vin = v.get_vin_code(vin['vin'])
                try:
                    asyncio.run(sql_adapter.create_dc_for_vin(vin[0], force))
                except:
                    pass
                break
            except StopIteration:
                if v.proxy:
                    config.r_proxies = cycle(config.proxies)
                    v.proxy = next(config.r_proxies)
                c += 1
            except Exception as e:
                config.logger.error(e)
                if v.proxy:
                    v.proxy = next(config.r_proxies)
                c += 1


def mulithreaded_processor(vins: list):
    start_dt = datetime.datetime.now()
    length_of_vins_list = len(vins)
    if length_of_vins_list > 0:
        # self.results = []
        array_of_threads = []
        threads_count = config.threads
        vins_in_thread, vins_in_last_thread = divmod(length_of_vins_list, threads_count)
        # vins_in_thread += 1

        vins_lists = []
        if vins_in_thread > 0:
            for i in range(0, threads_count + 1):
                config.logger.info(f'{i + 1} of {config.threads}')
                slice_low = vins_in_thread * i
                slice_high = slice_low + vins_in_thread
                if slice_high > len(vins):
                    slice_high = slice_low + vins_in_last_thread
                vins_lists.append(vins[slice_low:slice_high])

            for i in range(0, threads_count + 1):
                array_of_threads.append(
                    threading.Thread(target=process_thread, args=(vins_lists[i],), daemon=True))
            for thread in array_of_threads:
                thread.start()
                config.logger.info(
                    f'Started thread #{array_of_threads.index(thread) + 1} of {len(array_of_threads)} with {len(vins_lists[array_of_threads.index(thread)])} vins')

            for thread in array_of_threads:
                thread.join()
                config.logger.info(
                    f'Joined thread #{array_of_threads.index(thread) + 1} of {len(array_of_threads)} with {len(vins_lists[array_of_threads.index(thread)])} vins')
        else:
            config.logger.info(f'Started parsing of {length_of_vins_list} vin in 1 thread...')
            t1 = threading.Thread(target=process_thread, args=(vins,), daemon=True)
            t1.start()
            t1.join()
        stop_dt = datetime.datetime.now()
        dt_diff = (stop_dt - start_dt).total_seconds()
        if dt_diff > 60:
            dt_m, dt_s = divmod(dt_diff, 60)
            dt_str = f'{length_of_vins_list} records: {int(dt_m)} minutes {round(dt_s)} seconds passed'
        elif dt_diff > 3600:
            dt_m, dt_s = divmod(dt_diff, 60)
            dt_h, dt_m = divmod(dt_m, 60)
            dt_str = f'{length_of_vins_list} records: {int(dt_h)} hours {int(dt_m)} minutes {round(dt_s)} seconds passed'
        else:
            dt_str = f'{length_of_vins_list} records: {round(dt_diff)} seconds passed'
        config.logger.info(dt_str)
    else:
        config.logger.info(f'VINs list is empty. All VINs are up to date.')


if __name__ == '__main__':
    pass
