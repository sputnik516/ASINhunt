import pandas as pd
import mwsPy3 as mws
import Creds as c
import time

upc_list = ('645397057123', # generates 2 responses
             '645397058120',
             '812028011377',
             '712536746061',
             '45454')  # item doesn't exist, correct UPC: 645397929628
upc_list2 = ('812028011377',
             '712536746061',
             '645397929628',
             '645397058120',
             '12354',
             '78',
             '645397057123')

upc_list3 = ('0712536746061', '645397929628', '33', '812028011377', '729294825501',#generates 1 response
            '645397057123', '0')  # generates 2 responses

asin_list = ('B004PRKD4W','B0063IV52U','B001GTT9TW','B00LOCX74O','B00LPDAA10','B006JWWE6Q','B006CPUY3K','B00LB46AEY')

upc_list4 = ('856097000757', '0712536746061', '645397929628', '33', '812028011377', '715757330804', '729294825501',
             '729294366806', '899126000854', '601209051482')
upc_list5 = ('856097000757')

class ASINHunt(object):

    def __init__(self, access_key, secret_key, account_id):
        self.access_key = access_key
        self.account_id = account_id
        self.secret_key = secret_key
        self.con_products = mws.Products(self.access_key, self.secret_key, self.account_id)

    def get_service_status(self):

        resp = self.con_products.get_service_status()

        return resp.dict_to_df()

    def match_products_for_id(self, marketplaceid, type, ids):

        df_final = pd.DataFrame()

        i = 0
        while i < len(ids):
            id_slice = ids[i: min(len(ids), i+5)]
            resp = self.con_products.get_matching_product_for_id(marketplaceid, type, id_slice)
            df = resp.dict_to_df()
            df_final = df_final.append(df, ignore_index=True)
            time.sleep(1)
            i += 5

        return df_final

    def get_lowest_priced_offers_for_asin(self, marketplaceid, ids, condition):

        df_final = pd.DataFrame()

        # If > 1 ASIN passed:
        if isinstance(ids, (list, tuple)):
            for item in ids:
                resp = self.con_products.get_lowest_priced_offers_for_asin(marketplaceid, item, condition)
                df = resp.dict_to_df()
                df_final = df_final.append(df, ignore_index=True)

        # If 1 ASIN passed:
        elif isinstance(ids, str):
            resp = self.con_products.get_lowest_priced_offers_for_asin(marketplaceid, ids, condition)
            df_final = resp.dict_to_df()

        else:
            raise ValueError('List of ASINs is not a \'tuple\', \'list\' or \'str\'')

        return df_final


a = ASINHunt(access_key=c.aws_key, secret_key=c.s_key, account_id=c.sellerID)
# s = a.match_products_for_id(c.marketplaceID_US, 'UPC', ids=upc_list2)
s = a.get_lowest_priced_offers_for_asin(c.marketplaceID_US, asin_list, 'New')

print(s)
s.to_csv('test.csv')














