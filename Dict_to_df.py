import pandas as pd

# -Added by Alex:
def GetServiceStatusResult(parsed_data):

    df = pd.DataFrame(columns=['Status', 'Timestamp'], index=[0])
    df['Status'] = parsed_data.Status
    df['Timestamp'] = parsed_data.Timestamp

    return df

def GetMatchingProductForIdResult(parsed_data):

    def fillCols(df, row, item, IsMultASIN):
        df.set_value(row, 'IsMultASIN', IsMultASIN)
        df.set_value(row, 'Status', item.status)
        df.set_value(row, 'Id', item.Id)
        df.set_value(row, 'IdType', item.IdType)
        df.set_value(row, 'ASIN', item.Products.Product.Identifiers.MarketplaceASIN.ASIN)
        df.set_value(row, 'BrandAmazon', item.Products.Product.AttributeSets.ItemAttributes.Brand)
        df.set_value(row, 'Title', item.Products.Product.AttributeSets.ItemAttributes.Title)
        df.set_value(row, 'ProductGroup', item.Products.Product.AttributeSets.ItemAttributes.ProductGroup)
        df.set_value(row, 'ImgURL', item.Products.Product.AttributeSets.ItemAttributes.SmallImage.URL)
        df.set_value(row, 'PkgHeight',
                     item.Products.Product.AttributeSets.ItemAttributes.PackageDimensions.Height.value)
        df.set_value(row, 'PkgWidth',
                     item.Products.Product.AttributeSets.ItemAttributes.PackageDimensions.Width.value)
        df.set_value(row, 'PkgLength',
                     item.Products.Product.AttributeSets.ItemAttributes.PackageDimensions.Length.value)
        df.set_value(row, 'PkgWeight',
                     item.Products.Product.AttributeSets.ItemAttributes.PackageDimensions.Weight.value)
        df.set_value(row, 'PackageQuantity', item.Products.Product.AttributeSets.ItemAttributes.PackageQuantity)

        return df

    # Create blank DataFrame:
    cols = ['Status', 'Id', 'IdType', 'IsMultASIN', 'ASIN', 'BrandAmazon', 'Title',
                               'ProductGroup', 'ImgURL', 'PkgHeight', 'PkgWidth', 'PkgLength', 'PkgWeight',
                               'PackageQuantity']
    df = pd.DataFrame(columns=cols)

    # Create blank DataFrame to be used for items w/ Multiple Results,
    # and later merge with df:
    df_multi = pd.DataFrame(columns=cols)

    for i, item in enumerate(parsed_data):

        # Only items that were found by Amazon
        # AND where UPC only matches one ASIN
        # For UPC's with multiple ASIN's 'item.Products.Product' is a list:
        print(item.Id)
        if item.status == 'Success' and not isinstance(item.Products.Product, list):
            try:
                df = fillCols(df, i, item, False)
            except:
                raise ValueError('Error in item:', item.Id, item)

        # Only items that were found by Amazon
        # AND where UPC matches multiple ASIN's
        # For UPC's with multiple ASIN's 'item.Products.Product' is a list:
        elif item.status == 'Success' and isinstance(item.Products.Product, list):

            for n, subItem in enumerate(item.Products.Product):
                df_multi.set_value(n, 'IsMultASIN', True)
                df_multi.set_value(n, 'Status', item.status)
                df_multi.set_value(n, 'Id', item.Id)
                df_multi.set_value(n, 'IdType', item.IdType)
                df_multi.set_value(n, 'ASIN', subItem.Identifiers.MarketplaceASIN.ASIN)
                df_multi.set_value(n, 'BrandAmazon', subItem.AttributeSets.ItemAttributes.Brand)
                df_multi.set_value(n, 'Title', subItem.AttributeSets.ItemAttributes.Title)
                df_multi.set_value(n, 'ProductGroup', subItem.AttributeSets.ItemAttributes.ProductGroup)
                df_multi.set_value(n, 'ImgURL', subItem.AttributeSets.ItemAttributes.SmallImage.URL)
                try:
                    df_multi.set_value(n, 'PkgHeight', subItem.AttributeSets.ItemAttributes.PackageDimensions.Height.value)
                except KeyError:
                    df_multi.set_value(n, 'PkgHeight', '')
                try:
                    df_multi.set_value(n, 'PkgWidth', subItem.AttributeSets.ItemAttributes.PackageDimensions.Width.value)
                except KeyError:
                    df_multi.set_value(n, 'PkgWidth', '')
                try:
                    df_multi.set_value(n, 'PkgLength', subItem.AttributeSets.ItemAttributes.PackageDimensions.Length.value)
                except KeyError:
                    df_multi.set_value(n, 'PkgLength', '')
                try:
                    df_multi.set_value(n, 'PkgWeight', subItem.AttributeSets.ItemAttributes.PackageDimensions.Weight.value)
                except KeyError:
                    df_multi.set_value(n, 'PkgWeight', '')
                try:
                    df_multi.set_value(n, 'PackageQuantity', subItem.AttributeSets.ItemAttributes.PackageQuantity)
                except KeyError:
                    df_multi.set_value(n, 'PackageQuantity', '')

        # Items that were NOT found by Amazon:
        elif item.status == 'ClientError':
            try:
                df.set_value(i, 'Status', item.status)
                df.set_value(i, 'Id', item.Id)
                df.set_value(i, 'IdType', item.IdType)
                df.set_value(i, 'IsMultASIN', False)

            except:
                raise ValueError('Error in item:', item.Id, item)


    #Combine df and df_multi:
    return pd.concat([df, df_multi], ignore_index=True)

def GetLowestPricedOffersForASINResult(parsed_data):
    # Create blank DataFrame:
    cols = ['ASIN', 'TimeOfOfferChange', 'CtFBA', 'CtMerch', 'BuyBoxPrice', 'BuyBoxEligibleOffers_Merch',
            'BuyBoxEligibleOffers_FBA']
    df = pd.DataFrame(columns=cols)

    df.set_value(0, 'ASIN', parsed_data.Identifier.ASIN)
    df.set_value(0, 'TimeOfOfferChange', parsed_data.Identifier.TimeOfOfferChange)

    # Buy box price, New:
    for i in parsed_data.Summary.BuyBoxPrices.BuyBoxPrice:
        if i.condition == 'New':
            df.set_value(0, 'BuyBoxPrice', i.LandedPrice.Amount)

    # Total Number of New FBA and MFN listings:
    for i in parsed_data.Summary.NumberOfOffers.OfferCount:
        if i.fulfillmentChannel =='Amazon' and i.condition =='new':
            df.set_value(0, 'CtFBA', i.value)
        if i.fulfillmentChannel == 'Merchant' and i.condition == 'new':
            df.set_value(0, 'CtMerch', i.value)

    # Number of New FBA and MFN listings eligible for the Buy Box:
    for i in parsed_data.Summary.BuyBoxEligibleOffers.OfferCount:
        if i.fulfillmentChannel == 'Amazon' and i.condition == 'new':
            df.set_value(0, 'BuyBoxEligibleOffers_FBA', i.value)
        if i.fulfillmentChannel == 'Merchant' and i.condition == 'new':
            df.set_value(0, 'BuyBoxEligibleOffers_Merch', i.value)

    # Offers. Up to 20 Offers may be returned:
    for n, offer in enumerate(parsed_data.Offers.Offer):
        df['Ofr_Cond' + str(n)] = offer.SubCondition
        df['Ofr_FbPct' + str(n)] = offer.SellerFeedbackRating.SellerPositiveFeedbackRating
        df['Ofr_FbCt' + str(n)] = offer.SellerFeedbackRating.FeedbackCount
        df['Ofr_Price' + str(n)] = float(offer.Shipping.Amount) + float(offer.ListingPrice.Amount)
        df['Ofr_IsFBA' + str(n)] = offer.IsFulfilledByAmazon
        df['Ofr_IsBuyBox' + str(n)] = offer.IsBuyBoxWinner
        df['Ofr_IsFeatured' + str(n)] = offer.IsFeaturedMerchant






    print(df)
