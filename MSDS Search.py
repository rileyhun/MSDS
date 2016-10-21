import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from datetime import datetime


Analyzers = ["Advia 1200", "Digene HPV", "DSRi", "Immulite", "ImmunoCap 250",
                 "Liasion", "Ortho Provue", "PrepStain", "Variant II"]
Analyzers = [("Instrument/Analyzer", x) for x in Analyzers]

def MSDS_SearchByAnalyzer(Analyzers):

    # Parameters to be called
    url = 'http://www.lifelabs.msdss.com/Login.aspx?ReturnUrl=%2fMainMenu.aspx%3ffm%3d0%26tb%3d0'

    # Sign into SafeTec
    browser = webdriver.Firefox()
    browser.get(url)
    browser.find_element_by_class_name("text").click()

# Conduct MSDS Searches on SafeTec
    for i in range(len(Analyzers)):

        wait = WebDriverWait(browser,10)

        # Conduct DataBase search using Analyzer search criteria
        Classification_Type = Select(browser.find_element_by_id("placeBody_dynField60_dropClassType"))
        Classification_Type.select_by_visible_text("Instrument/Analyzer")

        Sub_Class_1 = wait.until(EC.visibility_of_element_located((By.ID, "placeBody_dynField60_dropSubClass1")))
        Select(Sub_Class_1).select_by_visible_text(Analyzers[i][1])

        browser.find_element_by_id("placeBody_linkSearchBottom").click()

        # Find number of pages of records
        html_ = browser.page_source

        if len(browser.find_elements_by_id("ctl00_placeBody_gridView_gridView_ctl01_ctl00_lnkNext")) > 0:
            number_pages = int(html_.split('ctl01_ctl00_lnkGo">Page</a>')[1].split('</span>')[0].strip()[-1])
        else:
            number_pages = 1

        page_number = 1
        for record_page in range(0, number_pages):

            # Find the number of links on each page
            list_links = browser.find_elements_by_css_selector("a[href*='MSDSDetail']")

            # For each page, click into the SDS Links
            for j in range(0, len(list_links)):

                list_links = wait.until(EC.visibility_of_any_elements_located((By.CSS_SELECTOR,
                                                                                       "a[href*='MSDSDetail']")))
                list_links[j].click()

                # Extract Ingredients and composition of each product
                # Extract Basic Information of each product
                Product_Name = wait.until(EC.visibility_of_element_located((By.ID,"placeBody_dynField1_txtTextBox")))
                Product_Name = Product_Name.text
                Manufacturer = wait.until(EC.visibility_of_element_located((By.ID,
                                                                            "placeBody_dynField2_txtTextBox")))
                Manufacturer = Manufacturer.text
                MSDS_Number = wait.until(EC.visibility_of_element_located((By.ID,
                                                                           "placeBody_dynField6_txtTextBox")))
                MSDS_Number = MSDS_Number.text
                LL_Number = wait.until(EC.visibility_of_element_located((By.ID,
                                                                         "placeBody_dynField10_txtTextBox")))
                LL_Number = LL_Number.text
                Analyzer = Analyzers[i][1]

                # Find number of pages listing Ingredients
                html = browser.page_source

                if len(browser.find_elements_by_id("placeBody_dynField77_gridView_pager_lnkNext")) > 0:
                    max_pages = int(html.split('select id="placeBody_dynField77')[1].split('</span>')[0].strip()[-1])
                else:
                    max_pages = 1

                Ingredients = []

                # Extract information from Ingredients Table
                current_page = 1
                for _ in range(0, max_pages):
                    html = browser.page_source
                    soup = BeautifulSoup(html)
                    table = soup.find('div', {'id': 'placeBody_dynField77_divScroll'})
                    rows = table.findAll('tr')

                    Ingredients_section = html.split('<span>Ingredients</span>')[1].split('<span>Attachments')[0]

                    if "No records were found." in Ingredients_section:
                        Ingredients.append(["NA"]*8)
                    else:
                        for row in rows[1:]:
                            cols = row.find_all('td')
                            cols = [ele.text.strip() for ele in cols]
                            Ingredients.append([ele for ele in cols if ele])

                    # Go to next page of Ingredients section if applicable
                    if current_page < max_pages:
                        next_page = wait.until(EC.visibility_of_element_located((By.ID,
                                                                          "placeBody_dynField77_gridView_pager_lnkNext")))
                        next_page.click()

                    current_page+=1

                # Concatenate Basic Information to Ingredients Table
                for item in Ingredients:
                    item.insert(0, Analyzer)
                    item.insert(1, Product_Name)
                    item.insert(2, Manufacturer)
                    item.insert(3, MSDS_Number)
                    item.insert(4, LL_Number)

                # Convert to DataFrame and Export

                data = pd.DataFrame(Ingredients)

                if i == 0 and j==0:
                    data.to_csv("MSDS Inventory Results "+"{:%B %d, %Y}".format(datetime.now())+".csv", mode='a', index=False)
                else:
                    data.to_csv("MSDS Inventory Results "+"{:%B %d, %Y}".format(datetime.now())+".csv", mode='a',
                                header=False, index=False)

                # Return to Links page
                for _ in range(0, max_pages):
                    browser.back()

            # Go to next page of SDS Records
            if page_number < number_pages and len(browser.find_elements_by_id("ctl00_placeBody_gridView_gridView_ctl01_"
                                                                              "ctl00_lnkNext")) > 0:
                browser.find_element_by_id("ctl00_placeBody_gridView_gridView_ctl01_ctl00_lnkNext").click()
            page_number+=1

        browser.get(url)

MSDS_SearchByAnalyzer(Analyzers)
