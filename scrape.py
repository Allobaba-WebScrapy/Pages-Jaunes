from seleniumbase import SB
from selenium.common.exceptions import TimeoutException
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from data import client_urls
import json
import base64
import time


class PageJaunesScraper:
    def __init__(self):
        self.__server_urls = []
        self.data = []

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

    def get_limits_pages(self, compteur):
        """
        Extracts the limits of pages from the given counter string.
        """
        return list(map(int, compteur[4:].split(" / ")))

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

    def classify_number(self, phone_number):
        if phone_number.startswith(("01", "04", "05")):
            return "B2B"
        elif phone_number.startswith(("06", "07", "09")):
            return "B2C"
        else:
            return "Unknown"

    def check_valid_card(self, index):
        try:
            if self.sb.is_element_present(
                f"li.bi:nth-child({index+1}) div.bi-ctas button"
            ):
                self.sb.click(f"li.bi:nth-child({index+1}) div.bi-ctas button")
                phones = self.sb.find_elements(
                    f"li.bi:nth-child({index +1}) div.bi-ctas div.bi-fantomas div.number-contact"
                )
                isValid = False
                gotPhones = []
                for phoneIndex, phone in enumerate(phones):
                    if self.sb.is_element_visible(
                        f"li.bi:nth-child({index+1}) div.bi-ctas div.number-contact:nth-child({phoneIndex+1}) > span:last-child"
                    ):
                        phone_text = self.sb.get_text(
                            f"li.bi:nth-child({index+1}) div.bi-ctas div.number-contact:nth-child({phoneIndex+1}) > span:last-child"
                        )
                        gotPhones.append(phone_text)
                        if self.data[-1]["businessType"] == self.classify_number(
                            phone_text
                        ):
                            isValid = True

                print("Telephone businessType found: ", list(dict.fromkeys(gotPhones)))
                return {"isValid": isValid, "phone": list(dict.fromkeys(gotPhones))}
        except:
            print("Telephone not found within the given time.")
            return {"isValid": False, "phone": "Element not found!"}

    def get_card_info(self, index):
        #!---------------------------- Title ----------------------------
        title = self.get_simple_info(
            f"li.bi:nth-child({index+1}) div.bi-header-title h3"
        )
        #!---------------------------- Activitée ----------------------------
        activite = self.get_simple_info(
            f"li.bi:nth-child({index+1}) span.bi-activity-unit.small"
        )
        #!---------------------------- Address ----------------------------
        address = self.get_simple_info(
            f"li.bi:nth-child({index+1}) div.bi-address.small a"
        ).replace(" Voir le plan", "")
        #!---------------------------- Address Link ----------------------------
        address_link_attribute = self.sb.get_attribute(
            f"li.bi:nth-child({index+1}) div.bi-address.small a", "data-pjlb"
        )
        address_link = self.decode_link(address_link_attribute) or "No link found!"
        return {
            "title": title,
            "activite": activite,
            "address": {
                "text": address,
                "link": "https://www.pagesjaunes.fr" + address_link,
            },
        }

    def scrap_page(self, base_url, index, endPage):
        print("Page: ", base_url)
        """
        Main application logic for scraping data from the base URL.
        """
        try:
            self.sb.open(base_url)
            self.sb.wait_for_ready_state_complete(timeout=5)
        except:
            print("Page not found!")
            yield {"type": "error", "message": f"Page not found: {index}/{endPage}"}
            return
        try:
            if self.sb.wait_for_element_visible(
                "span.didomi-continue-without-agreeing", timeout=1
            ):
                self.sb.click("span.didomi-continue-without-agreeing")
        except:
            pass
            # if self.sb.is_element_visible("span#SEL-compteur"):
            #     compteur = self.sb.get_text("span#SEL-compteur")
            #     print(self.get_limits_pages(compteur))
            if self.sb.wait_for_element_visible("span#SEL-nbresultat", timeout=2):
                print("Page Found :", self.sb.get_text("span#SEL-nbresultat"))
                # --------------------------------- Page is loaded -------------------------------
                if self.sb.is_element_visible("ul.bi-list"):
                    lists_li = self.sb.find_elements("ul.bi-list li.bi")
                    yield {
                        "type": "progress",
                        "message": f"Scraping Page : {index}/{endPage}",
                        "limiCard": {
                            "scrapedCardsNumbers": 0,
                            "avalaibleCardsNumbers": len(lists_li),
                        },
                    }
                    for index, list in enumerate(lists_li):
                        try:
                            if self.sb.is_element_present(
                                f"li.bi:nth-child({index+1})"
                            ):
                                result = self.check_valid_card(index) or {
                                    "isValid": False,
                                    "phone": "Element not found!",
                                }
                                isValid = result.get("isValid", False)
                                phone = result.get("phone", "Element not found!")
                                if isValid or self.data[-1]["businessType"] == "ALL":
                                    card_id = self.sb.get_attribute(
                                        f"li.bi:nth-child({index+1})", "id"
                                    ).split("-")[1]
                                    # card_id = each_li.get_attribute("id").split("-")[1]
                                    # ---------------- Card Info ----------------
                                    result = self.get_card_info(index)
                                    title = result["title"]
                                    activite = result["activite"]
                                    address = result["address"]
                                    self.data[-1]["pages"][-1]["cards"].append(
                                        {
                                            "card_id": card_id,
                                            "card_url": f"https://www.pagesjaunes.fr/pros/{card_id}#zoneHoraires",
                                            "info": {
                                                "title": title,
                                                "activite": activite,
                                                "address": address,
                                                "phones": phone,
                                            },
                                        }
                                    )
                                    yield self.data[-1]["pages"][-1]["cards"][-1]
                                # ------------------------------------------------
                        except Exception as e:
                            print("Error Scrap Card:", e)
                            yield {
                                "type": "error",
                                "message": f"Fails to scrap card: {index}/{len(lists_li)}",
                            }

    def run(self):
        """
        Starts the application by initializing the web driver and executing the scraping process.
        """
        with SB(
            uc_cdp=True,
            agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            guest_mode=True,
            headless=False,
            undetected=True,
        ) as sb:
            self.sb = sb
            self.sb.set_window_size(600, 1200)
            time.sleep(5)
            try:
                self.sb.open("https://www.pagesjaunes.fr")
                self.sb.wait_for_ready_state_complete(timeout=20)
            except:
                print("Page Jaune not found, please check your internet connection!")
                yield {
                    "type": "error",
                    "message": "Bybass verification failed! Page Jaune not found!",
                }
                return

            #! Try to pass the CloudFare verification process
            try:
                if self.sb.is_element_visible("div.claim.wrapper"):
                    print("Verification passed!")
                    yield {"type": "progress", "message": "Verification passed!"}
                    # Handle cookies
                    try:
                        if self.sb.is_element_visible(
                            "span.didomi-continue-without-agreeing"
                        ):
                            print("Cookie accepted")
                            self.sb.click("span.didomi-continue-without-agreeing")
                            yield {"type": "progress", "message": "Cookies accepted!"}
                    except:
                        print("Bybass cookies failed!")
                        yield {"type": "error", "message": "Bybass cookies failed!"}

                    # Loop through provided URLs and iterate over each to navigate through each subsequent page.
                    for server_url in self.__server_urls:
                        print(server_url)
                        url = server_url["url"]
                        startPage = int(server_url.get("startPage"))
                        endPage = int(server_url.get("endPage"))
                        businessType = server_url.get("businessType")
                        self.data.append(
                            {"base_url": url, "businessType": businessType, "pages": []}
                        )
                        yield {"type": "progress", "message": "Scraping url: " + url}
                        for index, pageNumber in enumerate(
                            range(startPage, startPage + endPage)
                        ):
                            page_url = self.add_arguments_to_url(url, page=pageNumber)
                            self.data[-1]["pages"].append(
                                {"page": pageNumber, "page_url": page_url, "cards": []}
                            )
                            print("|__Next Page__|:", page_url)
                            time.sleep(2)
                            yield from self.scrap_page(page_url, index + 1, endPage)
                        print("__" * 70)
            except:
                print("Bybass verification failed!")
                yield {"type": "error", "message": "Bybass verification failed!"}
            # return self.data

    @property
    def server_urls(self):
        """
        Getter method to get the value of self.server_urls.
        """
        return self.__server_urls

    @server_urls.setter
    def server_urls(self, value):
        """
        Setter method to set the value of self.server_urls.
        """
        self.__server_urls = value

        # --------------------------------------- Start App ----------------------------------------


# scraper = PageJaunesScraper()


# for url in client_urls[:1]:
#     scraper.add_base_url(url["url"], params=url.get("params"), limit=url.get("limit"))
# print(scraper.run())
