import asyncio
import datetime
import random
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
    # def __init__(self):
    #     self.results = []
    #     self.captch_req_url = 'https://check.gibdd.ru/captcha'
    #     self.dc_check_url = 'https://xn--b1afk4ade.xn--90adear.xn--p1ai/proxy/check/auto/diagnostic'
    #     self.session = requests.Session()
    #     # self.api_key = sql_adapter.get_setting('captcha_api_key')
    #     self.api_key = 'e9e783d3e52abd6101fc807ab1109400'
    #     self.solver = Anticaptcha(token=self.api_key)
    def __init__(self, proxy=None):
        self.results = []
        self.captch_req_url = 'https://check.gibdd.ru/captcha'
        self.dc_check_url = 'https://xn--b1afk4ade.xn--90adear.xn--p1ai/proxy/check/auto/diagnostic'
        self.session = requests.Session()
        # self.api_key = sql_adapter.get_setting('captcha_api_key')
        self.api_key = 'e9e783d3e52abd6101fc807ab1109400'
        self.solver = Anticaptcha(token=self.api_key)
        self.proxy = proxy
        self.captcha = None
        if proxy is not None:
            print(proxy)

    # def get_captcha(self, proxy=None):
    #     if proxy:
    #         try:
    #             r = self.session.get(self.captch_req_url, verify=False, proxies=proxy)
    #         except requests.exceptions.SSLError as ssl_error:
    #             proxy = next(config.r_proxies)
    #             return self.get_captcha(proxy)
    #     else:
    #         r = self.session.get(self.captch_req_url, verify=False)
    #     if r:
    #         result = r.json()
    #         # config.logger.info(result.get('token'))
    #         res = self.resolve_captcha(result.get('base64jpg'))
    #         # config.logger.info(js)
    #         result.update({'code': res})
    #     else:
    #         result = None
    #     # config.logger.info(json.dumps(result, ensure_ascii=False, indent=2))
    #     return result
    #
    # def resolve_captcha(self, captcha_img_b64):
    #     # self.solver.normal()
    #     return self.solver.resolve_captcha(captcha_img_b64)
    #
    # def get_vin_code(self, vin_code, proxy=None):
    #     config.logger.debug(f'{vin_code} - Start')
    #     asyncio.run(sql_adapter.touch_vin_at(vin_code))
    #     captcha = self.get_captcha(proxy)
    #     if captcha:
    #         c_token = captcha.get('token')
    #         try:
    #             c_code = int(captcha.get('code'))
    #         except:
    #             c_code = 0
    #         params = {
    #             'vin': vin_code,
    #             'checkType': 'diagnostic',
    #             'captchaWord': c_code,
    #             'captchaToken': c_token
    #         }
    #         self.session.headers.update({'Content-Type': 'application/x-www-form-urlencoded'})
    #         if proxy:
    #             try:
    #                 r = self.session.post(self.dc_check_url, data=params, verify=False, proxies=proxy)
    #             except requests.exceptions.SSLError as ssl_error:
    #                 proxy = next(config.r_proxies)
    #                 config.logger.info(f'{proxy["http"].split("@")[1]} - SSL Error: {ssl_error}, change proxy')
    #                 return self.get_vin_code(vin_code, proxy)
    #         else:
    #             r = self.session.post(self.dc_check_url, data=params, verify=False)
    #         try:
    #             # config.logger.info(r.text)
    #             res = r.json()
    #
    #             if res.get('code', 200) in ['201', 201]:
    #                 time.sleep(1)
    #                 config.logger.debug(f'{vin_code} Captcha error, retrying...')
    #                 return self.get_vin_code(vin_code, proxy)
    #
    #             result = res.get('RequestResult').get('diagnosticCards')
    #             for r in result:
    #                 r['vin'] = vin_code
    #             config.logger.info(f'{vin_code} - {str(result[0]["dcNumber"])}')
    #
    #         except Exception as e:
    #             if res.get('code', 200) in ['201', 201]:
    #                 pass
    #             else:
    #                 config.logger.debug(e)
    #                 # if RequestResult.status in ['NO_DATA','ERROR']: need catcher
    #                 with open(f'responses/{vin_code}.txt', 'w') as f:
    #                     ex = ''
    #                     for arg in e.args:
    #                         ex += arg + '\n'
    #                     f.write(str(r.status_code) + '\n' + r.text + '\n\n' + str(ex))
    #             result = None
    #             config.logger.debug(f'{vin_code} - Failed')
    #         return result
    #
    # def get_vin_codes(self, vins: list, use_proxy=False):
    #     for vin in vins:
    #         # self.get_vin_code(vin, proxy)
    #         c = 0
    #         prx = None
    #         while c <= config.tries:
    #             try:
    #                 force = False
    #                 if use_proxy:
    #                     prx = next(config.r_proxies)
    #                     config.logger.debug(f'Trying proxy {prx["http"]}')
    #                 if not (vin.get('createdAt', None)):
    #                     force = True
    #                 vin = self.get_vin_code(vin['vin'], prx)
    #                 asyncio.run(sql_adapter.create_dc_for_vin(vin[0], force))
    #                 # sql_adapter.create_dc_for_vin(vin)
    #                 self.results.append(vin[0])
    #                 break
    #             except StopIteration:
    #                 if use_proxy:
    #                     config.r_proxies = cycle(config.proxies)
    #                     prx = next(config.r_proxies)
    #                 c += 1
    #             except Exception as e:
    #                 config.logger.info(e)
    #                 if use_proxy:
    #                     prx = next(config.r_proxies)
    #                 c += 1
    #
    # def multithreading_get_vins(self, vins, use_proxy=True):
    #     start_dt = datetime.datetime.now()
    #     arr_length = len(vins)
    #     self.results = []
    #     t_s = []
    #     tc = config.threads
    #     l_count, l_mod = divmod(len(vins), tc)
    #     l_count += 1
    #     # l_mod = len(vins) % tc
    #     # if l_mod != 0:
    #     #
    #     #     l_mod = len(vins) % config.threads
    #     #     if l_mod == 0:
    #     #         tc = config.threads
    #     #         l_count = len(vins) // tc
    #     #
    #     #     else:
    #     #         tc = config.threads - 1
    #     #         l_count = len(vins) // tc
    #
    #     l_c = []
    #     for i in range(0, config.threads):
    #         config.logger.info(f'{i + 1} of {config.threads}')
    #         min = l_count * i
    #         max = min + l_count
    #         if max > len(vins):
    #             max = min + l_mod
    #         l_c.append(vins[min:max])
    #
    #     for i in range(0, config.threads):
    #         t_s.append(
    #             threading.Thread(target=self.get_vin_codes, args=(l_c[i], use_proxy), daemon=True))
    #     for t in t_s:
    #         t.start()
    #         config.logger.info(f'Started thread #{t_s.index(t) + 1} of {len(t_s)} with {len(l_c[t_s.index(t)])} vins')
    #
    #     for t in t_s:
    #         t.join()
    #         config.logger.info(f'Joined thread #{t_s.index(t) + 1} of {len(t_s)} with {len(l_c[t_s.index(t)])} vins')
    #     stop_dt = datetime.datetime.now()
    #     dt_diff = (stop_dt - start_dt).total_seconds()
    #     if dt_diff > 60:
    #         dt_m, dt_s = divmod(dt_diff, 60)
    #         dt_str = f'{arr_length} records: {int(dt_m)} minutes {round(dt_s)} seconds passed'
    #     elif dt_diff > 3600:
    #         dt_m, dt_s = divmod(dt_diff, 60)
    #         dt_h, dt_m = divmod(dt_m, 60)
    #         dt_str = f'{arr_length} records: {int(dt_h)} hours {int(dt_m)} minutes {round(dt_s)} seconds passed'
    #     else:
    #         dt_str = f'{arr_length} records: {round(dt_diff)} seconds passed'
    #     config.logger.info(dt_str)

    def get_captcha(self):
        print('Getting captcha data')
        if self.proxy:
            try:
                r = self.session.get(self.captch_req_url, verify=False, proxies=self.proxy)
            except:
                self.proxy = next(config.r_proxies)
                return self.get_captcha()
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
        # with open('session.headers', 'w', encoding='utf-8') as f:
        #     f.write(json.dumps(self.session.headers.__dict__, ensure_ascii=False, indent=2))
        #     f.write(json.dumps(r.headers.__dict__, ensure_ascii=False, indent=2))
        # with open('session.cookies', 'wb') as f:
        #     try:
        #         print(self.session.cookies.__dict__)
        #     except:
        #         pass
        #     pickle.dump(self.session.cookies, f)
        return result

    def resolve_captcha(self, captcha_img_b64):
        return self.solver.resolve_captcha(captcha_img_b64)

    def get_vin_code(self, vin_code):
        if not self.captcha:
            self.captcha = self.get_captcha()
        if self.captcha:
            c_token = self.captcha.get('token')
            try:
                c_code = int(self.captcha.get('code'))
            except:
                c_code = 0
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
                    print(f'{self.proxy["http"].split("@")[1]} - SSL Error: {ssl_error}, change proxy')
                    return self.get_vin_code(vin_code)
            else:
                r = self.session.post(self.dc_check_url, data=params, verify=False)
            try:
                res = r.json()

                if res.get('code', 200) in ['201', 201]:
                    time.sleep(1)
                    print(f'{vin_code} Captcha error, retrying...')
                    self.captcha = None
                    return self.get_vin_code(vin_code)

                result = res.get('RequestResult').get('diagnosticCards')
                for r in result:
                    r['vin'] = vin_code
                print(f'[{c_code}] {vin_code} - {str(result[0]["dcNumber"])}')

            except Exception as e:
                print(f'[{c_code}] {vin_code} - None')
                try:
                    if res.get('code', 200) in ['201', 201]:
                        pass
                    else:
                        print(e)
                        # if RequestResult.status in ['NO_DATA','ERROR']: need catcher
                        with open(f'responses/{vin_code}.txt', 'w') as f:
                            ex = ''
                            for arg in e.args:
                                ex += arg + '\n'
                            f.write(str(r.status_code) + '\n' + r.text + '\n\n' + str(ex))
                    result = None
                    print(f'{vin_code} - Failed')
                except Exception as e:
                    config.logger.error(e)
                    result = None
            return result


def process_thread(vins: list):
    try:
        prx = next(config.r_proxies)
    except:
        config.r_proxies = cycle(config.proxies)
        prx = next(config.r_proxies)
    v = VinDcCheck(prx)
    # v.get_vin_code(vins[0])
    # for vin in vins:
    #     v.get_vin_code(vin)
    #     t = 0.1 + (random.randint(0, 100) / 200)
    #     time.sleep(round(t, 2))
    for vin in vins:
        # self.get_vin_code(vin, proxy)
        c = 0
        prx = None
        while c <= config.tries:
            try:
                force = False
                if v.proxy:
                    v.proxy = next(config.r_proxies)
                    config.logger.debug(f'Trying proxy {v.proxy["http"]}')
                if not (vin.get('createdAt', None)):
                    force = True
                # vin = v.get_vin_code(vin['vin'])
                vin = v.get_vin_code(vin['vin'])
                t = 0.1 + (random.randint(0, 100) / 200)
                time.sleep(round(t, 2))
                asyncio.run(sql_adapter.create_dc_for_vin(vin[0], force))
                # sql_adapter.create_dc_for_vin(vin)
                # self.results.append(vin[0])
                break
            except StopIteration:
                if v.proxy:
                    config.r_proxies = cycle(config.proxies)
                    v.proxy = next(config.r_proxies)
                c += 1
            except Exception as e:
                config.logger.info(e)
                if v.proxy:
                    v.proxy = next(config.r_proxies)
                c += 1


def mulithreaded_processor(vins: list):
    start_dt = datetime.datetime.now()
    length_of_vins_list = len(vins)
    # self.results = []
    array_of_threads = []
    threads_count = config.threads
    vins_in_thread, vins_in_last_thread = divmod(length_of_vins_list, threads_count)
    vins_in_thread += 1

    vins_lists = []
    for i in range(0, threads_count):
        config.logger.info(f'{i + 1} of {config.threads}')
        slice_low = vins_in_thread * i
        slice_high = slice_low + vins_in_thread
        if slice_high > len(vins):
            slice_high = slice_low + vins_in_last_thread
        vins_lists.append(vins[slice_low:slice_high])

    for i in range(0, threads_count):
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

if __name__ == '__main__':
    pass
