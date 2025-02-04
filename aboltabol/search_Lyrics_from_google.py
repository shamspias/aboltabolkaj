"""
Search lyrics form google using seleniam web drive

"""

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

search_text = input("Enter song name you want to saerch: ")
search_text += search_text+" lyrics"

options = webdriver.ChromeOptions()
options.add_argument('headless')
options.add_argument('disable-gpu')

driver = webdriver.Chrome(executable_path='C:\Development\chromedriver.exe', options=options)

driver.get("https://www.google.com/")

search = driver.find_element_by_css_selector('.a4bIc input')
search.send_keys(search_text)
search.send_keys(Keys.ENTER)

lyrics = driver.find_elements_by_css_selector('.i4J0ge .bbVIQb span')

lyrics_list = []

for lyric in lyrics:
    if lyric.text != '':
        lyrics_list.append(lyric.text)

driver.quit()

print(lyrics_list)
