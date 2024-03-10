from seleniumbase import SB
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from data import client_urls
import json
import base64


class PageJaunesScraper:
    def __init__(self):
        self.base_urls = []
        self.data = []

    def verify_success(self):
        """
        Verifies the success of an action by sleeping for 1 second.
        """
        self.sb.sleep(1)

    def passCloudFareVerification(self):
        """
        Handles the CloudFare verification process.
        """
        try:
            self.verify_success()
        except Exception:
            if self.sb.is_element_visible('input[value*="Verify"]'):
                self.sb.click('input[value*="Verify"]')
            elif self.sb.is_element_visible('iframe[title*="challenge"]'):
                self.sb.switch_to_frame('iframe[title*="challenge"]')
                self.sb.click("span.mark")
                return True
            else:
                self.passCloudFareVerification()
        try:
            self.verify_success()
        except Exception:
            self.passCloudFareVerification()

    def make_perfect_url(self, base_url):
        """
        Constructs a perfect URL based on the given base URL.
        """
        parsed_url = urlparse(base_url)
        if parsed_url.path == "/annuaire/chercherlespros":
            query_params = parse_qs(parsed_url.query)
            preserved_params = {
                key: value[-1] if isinstance(value, list) else value
                for key, value in query_params.items()
                if key in ["quoiqui", "ou", "tri", "page"]
            }
            perfect_url = urlunparse(
                (
                    parsed_url.scheme,
                    parsed_url.netloc,
                    parsed_url.path,
                    parsed_url.params,
                    urlencode(preserved_params, doseq=True),
                    parsed_url.fragment,
                )
            )
        else:
            path_parts = parsed_url.path.split("/")
            city = path_parts[-2] if len(path_parts) >= 3 else None
            category = path_parts[-1] if len(path_parts) >= 2 else None
            query_params = {
                "quoiqui": [category] if category else ["restaurants"],
                "ou": [city] if city else ["paris-75"],
            }
            perfect_url = urlunparse(
                (
                    parsed_url.scheme,
                    parsed_url.netloc,
                    "/annuaire/chercherlespros",
                    parsed_url.params,
                    urlencode(query_params, doseq=True),
                    "",
                )
            )
        return perfect_url

    def get_limits_pages(self, compteur):
        """
        Extracts the limits of pages from the given counter string.
        """
        return list(map(int, compteur[4:].split(" / ")))

    def add_arguments_to_url(self, base_url, **kwargs):
        """
        Adds the given keyword arguments as query parameters to the base URL.
        """
        parsed_url = urlparse(base_url)
        query_params = parse_qs(parsed_url.query)
        for key, value in kwargs.items():
            query_params[key] = [value]
        updated_query_string = urlencode(query_params, doseq=True)
        updated_url = urlunparse(
            (
                parsed_url.scheme,
                parsed_url.netloc,
                parsed_url.path,
                parsed_url.params,
                updated_query_string,
                parsed_url.fragment,
            )
        )
        return updated_url

    def process_urls(self):
        """
        Processes the base URLs and returns a list of updated URLs with parameters.
        """
        updated_urls = []
        for item in self.base_urls:
            url = item.get("url")
            params = item.get("params", {})
            page = params.get("page", 1)
            tri = params.get("tri", "PERTINENCE-ASC")
            limit = item.get("limit", 1)
            try:
                perfect_url = self.make_perfect_url(url)
                if not params and "?" in perfect_url:
                    updated_url = perfect_url
                else:
                    updated_url = self.add_arguments_to_url(
                        perfect_url, page=page, tri=tri
                    )
                updated_urls.append(
                    {"url": updated_url, "start-limit": page, "end-limit": limit}
                )
            except ValueError as e:
                print("Error:", e)
        return [
            dict(item) for item in set(tuple(item.items()) for item in updated_urls)
        ]

    def decode_link(self, attribute_link):
        """
        Decodes the encoded URL from the given attribute link.
        """
        data_dict = json.loads(attribute_link)
        encoded_url = data_dict["url"]
        decoded_url = base64.b64decode(encoded_url).decode("utf-8")
        return decoded_url

    def get_simple_info(self, selector):
        """
        Retrieves the content of the element identified by the given selector.
        """
        if self.sb.is_element_visible(selector):
            content = self.sb.get_text(selector)
            return content
        else:
            return "Element not found!"

    def get_card_info(self, base_url, card_url):
        """
        Retrieves and prints information from the card URL.
        """
        print("\n", card_url)
        self.sb.open(card_url["base_url"])
        try:
            #!---------------------------- Title ----------------------------
            title = self.get_simple_info(
                "div.header-main-infos h1.noTrad"
            ).splitlines()[0]
            self.data[-1]["pages"][-1]["cards"][-1]["data"]["title"] = title
            #!---------------------------- Activite ----------------------------
            parsed_url = urlparse(base_url)
            query_params = parse_qs(parsed_url.query)
            quoiqui_value = query_params.get("quoiqui")
            if quoiqui_value:
                self.data[-1]["pages"][-1]["cards"][-1]["data"]["activite"] = (
                    quoiqui_value[0]
                )
            else:
                self.data[-1]["pages"][-1]["cards"][-1]["data"][
                    "activite"
                ] = "Not Found"
                print(
                    "Activite: !!!!!!!!!!!!!!!!!!! You have a bugs !!!!!!!!!!!!!!!!!!!!!!"
                )
            #!---------------------------- Rank ----------------------------
            rank = self.get_simple_info("span.note_moyenne")
            self.data[-1]["pages"][-1]["cards"][-1]["data"]["rank"] = rank
            #!---------------------------- Avis ----------------------------
            avis = self.get_simple_info("span.bi-rating")
            self.data[-1]["pages"][-1]["cards"][-1]["data"]["avis"] = avis
            #!---------------------------- Adress ----------------------------
            adress = self.get_simple_info("div.address-container span.noTrad")
            self.data[-1]["pages"][-1]["cards"][-1]["data"]["adress"] = adress
            #!---------------------------- Website ----------------------------
            website = self.get_simple_info("div.lvs-container span.value")
            self.data[-1]["pages"][-1]["cards"][-1]["data"]["website"] = website
            #!---------------------------- Horaires ----------------------------
            try:
                if self.sb.is_element_visible("ul.liste-horaires-principaux"):
                    horaires_elements = self.sb.find_elements("li.horaire-ouvert")
                    list_horaires = []
                    for index, horaire_element in enumerate(horaires_elements):
                        if self.sb.is_element_visible(
                            f"li.horaire-ouvert:nth-child({index+1})"
                        ):
                            day = self.sb.get_text(
                                f"li.horaire-ouvert:nth-child({index+1}) p.jour"
                            )
                            horaire = self.sb.get_text(
                                f"li.horaire-ouvert:nth-child({index+1}) p.liste"
                            )
                            list_horaires.append({"jour": day, "horaire": horaire})
                    self.data[-1]["pages"][-1]["cards"][-1]["data"][
                        "horaires"
                    ] = list_horaires
            except:
                self.data[-1]["pages"][-1]["cards"][-1]["data"][
                    "horaires"
                ] = "Not found!"
                print("Horaires not found!")
            #!---------------------------- Réseaux Sociaux ----------------------------
            try:
                if self.sb.is_element_visible(
                    "div.bloc-info-sites-reseaux ul.clearfix"
                ):
                    links_elements = self.sb.find_elements(
                        "ul.clearfix li.premiere-visibilite"
                    )
                    links = []
                    for index, link_element in enumerate(links_elements):
                        if self.sb.is_element_visible(
                            f"ul.clearfix li.premiere-visibilite:nth-child({index+1}) a.pj-link"
                        ):
                            href_link = self.sb.get_attribute(
                                f"ul.clearfix li.premiere-visibilite:nth-child({index+1}) a.pj-link",
                                "href",
                            )
                            if (
                                href_link
                                == f"https://www.pagesjaunes.fr/pros/{card_url['card_id']}#"
                            ):
                                attribute_link = self.sb.get_attribute(
                                    f"ul.clearfix li.premiere-visibilite:nth-child({index+1}) a.pj-link",
                                    "data-pjlb",
                                )
                                links.append(self.decode_link(attribute_link))
                            else:
                                links.append(href_link)
                    self.data[-1]["pages"][-1]["cards"][-1]["data"]["links"] = links

            except:
                self.data[-1]["pages"][-1]["cards"][-1]["data"]["links"] = "Not found!"
            #!---------------------------- Telephone ----------------------------
            try:
                if self.sb.is_element_visible('a[title="Appeler ce professionnel"]'):
                    phones = []
                    phones_number = self.sb.find_elements(
                        'a[title="Appeler ce professionnel"]'
                    )
                    for phone_number in phones_number:
                        attribute = phone_number.get_attribute("data-pjlb")
                        phones.append(self.decode_link(attribute))
                    print("Telepone Data: ", phones)
                    self.data[-1]["pages"][-1]["cards"][-1]["data"][
                        "telephone"
                    ] = phones
            except:
                self.data[-1]["pages"][-1]["cards"][-1]["data"][
                    "telephone"
                ] = "Not found!"
        #!--------------------------------------------- End -------------------------------------------------
        except Exception as e:
            print("Error:", e)

    def app(self, base_url):
        """
        Main application logic for scraping data from the base URL.
        """
        self.sb.open(base_url)
        if self.sb.is_element_visible("span.didomi-continue-without-agreeing"):
            self.sb.click("span.didomi-continue-without-agreeing")
        else:
            pass
        if self.sb.is_element_visible("span#SEL-compteur"):
            compteur = self.sb.get_text("span#SEL-compteur")
            print(self.get_limits_pages(compteur))
        if self.sb.is_element_visible("ul.bi-list"):
            lists_li = self.sb.find_elements("ul.bi-list li.bi")
            lists_card_url = []
            for index, list in enumerate(lists_li):
                if self.sb.is_element_visible(f"li.bi:nth-child({index+1})"):
                    list_id = self.sb.get_attribute(
                        f"li.bi:nth-child({index+1})", "id"
                    ).split("-")[1]
                    lists_card_url.append(
                        {
                            "base_url": f"https://www.pagesjaunes.fr/pros/{list_id}#zoneHoraires",
                            "card_id": list_id,
                        }
                    )
                else:
                    continue
            print(lists_card_url)
            # for card_url in lists_card_url:
            for card_url in lists_card_url[:0]:
                self.data[-1]["pages"][-1]["cards"].append(
                    {
                        "card_id": card_url["card_id"],
                        "url": card_url["base_url"],
                        "data": {},
                    }
                )
                self.get_card_info(base_url, card_url)

    def run(self):
        """
        Starts the application by initializing the web driver and executing the scraping process.
        """
        with SB(uc_cdp=True, guest_mode=True, headless=False, undetected=True) as sb:
            self.sb = sb
            self.sb.set_window_size(600, 1200)
            self.sb.open("https://www.pagesjaunes.fr")

            # Try to pass the CloudFare verification process
            try:
                self.passCloudFareVerification()
            except Exception:
                try:
                    self.verify_success()
                except Exception:
                    pass
                    self.sb.open("https://www.pagesjaunes.fr")

            # Handle cookies
            if self.sb.is_element_visible("span.didomi-continue-without-agreeing"):
                self.sb.click("span.didomi-continue-without-agreeing")

            # Loop through provided URLs and iterate over each to navigate through each subsequent page.
            for updated_url in self.process_urls():
                try:
                    print(
                        "|------------------- Base: ",
                        updated_url,
                        " -----------------|",
                    )
                    url = updated_url["url"]
                    start_limit = updated_url.get("start-limit")
                    end_limit = updated_url.get("end-limit")
                    self.data.append({"base_url": url, "pages": []})
                    for pageNumber in range(start_limit, start_limit + end_limit):
                        url = self.add_arguments_to_url(url, page=pageNumber)
                        self.data[-1]["pages"].append(
                            {"page": pageNumber, "url": url, "cards": []}
                        )
                        print("|__Next Page__|:", url)
                        self.app(url)
                    yield self.data[-1]
                except Exception as e:
                    print("Error:", e)
                print("__" * 70)
            # return self.data

    def add_base_url(self, url, params=None, limit=1):
        self.base_urls.append({"url": url, "params": params, "limit": limit})

        # --------------------------------------- Start App ----------------------------------------


# scraper = PageJaunesScraper()

# for url in client_urls[:1]:
#     scraper.add_base_url(url["url"], params=url.get("params"), limit=url.get("limit"))
# print(scraper.run())
