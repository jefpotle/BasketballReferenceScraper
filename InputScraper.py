from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from urllib.request import urlopen as uReq
from bs4 import BeautifulSoup as soup
import numpy as np
import shutil
import os

# grabbing input from user
players = input("Which players data do you want (if more than one player, seperate by comma)? ")

# file creation
filename = "inputpropbettinglines.csv"
f = open(filename, "a", encoding = 'utf8')

browser = webdriver.Chrome("*/chromedriver") # locate path for chromedriver
def everything(player):

    # opening the browser
    browser.get('https://www.basketball-reference.com/')

    # finding the search and searching up the wanted player
    searchBar = browser.find_element_by_name('search')
    searchBar.send_keys(player)
    searchBar.send_keys(Keys.ENTER)

    # try catch to continue if name messes up
    zeroResults = browser.find_elements_by_xpath("//*[contains(text(), '0 hits')]")
    if len(zeroResults) > 0:
        f.write("The scraper messed up for " + player + ".\n\n")
        return

    try:
        nextClick = browser.find_element_by_class_name('search-item-url')
        nextClick = nextClick.text
        nextClick = nextClick.strip(".html")
        nextClick += "/gamelog/2020"
        browser.get('https://www.basketball-reference.com/' + nextClick)
        print(player)
    except:
        nextClick = browser.current_url
        nextClick = nextClick[:-5]
        nextClick += "/gamelog/2020"
        browser.get(nextClick)
        print(player)

    noPlaying = browser.find_elements_by_xpath("//*[contains(text(), 'Wins,  Losses')]")
    if len(noPlaying) > 0:
        f.write("There is no data for " + player + ". " + player + " has not played this season.\n\n")
        return

    # scraping algo, opening up connection, grabbing page
    my_URL = browser.current_url
    uClient = uReq(my_URL)
    page_html = uClient.read()
    uClient.close()

    # html parser
    page_soup = soup(page_html, "html.parser")

    # grabs the HTML for the titles
    container = page_soup.findAll("th")
    del container[30:]
    hash = {}
    for x in container:
        hash[x.text] = ""

    # algo to scrape the data
    def scraper(dict, query, category):
        temp = page_soup.findAll("td", {"data-stat":query})
        tmp = []
        for x in temp:
            tmp.append(x.text)
        dict[category] = tmp

    # could be improved here
    scraper(hash, "game_season", "G")
    scraper(hash, "date_game", "Date")
    scraper(hash, "age", "Age")
    scraper(hash, "team_id", "Tm")
    scraper(hash, "game_result", "\xa0")
    scraper(hash, "opp_id", "Opp")
    scraper(hash, "gs", "GS")
    scraper(hash, "mp", "MP")
    scraper(hash, "fg", "FG")
    scraper(hash, "fga", "FGA")
    scraper(hash, "fg_pct", "FG%")
    scraper(hash, "fg3", "3P")
    scraper(hash, "fg3a", "3PA")
    scraper(hash, "fg3_pct", "3P%")
    scraper(hash, "ft", "FT")
    scraper(hash, "fta", "FTA")
    scraper(hash, "ft_pct", "FT%")
    scraper(hash, "orb", "ORB")
    scraper(hash, "drb", "DRB")
    scraper(hash, "trb", "TRB")
    scraper(hash, "ast", "AST")
    scraper(hash, "stl", "STL")
    scraper(hash, "blk", "BLK")
    scraper(hash, "tov", "TOV")
    scraper(hash, "pf", "PF")
    scraper(hash, "pts", "PTS")
    scraper(hash, "game_score", "GmSc")
    scraper(hash, "plus_minus", "+/-")

    # algo for rank
    count = []
    for x in range(len(hash["Date"])):
        count.append(x + 1)
    count.append("Average:")
    count.append("Median:")
    hash["Rk"] = count

    # algo to convert time
    count = []
    for x in range(len(hash["MP"])):
        temp = hash["MP"][x].split(":")
        temp = (int(temp[0]) * 60) + int(temp[1])
        count.append(temp)
    hash["MP"] = count

    # algo to calculate mean and median
    def medianAverage(dict, query):
        temp = dict[query]
        for x in range(len(temp)):
            try:
                temp[x] = float(temp[x])
            except:
                temp[x] = np.nan
        try:
            med = round(np.nanmedian(temp), 2)
        except:
            med = "N/A"
        try:
            avg = round(np.nanmean(temp), 2)
        except:
            avg = "N/A"
        for x in range(len(dict["G"])):
            if dict["G"][x] == "":
                dict[query].insert(x, "")
        dict[query].append(avg)
        dict[query].append(med)

    medianAverage(hash, "GS")
    medianAverage(hash, "MP")
    medianAverage(hash, "FG")
    medianAverage(hash, "FGA")
    medianAverage(hash, "FG%")
    medianAverage(hash, "3P")
    medianAverage(hash, "3PA")
    medianAverage(hash, "3P%")
    medianAverage(hash, "FT")
    medianAverage(hash, "FTA")
    medianAverage(hash, "FT%")
    medianAverage(hash, "ORB")
    medianAverage(hash, "DRB")
    medianAverage(hash, "TRB")
    medianAverage(hash, "AST")
    medianAverage(hash, "STL")
    medianAverage(hash, "BLK")
    medianAverage(hash, "TOV")
    medianAverage(hash, "PF")
    medianAverage(hash, "PTS")
    medianAverage(hash, "GmSc")
    medianAverage(hash, "+/-")

    # converting time back
    count = []
    for x in hash["MP"]:
        if x != "":
            minutes = int(x // 60)
            seconds = int(x % 60)
            if len(str(seconds)) < 2:
                output = "      " + str(minutes) + ":0" + str(seconds)
            else:
                output = "      " + str(minutes) + ":" + str(seconds)
            count.append(output)
        else:
            count.append("")
    hash["MP"] = count

    # outputing the file
    for x in hash.keys():
        if x == "\xa0":
            f.write("Score,")
        else:
            f.write(str(x) + ",")
    for x in range(len(hash["Rk"])):
        f.write("\n")
        for y in hash.keys():
            try:
                if hash[y][x] is np.nan:
                    f.write(",")
                else:
                    f.write(str(hash[y][x]) + ",")
            except:
                f.write(",")
    f.write("\nThese are the results for " + player + ". Written by @jefpotle.\n\n")

players = players.split(", ")
for x in players:
    if x == "" or x == " ":
        pass
    else:
        everything(x)
f.close()
browser.close()
shutil.move("inputpropbettinglines.csv", "*/Desktop") # location path for desktop
