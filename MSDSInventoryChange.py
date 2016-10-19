import pandas as pd
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from datetime import datetime
import re

# read data from Excel form
data = pd.read_excel(r'C:\Users\RHun\PycharmProjects\MSDS\MSDSInventoryChangeForm.xlsm', sheetname='Form',
                     skiprows=18, parse_cols='B:G',
                     names=['Add or Remove', 'MSDS Number', 'LL Item Number', 'Product Name', 'Manufacturer', 'Process'])

site_info = pd.read_excel(r'C:\Users\RHun\PycharmProjects\MSDS\MSDSInventoryChangeForm.xlsm', sheetname='Form',
                         parse_cols='D', header=None, names=['Site Info'])
data = data[:15].dropna(how='all')
site_info = site_info[:3]
# print(data)
# print(site_info['Site Info'][1])

# Parameters to be called
url = 'http://www.admin.lifelabs.msdss.com/'

# Sign into SafeTec
def Add():
    browser = webdriver.Firefox()
    browser.get(url)
    browser.find_element_by_class_name("text").click()


    Login_Name = browser.find_element_by_id("placeBody_txtLoginName")
    Password = browser.find_element_by_id("placeBody_txtPassword")
    Login_Name.send_keys('rhun')
    Password.send_keys('12345')
    browser.find_element_by_class_name("text").click()
    browser.find_element_by_link_text('SDS Search').click()

    for i in range(len(data['MSDS Number'])):
        browser.find_element_by_id("placeBody_dynField3_txtTextBox").clear()
        browser.find_element_by_id("placeBody_dynField3_txtTextBox").send_keys(data['MSDS Number'][i])
        browser.find_element_by_link_text("Search").click()
        wait = WebDriverWait(browser, 10)
        try:
            if data['Add or Remove'][i] == 'A':
                browser.find_element_by_css_selector("input[alt='Add SDS Location']").click()
                select1 = Select(browser.find_element_by_css_selector("select[id*='dropSubLocations_dropFacility']"))
                select1.select_by_visible_text(site_info['Site Info'][0])

                select2 = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR,
                    "select[id*='dropSubLocations_dropSubLocation1']")))
                Select(select2).select_by_visible_text(site_info['Site Info'][1])

                select3 = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR,
                    "select[id*='dropSubLocations_dropSubLocation2']")))
                Select(select3).select_by_visible_text(site_info['Site Info'][2])
                browser.find_element_by_link_text("Save").click()
            elif data['Add or Remove'][i] == 'R':
                browser.find_element_by_css_selector("input[alt='Archive SDS at Location']").click()
                select1 = Select(browser.find_element_by_css_selector("select[id*='dropSubLocations_dropFacility']"))
                select1.select_by_visible_text(site_info['Site Info'][0])

                select2 = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR,
                    "select[id*='dropSubLocations_dropSubLocation1']")))
                Select(select2).select_by_visible_text(site_info['Site Info'][1])

                select3 = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR,
                    "select[id*='dropSubLocations_dropSubLocation2']")))
                Select(select3).select_by_visible_text(site_info['Site Info'][2])
                browser.find_element_by_link_text("Save").click()
        except Exception as e:
            print(str(e), end=' ')
            print(site_info['Site Info'][2], end=' ')
            print(data['MSDS Number'][i])
            continue

if __name__=='__main__':
    Add()
