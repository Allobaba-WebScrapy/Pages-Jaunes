from seleniumbase import SB
from selenium.common.exceptions import TimeoutException
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from data import client_urls
import json
import base64


class PageJaunesScraper:
    def __init__(self):
        self.__server_urls = []
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
            if self.sb.wait_for_element_visible('input[value*="Verify"]', timeout=10):
                self.sb.click('input[value*="Verify"]')
            elif self.sb.wait_for_element_visible(
                'iframe[title*="challenge"]', timeout=10
            ):
                self.sb.switch_to_frame('iframe[title*="challenge"]')
                self.sb.click("span.mark")
            else:
                self.passCloudFareVerification()
        try:
            self.verify_success()
        except Exception:
            self.passCloudFareVerification()

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
                if self.sb.is_element_visible(
                    f"li.bi:nth-child({index+1}) div.bi-ctas div.number-contact > span:last-child"
                ):
                    phone_text = self.sb.get_text(
                        f"li.bi:nth-child({index+1}) div.bi-ctas div.number-contact > span:last-child"
                    )
                    if self.data[-1]["genre"] == self.classify_number(phone_text):
                        print("Telephone genre found: ", phone_text)
                        return {True, phone_text}
                    else:
                        return {False, phone_text}
            else:
                return {False, "No phone number found!"}
        except:
            print("Telephone not found within the given time.")

    def get_card_info(self, index):
        #!---------------------------- Title ----------------------------
        title = self.get_simple_info(
            f"li.bi:nth-child({index+1}) div.bi-header-title h3"
        )
        #!---------------------------- Activitée ----------------------------
        activite = self.get_simple_info(
            f"li.bi:nth-child({index+1}) span.bi-activity-unit.small"
        )
        #!---------------------------- Adress ----------------------------
        adress = self.get_simple_info(
            f"li.bi:nth-child({index+1}) div.bi-address.small a"
        ).replace(" Voir le plan", "")
        return {title, activite, adress}

    def scrap_page(self, base_url):
        print("Page: ", base_url)
        """
        Main application logic for scraping data from the base URL.
        """
        self.sb.open(base_url)
        if self.sb.is_element_visible("span.didomi-continue-without-agreeing"):
            self.sb.click("span.didomi-continue-without-agreeing")
        else:
            pass
        # if self.sb.is_element_visible("span#SEL-compteur"):
        #     compteur = self.sb.get_text("span#SEL-compteur")
        #     print(self.get_limits_pages(compteur))
        try:
            if self.sb.wait_for_element_visible("span#SEL-nbresultat", timeout=1):
                print(self.sb.get_text("span#SEL-nbresultat"))
                # ----------------------------------------------------------------
                if self.sb.is_element_visible("ul.bi-list"):
                    lists_li = self.sb.find_elements("ul.bi-list li.bi")
                    for index, list in enumerate(lists_li):
                        isValid, phone = self.check_valid_card(index)
                        if isValid:
                            list_id = self.sb.get_attribute(
                                f"li.bi:nth-child({index+1})", "id"
                            ).split("-")[1]
                            title, activite, adress = self.get_card_info(index)
                            self.data[-1]["pages"][-1]["cards"].append(
                                {
                                    "card_id": list_id,
                                    "card_url": f"https://www.pagesjaunes.fr/pros/{list_id}#zoneHoraires",
                                    "info": {
                                        "title": title,
                                        "activite": activite,
                                        "adress": adress,
                                        "phone": phone,
                                    },
                                }
                            )
                            yield self.data[-1]["pages"][-1]["cards"][-1]
        except TimeoutException:
            print("Page not found!")

    def run(self):
        """
        Starts the application by initializing the web driver and executing the scraping process.
        """
        with SB(
            uc_cdp=True,
            guest_mode=True,
            headless=False,
            undetected=True,
            timeout_multiplier=1,
        ) as sb:
            self.sb = sb
            self.sb.set_window_size(600, 1200)
            self.sb.open("https://www.pagesjaunes.fr")

            #! Try to pass the CloudFare verification process
            # try:
            #     if self.sb.wait_for_element_visible("input.checkbox", timeout=10):
            #         print("Verify found!")
            #         self.sb.click("input.checkbox")
            # except:
            #     print("Verify not found!")
            #     pass

            # Handle cookies
            if self.sb.is_element_visible("span.didomi-continue-without-agreeing"):
                print("Cookie found!")
                self.sb.click("span.didomi-continue-without-agreeing")

                # Loop through provided URLs and iterate over each to navigate through each subsequent page.
                for server_url in self.__server_urls:
                    try:
                        url = server_url["url"]
                        start_limit = int(server_url.get("start-limit"))
                        end_limit = int(server_url.get("end-limit"))
                        genre = server_url.get("genre")
                        self.data.append({"base_url": url, "genre": genre, "pages": []})
                        for pageNumber in range(start_limit, start_limit + end_limit):
                            page_url = self.add_arguments_to_url(url, page=pageNumber)
                            self.data[-1]["pages"].append(
                                {"page": pageNumber, "page_url": page_url, "cards": []}
                            )
                            print("|__Next Page__|:", page_url)
                            yield from self.scrap_page(page_url)
                    except Exception as e:
                        print("Error Run:", e)
                    print("__" * 70)
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
