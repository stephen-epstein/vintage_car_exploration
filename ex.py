from bs4 import BeautifulSoup
import requests
import re
import pandas as pd
import joblib
import sys

#### Get URL List ####
#### DO NOT DELETE ####

url = "https://bringatrailer.com/jaguar/xke/"
urls = []
r = requests.get(url)
soup = BeautifulSoup(r.content, "html.parser")

url = str(soup.findAll("div"))

i = 0

while i < len(url):
    if url[i : i + 5] == '"url"':
        tempurl = url[i + 7 : i + 200].partition('"')[0]
        if (
            "listing" in tempurl
            and "hardtop" not in tempurl
            and "memorabilia" not in tempurl
            and "tool kit" not in tempurl
        ):
            if "\\" in tempurl:
                tempurl = tempurl.replace("\\", "")
                if tempurl not in urls:
                    urls.append(tempurl.replace("\\", ""))
    i += 1


def get_data(url):

    r = requests.get(url)

    soup = BeautifulSoup(r.content, "html.parser")
    return str(soup)


soup_list = joblib.Parallel(n_jobs=-2)(joblib.delayed(get_data)(url) for url in urls)
