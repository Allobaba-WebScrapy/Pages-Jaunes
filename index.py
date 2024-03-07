from seleniumbase import SB
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
import json
import base64


chrome_options = {
    # "args": ["--headless"]
    "args": ["--disable-gpu"]
}


def verify_success(sb):
    sb.sleep(1)


def passCloudFareVerification(sb):
    try:
        verify_success(sb)
    except Exception:
        if sb.is_element_visible('input[value*="Verify"]'):
            sb.click('input[value*="Verify"]')
        elif sb.is_element_visible('iframe[title*="challenge"]'):
            sb.switch_to_frame('iframe[title*="challenge"]')
            sb.click("span.mark")
            return True
        else:
            passCloudFareVerification(sb)
    try:
        verify_success(sb)
    except Exception:
        passCloudFareVerification(sb)


def make_perfect_url(base_url):
    # Parse the base URL
    parsed_url = urlparse(base_url)

    # Extract city and category information from the path
    path_parts = parsed_url.path.split("/")
    city = path_parts[-2] if len(path_parts) >= 3 else None
    category = path_parts[-1] if len(path_parts) >= 2 else None

    # Construct query parameters
    query_params = {
        "quoiqui": [category] if category else ["restaurants"],
        "ou": [city] if city else ["paris-75"],
        "page": ["1"],
    }

    # Reconstruct the URL with perfect structure
    perfect_url = urlunparse(
        (
            parsed_url.scheme,
            parsed_url.netloc,
            "/annuaire/chercherlespros",
            parsed_url.params,
            urlencode(query_params, doseq=True),
            parsed_url.fragment,
        )
    )
    return perfect_url


def decode_link(attribute_link):
    # ?---------------// Decode URL \\---------------
    # Parse the JSON string
    data_dict = json.loads(attribute_link)
    # Extract the URL and decode it
    encoded_url = data_dict["url"]
    decoded_url = base64.b64decode(encoded_url).decode("utf-8")
    # ? ---------------------------------------------
    return decoded_url


def handle_card_info(sb, card_url):
    print("\n", card_url)
    sb.open(card_url["base_url"])

    #!---------------------------- Title ----------------------------
    if sb.is_element_visible("div.header-main-infos h1.noTrad"):
        title = sb.get_text("div.header-main-infos h1.noTrad").splitlines()[
            0
        ]  # => get just the title
        print("Title: ", title)

    #!---------------------------- Activite ----------------------------
    if sb.is_element_visible("span.activite"):
        activite = sb.get_text("span.activite")
        print("Activite: ", activite)

    #!---------------------------- Rank ----------------------------
    if sb.is_element_visible("span.note_moyenne"):
        rank = sb.get_text("span.note_moyenne")
        print("Rank: ", rank)

    #!---------------------------- Avis ----------------------------
    if sb.is_element_visible("span.bi-rating"):
        avis = sb.get_text("span.bi-rating")
        print("Avis: ", avis)

    #!---------------------------- Adress ----------------------------
    if sb.is_element_visible("div.address-container span.noTrad"):
        adress = sb.get_text("div.address-container span.noTrad")
        print("Adress: ", adress)
    if sb.is_element_visible("div.lvs-container span.value"):
        website = sb.get_text("div.lvs-container span.value")
        print("Website: ", website)

    #!---------------------------- Horaires ----------------------------
    if sb.is_element_visible("ul.liste-horaires-principaux"):
        horaires_elements = sb.find_elements("li.horaire-ouvert")
        list_horaires = []
        for index, horaire_element in enumerate(horaires_elements):
            if sb.is_element_visible(f"li.horaire-ouvert:nth-child({index+1})"):
                day = sb.get_text(f"li.horaire-ouvert:nth-child({index+1}) p.jour")
                horaire = sb.get_text(f"li.horaire-ouvert:nth-child({index+1}) p.liste")
                list_horaires.append({"jour": day, "horaire": horaire})
        print("Horaires: ", list_horaires)

    #!---------------------------- Réseaux Sociaux ----------------------------
    if sb.is_element_visible("div.bloc-info-sites-reseaux ul.clearfix"):
        links_elements = sb.find_elements("ul.clearfix li.premiere-visibilite")
        list_links = []

        for index, link_element in enumerate(links_elements):
            if sb.is_element_visible(
                f"ul.clearfix li.premiere-visibilite:nth-child({index+1}) a.pj-link"
            ):
                href_link = sb.get_attribute(
                    f"ul.clearfix li.premiere-visibilite:nth-child({index+1}) a.pj-link",
                    "href",
                )
                if (
                    href_link
                    == f"https://www.pagesjaunes.fr/pros/{card_url['card_id']}#"
                ):
                    attribute_link = sb.get_attribute(
                        f"ul.clearfix li.premiere-visibilite:nth-child({index+1}) a.pj-link",
                        "data-pjlb",
                    )
                    list_links.append(decode_link(attribute_link))
                else:
                    list_links.append(href_link)
        print("Réseaux Sociaux: ", list_links)

    #!---------------------------- Telephone ----------------------------
    if sb.is_element_visible('a[title="Appeler ce professionnel"]'):
        # if sb.is_element_visible('span.coord-numero-mobile'):
        phones_number = sb.find_elements('a[title="Appeler ce professionnel"]')
        for phone_number in phones_number:
            attribute = phone_number.get_attribute("data-pjlb")
            print(decode_link(attribute))


# --------------------------------------- Start App ----------------------------------------
with SB(uc_cdp=True, guest_mode=True, headless=False, undetected=True) as sb:
    sb.set_window_size(600, 1200)
    sb.open("https://www.pagesjaunes.fr")

    # Handle CloudFare Verification
    try:
        verify_success(sb)
    except Exception:
        if sb.is_element_visible('input[value*="Verify"]', timeout=10):
            sb.click('input[value*="Verify"]')
        elif sb.is_element_visible('iframe[title*="challenge"]', timeout=10):
            sb.switch_to_frame('iframe[title*="challenge"]')
            sb.click("span.mark")
        else:
            # sb.open('https://www.pagesjaunes.fr')
            raise Exception("Detected!")
        try:
            verify_success(sb)
        except Exception:
            # sb.open('https://www.pagesjaunes.fr')
            raise Exception("Detected!")

    # Handle Coockies
    if sb.is_element_visible("span.didomi-continue-without-agreeing"):
        print("Done Cookie")
        # ? <span class='didomi-continue-without-agreeing'>
        sb.click("span.didomi-continue-without-agreeing")

    def app(base_url):
        sb.open(base_url)
        # https://www.pagesjaunes.fr/annuaire/chercherlespros?quoiqui=restaurants&ou=paris-75&page=1
        # sb.open('https://webcache.googleusercontent.com/search?q=cache:https://www.pagesjaunes.fr/annuaire/paris-75/restaurants')

        # Handle Coockies
        if sb.is_element_visible("span.didomi-continue-without-agreeing"):
            print("Done Cookie")
            # ? <span class='didomi-continue-without-agreeing'>
            sb.click("span.didomi-continue-without-agreeing")
        else:
            pass

        # Get all card 1
        if sb.is_element_visible("ul.bi-list"):
            print(
                "Done <ul> List\n"
            )  # ? <span class='didomi-continue-without-agreeing'>
            # lists_li = sb.find_elements('ul.bi-list li.bi')
            # lists_card_url = []
            # for index, list in enumerate(lists_li):
            #     list_id = sb.get_attribute(f'li.bi:nth-child({index+1})','id').split('-')[1]
            #     lists_card_url.append({"base_url":f'https://www.pagesjaunes.fr/pros/{list_id}#zoneHoraires', "card_id":list_id})
            # print(lists_card_url)
            # for card_url in lists_card_url[:1] :
            #     handle_card_info(sb, card_url)

    base_urls = [
        "https://www.pagesjaunes.fr/annuaire/paris-75/coiffeurs",
        "https://www.pagesjaunes.fr/annuaire/paris-75/restaurants",
        "https://www.pagesjaunes.fr/annuaire/paris-75/boulangeries-patisseries-artisans",
        "https://www.pagesjaunes.fr/annuaire/paris-75/agences-immobilieres",
        "https://www.pagesjaunes.fr/annuaire/paris-75/clubs-de-sport-divers",
    ]
    for base_url in base_urls:
        try:
            app(make_perfect_url(base_url))
        except:
            print("Failed")
        print("|_" * 70)
