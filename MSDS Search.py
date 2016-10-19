import pandas as pd
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from datetime import datetime
import re

# read list of CAS Numbers to be searched
data = pd.read_csv("Toxic Substances List.csv", names=["CAS Number"])
data.dropna()
CAS = data["CAS Number"]

# read list of MSDS Numbers to be searched
SDS_data = pd.read_csv("SDS numbers.csv", header=None)
SDS_data.columns = ["SDS-Numbers"]
SDS_numbers = SDS_data["SDS-Numbers"]

# Parameters to be called
url = 'http://www.lifelabs.msdss.com/Login.aspx?ReturnUrl=%2fMainMenu.aspx%3ffm%3d0%26tb%3d0'

# Sign into SafeTec

browser = webdriver.Firefox()
browser.get(url)
browser.find_element_by_class_name("text").click()

def MSDS_SearchByCAS():
# Conduct MSDS Searches on SafeTec
    for i in range(len(CAS)):

        Ingredient_CAS_Number = browser.find_element_by_id("placeBody_dynField48_txtTextBox")
        Ingredient_CAS_Number.send_keys(CAS[i])
        browser.find_element_by_id("placeBody_linkSearchBottom").click()

        list_links = browser.find_elements_by_css_selector("a[href*='MSDSDetail']")
        collect = []

        for j in range(0, len(list_links)):
            list_links = browser.find_elements_by_css_selector("a[href*='MSDSDetail']")
            list_links1 = browser.find_elements_by_css_selector("a[href*='MSDSDetail']")[j]
            list_links1.click()

            # Extract Ingredients and composition of each product
            browser.implicitly_wait(1)
            html = browser.page_source
            soup = BeautifulSoup(html)
            table = soup.find('div', {'id': 'placeBody_dynField77_divScroll'})
            rows = table.findAll('tr')
            Ingredients = []
            for row in rows:
                cols = row.find_all('td')
                cols = [ele.text.strip() for ele in cols]
                Ingredients.append([ele for ele in cols if ele])
            Ingredients = pd.DataFrame(Ingredients)

            if Ingredients.shape[1] < 8:
                Ingredients['dummy'] = np.nan

            # Extract the Basic Information of each product
            Product_Name = browser.find_element_by_id("placeBody_dynField1_txtTextBox")
            Manufacturer = browser.find_element_by_id("placeBody_dynField2_txtTextBox")
            MSDS_Number = browser.find_element_by_id("placeBody_dynField6_txtTextBox")
            LL_Number = browser.find_element_by_id("placeBody_dynField10_txtTextBox")
            basic_info = [[MSDS_Number.text, Product_Name.text, Manufacturer.text, LL_Number.text]]
            basic_info = pd.DataFrame(basic_info)

            # Determine if Ingredients goes on to the next page and
            # how many pages listing composition chemicals each product has
            if len(browser.find_elements_by_id("placeBody_dynField77_gridView_pager_lnkNext")) > 0:
                select = browser.find_element_by_css_selector("select[id*='dynField77_gridView_pager_dropPage']")
                options = [x.text for x in select.find_elements_by_tag_name("option")]
                options2 = list(map(int, options))

                # Navigate to other pages listing composition chemicals
                Ingredients2 = []
                for a in range(max(options2)-1):
                    wait = WebDriverWait(browser, 10)
                    system = wait.until(EC.element_to_be_clickable((By.ID, "placeBody_dynField77_gridView_pager_lnkNext")))
                    system.click()
                    browser.implicitly_wait(2)
                    html2 = browser.page_source
                    soup2 = BeautifulSoup(html2)
                    table2 = soup2.find('div', {'id': 'placeBody_dynField77_divScroll'})
                    rows2 = table2.findAll('tr')

                    for row2 in rows2:
                        cols2 = row2.find_all('td')
                        cols2 = [ele2.text.strip() for ele2 in cols2]
                        Ingredients2.append([ele2 for ele2 in cols2 if ele2])
                Ingredients2 = pd.DataFrame(Ingredients2).ix[1:]

                if Ingredients2.shape[1] < 8:
                    Ingredients2['dummy'] = np.nan
                Ingredients2 = pd.concat([Ingredients, Ingredients2])
                Ingredients2 = Ingredients2.reset_index(drop=True)

                for s in range(len(options2) - 1):
                    browser.back()

            else:
                Ingredients2 = Ingredients

            # Merge Basic Information table with Composition table
            rep_basic = pd.concat([basic_info] * len(Ingredients2.index))
            rep_basic = rep_basic.reset_index(drop=True)
            result1 = pd.concat([Ingredients2, rep_basic], axis=1)
            if result1.shape[1] == 12:
                result1.columns = ["Chemical Name", "CAS Number", "% Context", "Min %", "Max %", "Avg %", "%Range",
                                "SARA", "MSDS Number", "Product Name", "Manufacturer", "LifeLabs Number"]
            print(result1.shape)
            result1.ix[1:].to_csv("MSDS Results "+"{:%B %d, %Y}".format(datetime.now())+".csv", mode='a',
                                  header=True, index=False)

            browser.back()

        # Determine if search results go on to next page
        if len(browser.find_elements_by_link_text("Next")) > 0:

            htmls = browser.page_source
            soup = BeautifulSoup(htmls)
            page_box = soup.find('div', {'class': 'pager no-change'})
            pages = page_box.find('span', text=re.compile(r'of'))
            pages = pages.text.replace("of", "")

            # Pull up MSDS search results for each page
            for k in range(int(pages)-1):

                click = browser.find_element_by_link_text("Next")
                click.click()

                list_links2 = browser.find_elements_by_css_selector("a[href*='MSDSDetail']")

                for j in range(0, len(list_links2)):
                    list_links2 = browser.find_elements_by_css_selector("a[href*='MSDSDetail']")
                    list_links3 = browser.find_elements_by_css_selector("a[href*='MSDSDetail']")[j]
                    list_links3.click()

                    # Extract Ingredients and composition of each product
                    browser.implicitly_wait(1)
                    html = browser.page_source
                    soup = BeautifulSoup(html)
                    table = soup.find('div', {'id': 'placeBody_dynField77_divScroll'})
                    rows = table.findAll('tr')
                    Ingredients = []
                    for row in rows:
                        cols = row.find_all('td')
                        cols = [ele.text.strip() for ele in cols]
                        Ingredients.append([ele for ele in cols if ele])
                    Ingredients = pd.DataFrame(Ingredients)

                    if Ingredients.shape[1] < 8:
                        Ingredients['dummy'] = np.nan

                    # Extract the Basic Information of each product
                    Product_Name = browser.find_element_by_id("placeBody_dynField1_txtTextBox")
                    Manufacturer = browser.find_element_by_id("placeBody_dynField2_txtTextBox")
                    MSDS_Number = browser.find_element_by_id("placeBody_dynField6_txtTextBox")
                    LL_Number = browser.find_element_by_id("placeBody_dynField10_txtTextBox")
                    basic_info = [[MSDS_Number.text, Product_Name.text, Manufacturer.text, LL_Number.text]]
                    basic_info = pd.DataFrame(basic_info)

                    # Determine if Ingredients goes on to the next page and
                    # how many pages listing composition chemicals each product has
                    if len(browser.find_elements_by_id("placeBody_dynField77_gridView_pager_lnkNext")) > 0:
                        select = browser.find_element_by_css_selector("select[id*='dynField77_gridView_pager_dropPage']")
                        options = [x.text for x in select.find_elements_by_tag_name("option")]
                        options2 = list(map(int, options))

                        # Navigate to other pages listing composition chemicals
                        Ingredients2 = []
                        for b in range(max(options2)-1):
                            wait = WebDriverWait(browser, 10)
                            system = wait.until(EC.element_to_be_clickable((By.ID, "placeBody_dynField77_gridView_pager_lnkNext")))
                            system.click()
                            browser.implicitly_wait(2)
                            html2 = browser.page_source
                            soup2 = BeautifulSoup(html2)
                            table2 = soup2.find('div', {'id': 'placeBody_dynField77_divScroll'})
                            rows2 = table2.findAll('tr')

                            for row2 in rows2:
                                cols2 = row2.find_all('td')
                                cols2 = [ele2.text.strip() for ele2 in cols2]
                                Ingredients2.append([ele2 for ele2 in cols2 if ele2])
                        Ingredients2 = pd.DataFrame(Ingredients2)

                        if Ingredients2.shape[1] < 8:
                            Ingredients2['dummy'] = np.nan
                        Ingredients2 = pd.concat([Ingredients, Ingredients2])
                        Ingredients2 = Ingredients2.reset_index(drop=True)

                        for s in range(len(options2) - 1):
                            browser.back()

                    else:
                        Ingredients2 = Ingredients

                    rep_basic = pd.concat([basic_info] * len(Ingredients2.index))
                    rep_basic = rep_basic.reset_index(drop=True)
                    result1 = pd.concat([Ingredients2, rep_basic], axis=1)

                    if result1.shape[1] == 12:
                        result1.columns = ["Chemical Name", "CAS Number", "% Context", "Min %", "Max %", "Avg %", "%Range",
                                       "SARA", "MSDS Number", "Product Name", "Manufacturer", "LifeLabs Number"]
                    print(result1.shape)
                    result1.ix[1:].to_csv("MSDS Results "+"{:%B %d, %Y}".format(datetime.now())+".csv", mode='a',
                                          header=True, index=False)

                    browser.back()

        browser.get(url)


def MSDS_SearchBySDSNumber():
# Conduct MSDS Searches on SafeTec
    for i in range(len(SDS_numbers)):

        Number_Search = browser.find_element_by_id("placeBody_dynField3_txtTextBox")
        Number_Search.send_keys(SDS_numbers[i])
        browser.find_element_by_id("placeBody_linkSearchBottom").click()

        list_links = browser.find_elements_by_css_selector("a[href*='MSDSDetail']")
        collect = []

        for j in range(0, len(list_links)):
            list_links = browser.find_elements_by_css_selector("a[href*='MSDSDetail']")
            list_links1 = browser.find_elements_by_css_selector("a[href*='MSDSDetail']")[j]
            list_links1.click()

            # Extract Ingredients and composition of each product
            browser.implicitly_wait(1)
            html = browser.page_source
            soup = BeautifulSoup(html)
            table = soup.find('div', {'id': 'placeBody_dynField77_divScroll'})
            rows = table.findAll('tr')
            Ingredients = []
            for row in rows:
                cols = row.find_all('td')
                cols = [ele.text.strip() for ele in cols]
                Ingredients.append([ele for ele in cols if ele])
            Ingredients = pd.DataFrame(Ingredients)

            if Ingredients.shape[1] < 8:
                Ingredients['dummy'] = np.nan

            # Extract the Basic Information of each product
            Product_Name = browser.find_element_by_id("placeBody_dynField1_txtTextBox")
            Manufacturer = browser.find_element_by_id("placeBody_dynField2_txtTextBox")
            MSDS_Number = browser.find_element_by_id("placeBody_dynField6_txtTextBox")
            LL_Number = browser.find_element_by_id("placeBody_dynField10_txtTextBox")
            basic_info = [[MSDS_Number.text, Product_Name.text, Manufacturer.text, LL_Number.text]]
            basic_info = pd.DataFrame(basic_info)

            # Determine if Ingredients goes on to the next page and
            # how many pages listing composition chemicals each product has
            if len(browser.find_elements_by_id("placeBody_dynField77_gridView_pager_lnkNext")) > 0:
                select = browser.find_element_by_css_selector("select[id*='dynField77_gridView_pager_dropPage']")
                options = [x.text for x in select.find_elements_by_tag_name("option")]
                options2 = list(map(int, options))

                # Navigate to other pages listing composition chemicals
                Ingredients2 = []
                for a in range(max(options2)-1):
                    wait = WebDriverWait(browser, 10)
                    system = wait.until(EC.element_to_be_clickable((By.ID, "placeBody_dynField77_gridView_pager_lnkNext")))
                    system.click()
                    browser.implicitly_wait(2)
                    html2 = browser.page_source
                    soup2 = BeautifulSoup(html2)
                    table2 = soup2.find('div', {'id': 'placeBody_dynField77_divScroll'})
                    rows2 = table2.findAll('tr')

                    for row2 in rows2:
                        cols2 = row2.find_all('td')
                        cols2 = [ele2.text.strip() for ele2 in cols2]
                        Ingredients2.append([ele2 for ele2 in cols2 if ele2])
                Ingredients2 = pd.DataFrame(Ingredients2).ix[1:]

                if Ingredients2.shape[1] < 8:
                    Ingredients2['dummy'] = np.nan
                Ingredients2 = pd.concat([Ingredients, Ingredients2])
                Ingredients2 = Ingredients2.reset_index(drop=True)

                for s in range(len(options2) - 1):
                    browser.back()

            else:
                Ingredients2 = Ingredients

            # Merge Basic Information table with Composition table
            rep_basic = pd.concat([basic_info] * len(Ingredients2.index))
            rep_basic = rep_basic.reset_index(drop=True)
            result1 = pd.concat([Ingredients2, rep_basic], axis=1)
            if result1.shape[1] == 12:
                result1.columns = ["Chemical Name", "CAS Number", "% Context", "Min %", "Max %", "Avg %", "%Range",
                                "SARA", "MSDS Number", "Product Name", "Manufacturer", "LifeLabs Number"]
            print(result1.shape)
            result1.ix[1:].to_csv("MSDS Results "+"{:%B %d, %Y}".format(datetime.now())+".csv", mode='a',
                                  header=True, index=False)

            browser.back()

        # Determine if search results go on to next page
        if len(browser.find_elements_by_link_text("Next")) > 0:

            htmls = browser.page_source
            soup = BeautifulSoup(htmls)
            page_box = soup.find('div', {'class': 'pager no-change'})
            pages = page_box.find('span', text=re.compile(r'of'))
            pages = pages.text.replace("of", "")

            # Pull up MSDS search results for each page
            for k in range(int(pages)-1):

                click = browser.find_element_by_link_text("Next")
                click.click()

                list_links2 = browser.find_elements_by_css_selector("a[href*='MSDSDetail']")

                for j in range(0, len(list_links2)):
                    list_links2 = browser.find_elements_by_css_selector("a[href*='MSDSDetail']")
                    list_links3 = browser.find_elements_by_css_selector("a[href*='MSDSDetail']")[j]
                    list_links3.click()

                    # Extract Ingredients and composition of each product
                    browser.implicitly_wait(1)
                    html = browser.page_source
                    soup = BeautifulSoup(html)
                    table = soup.find('div', {'id': 'placeBody_dynField77_divScroll'})
                    rows = table.findAll('tr')
                    Ingredients = []
                    for row in rows:
                        cols = row.find_all('td')
                        cols = [ele.text.strip() for ele in cols]
                        Ingredients.append([ele for ele in cols if ele])
                    Ingredients = pd.DataFrame(Ingredients)

                    if Ingredients.shape[1] < 8:
                        Ingredients['dummy'] = np.nan

                    # Extract the Basic Information of each product
                    Product_Name = browser.find_element_by_id("placeBody_dynField1_txtTextBox")
                    Manufacturer = browser.find_element_by_id("placeBody_dynField2_txtTextBox")
                    MSDS_Number = browser.find_element_by_id("placeBody_dynField6_txtTextBox")
                    LL_Number = browser.find_element_by_id("placeBody_dynField10_txtTextBox")
                    basic_info = [[MSDS_Number.text, Product_Name.text, Manufacturer.text, LL_Number.text]]
                    basic_info = pd.DataFrame(basic_info)

                    # Determine if Ingredients goes on to the next page and
                    # how many pages listing composition chemicals each product has
                    if len(browser.find_elements_by_id("placeBody_dynField77_gridView_pager_lnkNext")) > 0:
                        select = browser.find_element_by_css_selector("select[id*='dynField77_gridView_pager_dropPage']")
                        options = [x.text for x in select.find_elements_by_tag_name("option")]
                        options2 = list(map(int, options))

                        # Navigate to other pages listing composition chemicals
                        Ingredients2 = []
                        for b in range(max(options2)-1):
                            wait = WebDriverWait(browser, 10)
                            system = wait.until(EC.element_to_be_clickable((By.ID, "placeBody_dynField77_gridView_pager_lnkNext")))
                            system.click()
                            browser.implicitly_wait(2)
                            html2 = browser.page_source
                            soup2 = BeautifulSoup(html2)
                            table2 = soup2.find('div', {'id': 'placeBody_dynField77_divScroll'})
                            rows2 = table2.findAll('tr')

                            for row2 in rows2:
                                cols2 = row2.find_all('td')
                                cols2 = [ele2.text.strip() for ele2 in cols2]
                                Ingredients2.append([ele2 for ele2 in cols2 if ele2])
                        Ingredients2 = pd.DataFrame(Ingredients2)

                        if Ingredients2.shape[1] < 8:
                            Ingredients2['dummy'] = np.nan
                        Ingredients2 = pd.concat([Ingredients, Ingredients2])
                        Ingredients2 = Ingredients2.reset_index(drop=True)

                        for s in range(len(options2) - 1):
                            browser.back()

                    else:
                        Ingredients2 = Ingredients

                    rep_basic = pd.concat([basic_info] * len(Ingredients2.index))
                    rep_basic = rep_basic.reset_index(drop=True)
                    result1 = pd.concat([Ingredients2, rep_basic], axis=1)

                    if result1.shape[1] == 12:
                        result1.columns = ["Chemical Name", "CAS Number", "% Context", "Min %", "Max %", "Avg %", "%Range",
                                       "SARA", "MSDS Number", "Product Name", "Manufacturer", "LifeLabs Number"]
                    print(result1.shape)
                    result1.ix[1:].to_csv("MSDS Results "+"{:%B %d, %Y}".format(datetime.now())+".csv", mode='a',
                                          header=True, index=False)

                    browser.back()

        browser.get(url)

def get_siteinfo():
    for i in range(1):

        Number_Search = browser.find_element_by_id("placeBody_dynField3_txtTextBox")
        Number_Search.send_keys(SDS_numbers[i])
        browser.find_element_by_id("placeBody_linkSearchBottom").click()

        list_links = browser.find_elements_by_css_selector("a[href*='MSDSDetail']")
        collect = []

        for j in range(0, len(list_links)):
            list_links = browser.find_elements_by_css_selector("a[href*='MSDSDetail']")
            list_links1 = browser.find_elements_by_css_selector("a[href*='MSDSDetail']")[j]
            list_links1.click()

            browser.back()


# MSDS_SearchByCAS()
MSDS_SearchBySDSNumber()
# get_siteinfo()

