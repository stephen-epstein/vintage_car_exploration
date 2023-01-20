from bs4 import BeautifulSoup
import requests
import re


def get_urls(urlstart: str, urlend: str, pgend: int, urls: list):
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

    # Iterate through each page (Show More in BaT) and collect urls
    while pgnum < pgend:
        url.append(urlstart + str(pgnum) + urlend)
        pgnum += 1

    # For each URL get soup
    for j in range(0, len(url)):
        r = requests.get(url[j])
        soup = BeautifulSoup(r.content, "html.parser")
        urltemp = str(soup)
        i = 0
        # Search page for all listings and try to filter out non-car listings
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


def get_engine(transmission: str):
    """This function pulls the engine displacement. If displacement is negative, the engine displacement was not available.

    Args:
        transmission: Side bar text info on listing

    Returns:
        eng: float of engine displacement
    """
    i = 0
    eng = -1
    while i < len(transmission):
        if (
            transmission[i].isdigit() == True
            and transmission[i + 1] == "."
            and transmission[i + 2].isdigit() == True
            and (transmission[i + 3] == "-" or transmission[i + 3] == "L")
        ):
            eng = transmission[i : i + 3]
            break
        else:
            i += 1
    return float(eng)


def get_desc(urls: str):
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


def get_month(title: str):
    """This function pulls the month of the sale date.

    Args:
        title: String of HTML title

    Returns:
        month: Integer of month
    """

    months = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]

    for index, item in enumerate(months):
        if item in title:
            return index + 1

    return "N/A"


def get_sale_price(title: str, loc: str):
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


def get_location(loc: str):
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


def get_mileage(mileage: str):
    """This function pulls the mileage of the car or if TMU (Total Mileage Unknown) it will try to pull the number of miles listed on the odometer.

    Args:
        Mileage: String of mileage 'li' class in soup

    Returns:
        Miles: Mileage if not TMU
        MilesTMU: Mileage if TMU
    """
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
        miles = mileage[index - 20 : index].partition("<li>")[2]
        if "k" in miles or "K" in miles:
            miles = re.sub(r"[^0-9]", "", miles)
            miles = int(miles) * 1000
        else:
            miles = re.sub(r"[^0-9]", "", miles)
    else:
        milestmu = mileage[index - 20 : index].partition("<li>")[2]
        if "k" in milestmu or "K" in milestmu:
            milestmu = re.sub(r"[^0-9]", "", milestmu)
            milestmu = int(milestmu) * 1000
        else:
            milestmu = re.sub(r"[^0-9]", "", milestmu)

    if "kilometers" in mileage or "Kilometers" in mileage:
        if miles == "TMU":
            miles = "TMU - K"
        elif milestmu == "N/A":
            milestmu = "N/A - K"
    return miles, milestmu


def get_indicators(contents: str):
    """This function pulls multiple indicator variables if certain specific words appear in the listing body. (0 for no, 1 for yes)

    Args:
        Contents: String containing the entire body of listing description.

    Returns:
        rust: Search for rust word
        refurbished: Search for refurbished word
        restored: Search for restored word
        scratch: Search for scratch word
        paintbub: Search for paint bubble word
        metalrepair: Search for metal repair word
        hardtop: Search for hardtop word
        overdrive: Search for overdrive word
        turbo: Search for turbocharged word
        super: Search for supercharged word
    """
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


def get_listings(make: str, model: str):
    """This function accepts the make and model of the car and constructs a list of listing urls to iterate through in the main code.

    Args:
        Make: String of car make
        Model: String of car model

    Returns:
        ids: list of different series models if available to iterate through (For example Jaguar XKE has series I, II and III pages all separated, this deals with that)
        urls: list of listing urls
    """
    ids = []
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

    # Iterate through soup to find urls on each show more page and append to urls
    for i in range(0, len(url)):
        if url[i : i + r] == search:
            par_word = '"url":"'
            tempurl = url[i + r : i + 200].partition(par_word)[2]
            tempurl = tempurl.partition('"')[0]
            if "\\" in tempurl:
                tempurl = tempurl.replace("\\", "")
                if tempurl not in urls:
                    urls.append(tempurl.replace("\\", ""))
    # Iterate through the urls list and search for bat_keyword_pages to find unique ids for each page needed to make dynamic searching possible
    for i in urls:
        urltemp = i
        word = "bat_keyword_pages"
        listings = []
        r = requests.get(urltemp)
        soup = BeautifulSoup(r.content, "html.parser")
        url = str(soup.findAll("div"))
        if word in url:
            index = url.index(word)
            index = index + len(word) + 3
            id = url[index : index + 30].partition("]")[0]
            ids.append(id)

    return ids, urls


def get_engine_desc(essentials: str, engine: float):
    """This function accepts the essentials class from the soup and the current value of the engine size in float format and checks if the engine is correct and corrects the value if not.
    It also checks for certain key words and if found it will use the sentence as a description for the relevant output variable.

    Args:
        essentials: String of car descriptors
        engine: float of engine displacement in liters
    Returns:
        chassis: Chassis Number
        specialdesc: Descriptor for if mileage is not listed first, usually a special descriptor
        mileagedesc: Descriptor if mileage is found
        enginedesc: Descriptor of engine displacement and setup if found
        transdesc: Descriptor of transmission/gearbox if found
        paintdesc: Descriptor of car color if found
        interiodesc: Descriptor of interior if found
        carbdesc: Descriptor of carburetors if found
        wheeldesc: Descriptor of wheels if found
        brakedesc: Descriptor of brakes if found
        suspdesc: Descriptor of suspension if found
    """
    try:
        essentials = essentials.findAll("li")
    except:
        pass
    chassis = essentials[0].text
    chassis = chassis.partition(":")[2]
    specialdesc = "N/A"
    mileagedesc = (
        enginedesc
    ) = (
        transdesc
    ) = (
        paintdesc
    ) = interiordesc = carbdesc = wheeldesc = brakedesc = suspdesc = specialdesc

    # Iterate through each item in essentials and try to determine where mileage is listed, as well as engine description and use engine description to pull displacement
    # Includes special description in special case
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
                try:
                    engine = round(int(engine) / 1000, 1)
                except:
                    engine = -1.0
            elif engine == -1.0 and "ci" in enginedesc and "cc" not in enginedesc:
                index = enginedesc.partition("ci")[0]
                engine = re.sub(r"[^0-9]", "", index)
                try:
                    engine = round(int(engine) / 61.0237, 1)
                except:
                    engine = -1.0
            if i != 1:
                specialdesc = essentials[1].text

    # Iterate through essentials to find transmission, wheel, paint, upholstery, interior, carburetor, brakes, and suspension description
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
    for i in range(1, len(essentials)):
        if "Suspension" in essentials[i].text:
            suspdesc = essentials[i].text

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
        suspdesc,
        engine,
    )


def get_listings_no_model(make: str):
    if " " in make:
        make = make.replace(" ", "-")
    url = "https://bringatrailer.com/" + make + "/"
    r = requests.get(url)
    soup = BeautifulSoup(r.content, "html.parser")
    url = str(soup)
    i = 0
    urls = []
    while i < len(url):
        if url[i : i + 5] == '"url"':
            tempurl = url[i + 7 : i + 200].partition('"')[0]
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

    if len(urls) > 30:
        urlstart = (
            "https://bringatrailer.com/wp-json/bringatrailer/1.0/data/keyword-filter?s="
            + make
            + "&sort=td&page="
        )
        urlend = "&results=items"
        url = []
        pgnum = 1
        pgend = 15

        # Iterate through each page (Show More in BaT) and collect urls
        while pgnum < pgend:
            url.append(urlstart + str(pgnum) + urlend)
            pgnum += 1

        # For each URL get soup
        for j in range(0, len(url)):
            r = requests.get(url[j])
            soup = BeautifulSoup(r.content, "html.parser")
            urltemp = str(soup)
            i = 0
            # Search page for all listings and try to filter out non-car listings
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
