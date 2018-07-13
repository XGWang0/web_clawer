# coding:utf-8
import requests
import urllib.parse as urlparser
import re
import sys
import os
import pprint
import random
import time

from bs4 import BeautifulSoup


class Login(object):
    def __init__(self, user, password):
        pass


class FetchHtml(object):
    def __init__(self, url):
        self.session = requests.Session()
        self.root_url = url
        self.rent_root_url = url
        self.total_page_for_house = 1
        self.l_total_rent_house_urls = []
        self.text = ""

    def sleep_sometime(self):
        sleep_time = random.randint(8,15)
        time.sleep(sleep_time)

    def get_rent_page(self):
        self.sleep_sometime()
        rsp_obj = self.session.get(self.root_url)
        text = '<a href="/chuzu/" tongji_tag="pc_home_dh_zf">租房</a>'
        bs_inst_for_rent_page = BeautifulSoup(text, 'lxml')
        bs_inst_for_rent_content = bs_inst_for_rent_page.find('a', text='租房')

        if bs_inst_for_rent_content:
            self.rent_root_url = urlparser.urljoin(self.root_url, bs_inst_for_rent_content.attrs['href'])
            print(self.rent_root_url)

    def get_total_pages_count(self):
        self.sleep_sometime()
        rsp_rent_page_obj = self.session.get(self.rent_root_url, timeout=60)
        bs_rent_page_obj = BeautifulSoup(rsp_rent_page_obj.text, 'lxml')
        page_div_obj = bs_rent_page_obj.find('div', class_='pager')
        page_num_l = []
        for page_span_obj in page_div_obj.find_all('a'):
            try:
                page_num = int(page_span_obj.span.text)
                page_num_l.append(page_num)
            except Exception:
                pass
        total_page_for_house = sorted(page_num_l,reverse=True)[0]
        self.l_total_rent_house_urls = [urlparser.urljoin(self.rent_root_url, "pn" + str(i + 2)) \
                                       for i in range(total_page_for_house) if i+2 <= 70]
        return self.l_total_rent_house_urls

    def verification_code_warn(self, bs, url):
        if re.search('请输入验证码', bs.text):
            print("Need to input verification code for browser %s" % url)
            return False

    def get_house_link(self, url="http://bj.58.com/chuzu/pn2"):
        house_link_l = []
        self.sleep_sometime()
        rsp_house_obj = self.session.get(url, timeout=60)
        bs_house_inst = BeautifulSoup(rsp_house_obj.text, "lxml")
        house_links = bs_house_inst.find_all("div", class_="img_list")
        if house_links:
            for house_link in bs_house_inst.find_all("div", class_="img_list"):
                house_link_l.append(urlparser.urljoin('http://',house_link.a['href']))
            return house_link_l
        else:
            self.verification_code_warn(rsp_house_obj, url)
            return []

    def _get_house_desc_tag(self, bs):
        house_desc_tag = bs.find("div", class_=re.compile("house-basic-right", re.I))
        if house_desc_tag:
            return house_desc_tag

    def _get_price_info(self, tag):
        price_and_payway = tag.find("div", class_=re.compile("house-pay-way"))
        house_payway = "No payment way found"
        house_price = 0

        if price_and_payway and price_and_payway.span.b:
            house_price = price_and_payway.span.text
            house_payway_tag = price_and_payway.span.find_next_sibling("span")
            if house_payway_tag:
                house_payway = house_payway_tag.string

        return house_price, house_payway

    def _get_base_house_info(self, tag, span_text, tag_type="text"):
        if tag_type == "text":
            base_tag = tag.find("span", text=re.compile(span_text, re.I))
        elif tag_type == "class":
            base_tag = tag.find("span", class_=re.compile(span_text, re.I))

        if base_tag:
            return " ".join(base_tag.parent.text.split())
        else:
            return "No house base info via %s" % span_text

    def get_house_info(self, url=""):
        self.sleep_sometime()
        rsp_host_obj = self.session.get(url, timeout=60)
        bs_house_info_inst = BeautifulSoup(rsp_host_obj.text, "lxml")
        #bs_house_info_inst = BeautifulSoup(text, "lxml")
        if self.verification_code_warn(bs_house_info_inst, url):
            house_info = {}
        else:
            house_desc_tag = self._get_house_desc_tag(bs_house_info_inst)
            house_price, house_payway = self._get_price_info(house_desc_tag)
            house_lease_type = self._get_base_house_info(house_desc_tag, "租赁方式")

            house_type = self._get_base_house_info(house_desc_tag, "房屋类型")

            house_floor_orien = self._get_base_house_info(house_desc_tag, "朝向楼层")

            house_community = self._get_base_house_info(house_desc_tag, "所在小区")

            house_distinct = self._get_base_house_info(house_desc_tag, "所属区域")

            house_address = self._get_base_house_info(house_desc_tag, "详细地址")

            house_chat_phone = self._get_base_house_info(house_desc_tag, "house-chat-txt", tag_type="class")
            house_info =  {"house_price":house_price,
                            "house_payway":house_payway,
                            "house_lease_type": house_lease_type,
                            "house_type":house_type,
                            "house_floor_orien":house_floor_orien,
                            "house_community":house_community,
                            "house_distinct":house_distinct,
                            "house_address":house_address,
                            "house_chat_phone":house_chat_phone}
            house_info_format = '=' * 50 + "\n" + \
                                '房屋地址'.ljust(15) + ": %s\n" % house_info["house_address"] + \
                                '房屋小区'.ljust(15) + ": %s\n" % house_info["house_community"] + \
                                '所在区域'.ljust(15) + ": %s\n" % house_info["house_distinct"] + \
                                '付款方式'.ljust(15) + ": %s\n" % house_info["house_payway"] + \
                                '租赁方式'.ljust(15) + ": %s\n" % house_info["house_lease_type"] + \
                                '联系电话'.ljust(15) + ": %s\n" % house_info["house_chat_phone"]

            print(house_info_format)
        return house_info

if __name__ == '__main__':
    fh_ins = FetchHtml(url="http://bj.58.com/chuzu/")
    #fh_ins.get_rent_page()
    page_links = fh_ins.get_total_pages_count()
    print(page_links)
    house_links = fh_ins.get_house_link(page_links[0])
    print(house_links)
    fh_ins.get_house_info(house_links[0])
    print("end")
    #fh_ins.get_house_link()

