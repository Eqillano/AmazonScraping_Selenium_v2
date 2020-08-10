from amazon_config import (
    get_web_driver_options,
    get_chrome_web_driver,
    set_ignore_certificate_error,
    set_browser_as_incognito,
    #sset_automation_as_head_less,
    NAME,
    CURRENCY,
    FILTERS,
    BASE_URL,
    DIRECTORY
)
import json
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
import time
from datetime import datetime

class GenerateReport:
    def __init__(self,file_name,filters,base_link,currency,data):
        self.data = data
        self.file_name = file_name
        self.filters = filters
        self.base_link = base_link
        self.currency = currency

        report = {
            'title':self.file_name,
            'date':self.get_now(),
            'best_item':self.get_best_item(),
            'currency':self.currency,
            'filters':self.filters,
            'base_link':self.base_link,
            'products':self.data
        }
        print('Creating report...')
        with open(f'{DIRECTORY}/{file_name}.json', 'w') as f:
            json.dump(report, f)
        print("Done...")
        



    def get_best_item(self):
        try:
            return sorted(self.data,key=lambda k : ['price'])[0]
        except Exception as e:
            print(e)
            print('Problem with sorting items')
            return None


    def get_now(self):
        now = datetime.now()
        return now.strftime("%d/%m/%Y %H:%M:%S")

class AmazonAPI:
    def __init__(self,search_term,filters,base_url,currency):
        self.base_url = base_url
        #self.filters = filters
        self.currency = currency
        self.search_term = search_term
        options = get_web_driver_options()
        set_ignore_certificate_error(options)
        set_browser_as_incognito(options)
        self.driver = get_chrome_web_driver(options)
        self.price_filter = f"&rh=p_36%3A{filters['min']}00-{filters['max']}00"

    def run(self):
        print('Starting script...')
        print("Looking for {} products...".format(self.search_term))
        links = self.get_products_links()
        time.sleep(1)
        if not links:
            print('Stopped script.')
            return 
        print('Got {} links to products...')
        print('Getting info about products')
        products = self.get_products_info(links)
        print("Got info about {} products....".format(len(products)))
        self.driver.quit()


    def get_products_info(self,links):
        asins = self.get_asins(links)
        products = []
        for asin in asins[:10]:
            product = self.get_single_product_info(asin)
            if product:
                products.append(product)
        return products


    def get_single_product_info(self,asin):
        print("Product: {} - getting data...".format(asin))
        product_short_url = self.shorten_url(asin)
        self.driver.get("{}?language=en_GB".format(product_short_url))
        time.sleep(2)
        title = self.get_title()
        seller = self.get_seller()
        price = self.get_price()
        if title and seller and price:
            product_info = {
                'asin':asin,
                'url':product_short_url,
                'title':title,
                'seller':seller,
                'price':price
            }
            return product_info
        return None


    def get_title(self):
        try:
            return self.driver.find_element_by_id('productTitle').text
        except Exception as e:
            print(e)
            return None

    def get_seller(self):
        try:
            return self.driver.find_element_by_id('bylineInfo').text
        except Exception as e:
            print(e)
            return None

    def get_price(self):
        price = None
        try:
            price = self.driver.find_element_by_id('priceblock_ourprice').text
            price = self.convert_price(price)
        except NoSuchElementException:
            try:
                availability = self.driver.find_element_by_id('availability').text
                if 'Available' in availability:
                    price = self.driver.find_element_by_class_name('olp-padding-right').text
                    price = price[price.find(self.currency):]
                    price = self.convert_price(price)
            except Exception as e:
                print(e)
                print(f"Can't get price of a product - {self.driver.current_url}")
                return None
        except Exception as e:
            print(e)
            print(f"Can't get price of a product - {self.driver.current_url}")
            return None
        return price


    def convert_price(self, price):
        price = price.split(self.currency)[1]
        try:
            price = price.split("\n")[0] + "." + price.split("\n")[1]
        except:
            Exception()
        try:
            price = price.split(",")[0] + price.split(",")[1]
        except:
            Exception()
        return float(price)
        

    
    def shorten_url(self,asin):
        return self.base_url + 'dp/' + asin
    
    def get_asins(self,links):
        return [self.get_asin(link) for link in links]

    def get_asin(self,product_link):
        return product_link[product_link.find('/dp/') + 4:product_link.find('/ref')]

    def get_products_links(self):
        self.driver.get(self.base_url)
        element = self.driver.find_element_by_xpath('//*[@id="twotabsearchtextbox"]')
        element.send_keys(self.search_term)
        element.send_keys(Keys.ENTER)
        self.driver.get(f'{self.driver.current_url}{self.price_filter}')
        time.sleep(2)
        result_list = self.driver.find_elements_by_class_name('s-result-list')

        links = []

        try:
            results = result_list[0].find_elements_by_xpath(
                "//div/span/div/div/div[2]/div[2]/div/div[1]/div/div/div[1]/h2/a")
            links = [link.get_attribute('href') for link in results]
            return links

        except Exception as e:
            print("Didn't get any products...")
            print(e)
            return links


if __name__ == '__main__':
    print('fuckoff')
    amazon = AmazonAPI(NAME,FILTERS,BASE_URL,CURRENCY)
    print(amazon.price_filter)
    data = amazon.run()
    GenerateReport(NAME,FILTERS,BASE_URL,CURRENCY,data)
    print(data)