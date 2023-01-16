from bs4 import BeautifulSoup
import requests
import re
import pandas as pd
import joblib
import os
import sys


def geturls(urlstart: str, urlend: str, pgend: int, urls: list):
    """This function pulls the list of urls for each listing.

    Args:
        urlstart: First part of the url split at page number
        urlend: Last part of url split at page number
        pgend: Number of pages the car has on BaT

    Returns:
        urls: List of urls
    """
    url = []
    pgnum = 1
    while pgnum < pgend:
        url.append(urlstart + str(pgnum) + urlend)
        pgnum += 1

    for j in range(0, len(url)):
        r = requests.get(url[j])
        soup = BeautifulSoup(r.content, "html.parser")
        urltemp = str(soup)
        i = 0

        while i < len(urltemp):
            if urltemp[i : i + 5] == '"url"':
                tempurl = urltemp[i + 7 : i + 200].partition('"')[0]
                if (
                    "listing" in tempurl
                    and "parts" not in tempurl
                    and "hardtop" not in tempurl
                    and "tool" not in tempurl
                    and "memorabilia" not in tempurl
                    and "tool kit" not in tempurl
                    and "inline" not in tempurl
                    and "removable" not in tempurl
                    and "gearbox" not in tempurl
                ):
                    if "\\" in tempurl:
                        tempurl = tempurl.replace("\\", "")
                        if tempurl not in urls:
                            urls.append(tempurl.replace("\\", ""))
            i += 1
    return urls


def getengine(transmission: str):
    """This function pulls the engine displacement. If displacement is negative, the engine displacement was not available.

    Args:
        transmission: Side bar text info on listing

    Returns:
        final: float of engine displacement
    """
    i = 0
    final = -1
    while i < len(transmission):
        if (
            transmission[i].isdigit() == True
            and transmission[i + 1] == "."
            and transmission[i + 2].isdigit() == True
            and (transmission[i + 3] == "-" or transmission[i + 3] == "L")
        ):
            final = transmission[i : i + 3]
            break
        else:
            i += 1
    return float(final)


def getdesc(urls: str):
    """This function pulls the year, make and model of the car. Sometimes it will pull extra numbers because of how the urls are formatted but that is ok.

    Args:
        urls: The url of the listing

    Returns:
        desc: String of year, make and model
    """
    tempurl = urls.partition("listing/")[2]
    final = tempurl.split("-")
    test = final[-1].replace("/", "")
    if test.isdigit() == True:
        final.pop()
    desc = " ".join(final)
    desc = desc.replace("/", "")
    return desc


def getmonth(title: str):
    """This function pulls the month of the sale date.

    Args:
        title: String of HTML title

    Returns:
        month: Integer of month
    """
    if "January" in title:
        month = 1
    elif "February" in title:
        month = 2
    elif "March" in title:
        month = 3
    elif "April" in title:
        month = 4
    elif "May" in title:
        month = 5
    elif "June" in title:
        month = 6
    elif "July" in title:
        month = 7
    elif "August" in title:
        month = 8
    elif "September" in title:
        month = 9
    elif "October" in title:
        month = 10
    elif "November" in title:
        month = 11
    elif "December" in title:
        month = 12
    return month


def getsaleprice(title: str, loc: str):
    """This function pulls the sale price and whether the car met reserve or not.

    Args:
        title: String of HTML title
        loc: String of HTML text

    Returns:
        sold: Indicator for if the car met reserve or not. 1: The car sold, 0: The car did not meet reserve.
        price: Price listed on BaT of the highest bid if it did not meet reserve, or if it did the sale price.
    """
    if "sold for" in title:
        sold = 1
        ind = title.index("$")
        spl_word = " "
        price = title[ind + 1 : ind + 20].partition(spl_word)[0]
    elif "bid to $" in loc:
        sold = 0
        index = loc.index("bid to $")
        price = loc[index + 8 : index + 15].partition("<")[0]
    else:
        price = "N/A"
        sold = 0
    return sold, price


def getlocation(loc: str):
    """This function pulls the sale price and whether the car met reserve or not.

    Args:
        loc: String of HTML text

    Returns:
        town: Town of where the car was being sold from
        State: State of where the car was being sold from
    """
    if "/place/" in loc:
        index = loc.index("/place/")
        town = loc[index + 7 : index + 40].partition(",")[0]
        town = town.replace("%20", " ")

        state = loc[index + 7 : index + 200].partition(",")[2]
        state = state.partition('"')[0]
        state = state.replace("%20", " ")
        state = re.sub(r"[0-9]+", "", state)
    else:
        town = "N/A"
        state = "N/A"
    return town, state


def getmileage(mileage: str):
    miles = "TMU"
    milestmu = "N/A"
    index = 0
    if "Miles" in mileage:
        index = mileage.index("Miles")
    elif "miles" in mileage:
        index = mileage.index("miles")
    elif "kilometers" in mileage:
        index = mileage.index("kilometers")
    elif "Kilometers" in mileage:
        index = mileage.index("Kilometers")

    if "TMU" not in mileage[index + 10 : index + 20]:
        miles = mileage[index - 12 : index].partition("<li>")[2]
        if "k" in miles or "K" in miles:
            miles = re.sub(r"[^0-9]", "", miles)
            miles = int(miles) * 1000
        else:
            miles = re.sub(r"[^0-9]", "", miles)
    else:
        milestmu = mileage[index - 12 : index].partition("<li>")[2]
        if "k" in milestmu or "K" in milestmu:
            milestmu = re.sub(r"[^0-9]", "", milestmu)
            milestmu = int(milestmu) * 1000
        else:
            milestmu = re.sub(r"[^0-9]", "", milestmu)

    if "kilometers" in mileage:
        if miles.isdigit() == True:
            miles = miles + "K"
        else:
            milestmu = milestmu + "K"
    return miles, milestmu


def getindicators(contents):
    # Check for Rust
    if " rust" in contents or "Rust" in contents:
        rust = 1
    else:
        rust = 0

    # Check for Refurbishment
    if "refurbish" in contents or "Refurbish" in contents:
        refurbished = 1
    else:
        refurbished = 0

    # Check for Restoration
    if "restor" in contents or "Restor" in contents:
        restored = 1
    else:
        restored = 0

    # Various other Condition terms
    scratch = 0
    if "scratch" in contents or "Scratch" in contents:
        scratch = 1
    paintbub = 0
    if "paint bubble" in contents or "Paint bubble" in contents:
        paintbub = 1
    metalrepair = 0
    if "metal repair" in contents or "Metal repair" in contents:
        metalrepair = 1

    # Check for Hardtop
    if "hardtop" in contents or "Hardtop" in contents:
        hardtop = 1
    else:
        hardtop = 0

    # Check for Overdrive
    if "overdrive" in contents or "Overdrive" in contents:
        overdrive = 1
    else:
        overdrive = 0

    # Check for forced induction
    if "turbocharged" in contents or "Turbocharged" in contents:
        turbo = 1
    else:
        turbo = 0

    if "supercharged" in contents or "Supercharged" in contents:
        super = 1
    else:
        super = 0

    return (
        rust,
        refurbished,
        restored,
        scratch,
        paintbub,
        metalrepair,
        hardtop,
        overdrive,
        turbo,
        super,
    )


def getlistings(make, model):
    input = make + " " + model
    string = '"title":"'
    if " " in make:
        make = make.replace(" ", "-")
    if " " in model:
        model = model.replace(" ", "-")
    url = "https://bringatrailer.com/" + make + "/"
    urls = []
    r = requests.get(url)
    soup = BeautifulSoup(r.content, "html.parser")
    url = str(soup.findAll("div"))
    search = string + input
    r = len(input) + len(string)
    for i in range(0, len(url)):
        if url[i : i + r] == search:
            par_word = '"url":"'
            tempurl = url[i + r : i + 200].partition(par_word)[2]
            tempurl = tempurl.partition('"')[0]
            # .partition('"')[0]
            if "\\" in tempurl:
                tempurl = tempurl.replace("\\", "")
                if tempurl not in urls:
                    urls.append(tempurl.replace("\\", ""))
    ids = []
    for i in urls:
        urltemp = i
        word = "bat_keyword_pages"
        listings = []
        r = requests.get(urltemp)
        soup = BeautifulSoup(r.content, "html.parser")
        url = str(soup.findAll("div"))
        index = url.index(word)
        index = index + len(word) + 3
        id = url[index : index + 30].partition("]")[0]
        ids.append(id)
    return ids, urls, input


def getenginedesc(essentials, engine):
    try:
        essentials = essentials.findAll("li")
    except:
        essentials = essentials
    chassis = essentials[0].text
    chassis = chassis.partition(":")[2]
    specialdesc = "N/A"
    specialdesc = "N/A"
    mileagedesc = "N/A"
    enginedesc = "N/A"
    transdesc = "N/A"
    paintdesc = "N/A"
    interiordesc = "N/A"
    carbdesc = "N/A"
    wheeldesc = "N/A"
    brakedesc = "N/A"

    for i in range(1, len(essentials)):
        if " Miles" in essentials[i].text or "Kilometer" in essentials[i].text:
            mileagedesc = essentials[i].text
            try:
                enginedesc = essentials[i + 1].text
            except:
                enginedesc = "N/A"
            if engine == -1.0 and "cc" in enginedesc:
                index = enginedesc.partition("cc")[0]
                engine = re.sub(r"[^0-9]", "", index)
                engine = round(int(engine) / 1000, 1)
            elif engine == -1.0 and "ci" in enginedesc and "cc" not in enginedesc:
                index = enginedesc.partition("ci")[0]
                engine = re.sub(r"[^0-9]", "", index)
                try:
                    engine = round(int(engine) / 61.0237, 1)
                except:
                    engine = -1.0
            if i != 1:
                specialdesc = essentials[1].text
    for i in range(1, len(essentials)):
        if (
            "Transmission" in essentials[i].text
            or "Gearbox" in essentials[i].text
            or "-speed" in essentials[i].text
            or "-Speed" in essentials[i].text
        ):
            transdesc = essentials[i].text
    for i in range(1, len(essentials)):
        if (
            "Paint" in essentials[i].text
            or "painted" in essentials[i].text
            and "Wheels" not in essentials[i].text
        ):
            paintdesc = essentials[i].text
    for i in range(1, len(essentials)):
        if "Upholstery" in essentials[i].text or "Interior" in essentials[i].text:
            interiordesc = essentials[i].text
    for i in range(1, len(essentials)):
        if "Carburetor" in essentials[i].text:
            carbdesc = essentials[i].text
    for i in range(1, len(essentials)):
        if "Wheels" in essentials[i].text:
            wheeldesc = essentials[i].text
    for i in range(1, len(essentials)):
        if "Brakes" in essentials[i].text:
            brakedesc = essentials[i].text

    return (
        chassis,
        specialdesc,
        mileagedesc,
        enginedesc,
        transdesc,
        paintdesc,
        interiordesc,
        carbdesc,
        wheeldesc,
        brakedesc,
        engine,
    )
