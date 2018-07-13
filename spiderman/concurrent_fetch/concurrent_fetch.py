# coding:utf-8

import os
import multiprocessing
import concurrent.futures
import threading
import time
import datetime

from webhandler import fetchhtml


class ConcurrencyFetch(object):

    def __init__(self):
        self.pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
        self.thread_pool = None
        self.task = None
        self.task_param_l = []
        self.fetch_html_obj = fetchhtml.FetchHtml(url="http://bj.58.com/chuzu/")

    def init_task(self, ):
        self.task = self.warp_task
        self.task_param_l = self.fetch_html_obj.get_total_pages_count()[:1]
        #print(self.task_param_l)

    def warp_task(self, page_url):
        self.thread_pool = ThreadPool()
        self.thread_pool.task_param_l = self.fetch_html_obj.get_house_link(page_url)
        if self.thread_pool.task_param_l:
            self.thread_pool.task_param_l = self.thread_pool.task_param_l[:2]
            self.thread_pool.task = self.fetch_html_obj.get_house_info
            self.thread_pool.run_task()
        else:
            print("Failed to get house page")

    def clawer_web(self):
        self.init_task()
        result = self.pool.map(self.task, self.task_param_l)
        self.close_pool()

    def close_pool(self):
        self.pool.close()
        self.pool.join()

    def __getstate__(self):
        self_dict = self.__dict__.copy()
        del self_dict['pool']
        return self_dict

    def __setstate__(self, state):
        self.__dict__.update(state)


class ThreadPool(object):
    def __init__(self, thread_num=2):
        self.executors = concurrent.futures.ThreadPoolExecutor(max_workers=thread_num)
        self.task = None
        self.task_param_l = []
        self.fs_l = []
        self.thread_result_l = []

    '''
    def task(self, i):
        time.sleep(3)
        print(threading.current_thread(), i)
        return i
    '''

    def run_task(self):
        self.fs_l = {self.executors.submit(self.task, param) for param in self.task_param_l}
        try:
            for fs in concurrent.futures.as_completed(self.fs_l):
                try:
                    r = fs.result()
                    self.thread_result_l.append(r)
                except Exception as e:
                    print("*" * 10, str(e))
                    if fs.running():
                        fs.cancel()
        except Exception as e:
            print(e)



if __name__ == '__main__':
    cf = ConcurrencyFetch()
    cf.clawer_web()

    #ThreadPool([1,2,3]).run_task()