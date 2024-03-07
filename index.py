from seleniumbase import SB
import json
import base64
from seleniumbase import BaseCase
import time

def decode_link(attribute_link) :
    print("[1] :",attribute_link)
    #?---------------// Decode URL \\---------------
    # Parse the JSON string
    data_dict = json.loads(attribute_link)
    print("[2] :",data_dict)
    # Extract the URL and decode it
    encoded_url = data_dict['url']
    print("[3] :",encoded_url)
    decoded_url = base64.b64decode(encoded_url).decode('utf-8')
    print("[4] :",decoded_url)
    #? ---------------------------------------------
    return {"attr":attribute_link,"encoded_url":encoded_url, "decoded_url":decoded_url}

def verify_success(sb):
    sb.sleep(1)

def Handle_switch_link(sb,url) :
    print("\n",url)
    sb.open(url)

    #!---------------------------- Title ----------------------------
    if sb.is_element_visible('div.header-main-infos h1.noTrad'):
        title = sb.get_text('div.header-main-infos h1.noTrad').splitlines()[0]
        print("Title: ",title)
    #!---------------------------- Activite ----------------------------
    if sb.is_element_visible('span.activite'):
        activite = sb.get_text('span.activite')
        print("Activite: ",activite)
    #!---------------------------- Rank ----------------------------
    if sb.is_element_visible('span.note_moyenne'):
        rank = sb.get_text('span.note_moyenne')
        print("Rank: ",rank)
    #!---------------------------- Avis ----------------------------
    if sb.is_element_visible('span.bi-rating'):
        avis = sb.get_text('span.bi-rating')
        print("Avis: ",avis)
    #!---------------------------- Adress ----------------------------
    if sb.is_element_visible('div.address-container span.noTrad'):
        adress = sb.get_text('div.address-container span.noTrad')
        print("Adress: ",adress)
    if sb.is_element_visible('div.lvs-container span.value'):
        website = sb.get_text('div.lvs-container span.value')
        print("Website: ",website)
    #!---------------------------- Horaires ----------------------------
    if sb.is_element_visible('ul.liste-horaires-principaux'):
        horaires_elements = sb.find_elements('li.horaire-ouvert')
        list_horaires = []
        for index, horaire_element in enumerate(horaires_elements) :
            if sb.is_element_visible(f'li.horaire-ouvert:nth-child({index+1})'):
                day = sb.get_text(f'li.horaire-ouvert:nth-child({index+1}) p.jour')
                horaire = sb.get_text(f'li.horaire-ouvert:nth-child({index+1}) p.liste')
                list_horaires.append({"jour":day,"horaire":horaire})
        print("Horaires: ",list_horaires)
    #!---------------------------- Réseaux Sociaux ----------------------------
    if sb.is_element_visible('div.bloc-info-sites-reseaux ul.clearfix'):
        links_elements = sb.find_elements('ul.clearfix li.premiere-visibilite')
        list_links = []

        for index, link_element in enumerate(links_elements) :
            if sb.is_element_visible(f'ul.clearfix li.premiere-visibilite:nth-child({index+1}) a.pj-link') :
                href_link = sb.get_attribute(f'ul.clearfix li.premiere-visibilite:nth-child({index+1}) a.pj-link', 'href')
                if(href_link!="#") :
                    list_links.append(href_link)
                else :
                    attribute_link = sb.get_attribute(f'ul.clearfix li.premiere-visibilite:nth-child({index+1}) a.pj-link', 'data-pjlb')
                    list_links.append(decode_link(attribute_link))
        print("Réseaux Sociaux: ",list_links)

    if sb.is_element_visible('div.zone-fantomas a.hidden-phone'):
        # sb.click("a.hidden-phone")
        print("Phone Container success")

        # r = requests.get(url) 
        # soup = BeautifulSoup(r.content, 'html5lib') # If this line causes an error, run 'pip install html5lib' or install html5lib 
        # print(soup.prettify()) 
        # print(sb.get_page_source())
        # table = soup.find('div', attrs = {'id':'all_quotes'})


    if sb.is_element_visible('div.num-container'):
        print("Phone success")
        phone = sb.get_text('div.num-container span.coord-numero-inscription')
        print("Phone: ",phone)



def passCloudFareVerification() :
        try:
            verify_success(sb)
        except Exception:
            if sb.is_element_visible('input[value*="Verify"]'):
                sb.click('input[value*="Verify"]')
            elif sb.is_element_visible('iframe[title*="challenge"]'):
                sb.switch_to_frame('iframe[title*="challenge"]')
                sb.click('span.mark')
                return True
            else:
                passCloudFareVerification()
        try:
            verify_success(sb)
        except Exception:
            passCloudFareVerification()
    
    


with SB(uc_cdp=True, guest_mode=True,headless=False) as sb:
    sb.open('https://www.pagesjaunes.fr/annuaire/paris-75/restaurants')
    # sb.open('https://webcache.googleusercontent.com/search?q=cache:https://www.pagesjaunes.fr/annuaire/paris-75/restaurants')
# 
    # Handle Verification

    passCloudFareVerification()
    
    try:
        verify_success(sb)
    except Exception:
        if sb.is_element_visible('input[value*="Verify"]',timeout=10):
            sb.click('input[value*="Verify"]')
        elif sb.is_element_visible('iframe[title*="challenge"]',timeout=10):
            sb.switch_to_frame('iframe[title*="challenge"]')
            sb.click('span.mark')
        else:
            # passCloudFareVerification()
            raise Exception('Detected!')
        try:
            verify_success(sb)
        except Exception:
            raise Exception('Detected!')
        
    # Handle Coockies
    if sb.is_element_visible('span.didomi-continue-without-agreeing'):
            print('Done Cookie')
            #? <span class='didomi-continue-without-agreeing'>
            sb.click('span.didomi-continue-without-agreeing')

    # Get all card
    if sb.is_element_visible('ul.bi-list'):
        print('Done <ul> List\n')    #? <span class='didomi-continue-without-agreeing'>
        lists_li = sb.find_elements('ul.bi-list li.bi-generic')
        # lists = sb.find_elements('ul.bi-list li.bi-generic div.bi-header-title h3')
        lists_url = []
        for index, list in enumerate(lists_li):
            list_id = sb.get_attribute(f'li.bi-generic:nth-child({index+1})','id').split('-')[1]
            lists_url.append(f'https://www.pagesjaunes.fr/pros/{list_id}#zoneHoraires')
        for url in lists_url[:1] :
            Handle_switch_link(sb, url)




    # time.sleep(100)
    # Scraping data example:
    #! Let's say we want to scrape the names of restaurants from the page.
    # restaurant_names = sb.find_elements('span.denomination-links')

    # # Iterate through the elements and print their text (restaurant names)
    # for name in restaurant_names:
    #     print(name.text)





# BaseCase.main(__name__, __file__)

class MyTestClass(BaseCase):
    def test_swag_labs(self):
        self.open('https://www.pagesjaunes.fr/annuaire/paris-75/restaurants')
        time.sleep(12)
        print(self.get_page_source())
        


