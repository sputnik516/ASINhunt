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

    # Returns Buy Box price, if available:
    def getBuyBoxPrice(df, parsed_data):
        try:
            if isinstance(parsed_data.Summary.BuyBoxPrices.BuyBoxPrice.LandedPrice.Amount, str):
                df.set_value(0, 'BuyBoxPrice', parsed_data.Summary.BuyBoxPrices.BuyBoxPrice.LandedPrice.Amount)
        except (AttributeError, KeyError):
            try:
                for i in parsed_data.Summary.BuyBoxPrices.BuyBoxPrice:
                    try:
                        if i.condition == 'New':
                            df.set_value(0, 'BuyBoxPrice', i.LandedPrice.Amount)

                    # If there is only one Buy Box price:
                    except AttributeError:
                        df.set_value(0, 'BuyBoxPrice', parsed_data.Summary.BuyBoxPrices.BuyBoxPrice.LandedPrice.Amount)

            # If no Buy Box price is returned, leave blank:
            except KeyError:
                pass
        return df

    # Total Number of New FBA and MFN listings:
    def getFBAandMFNtotal(df, parsed_data):
        # If multiple offers are returned:
        for i in parsed_data.Summary.NumberOfOffers.OfferCount:
            try:
                if i.fulfillmentChannel == 'Amazon' and i.condition == 'new':
                    df.set_value(0, 'BuyBoxEligibleOffers_FBA', i.value)
                if i.fulfillmentChannel == 'Merchant' and i.condition == 'new':
                    df.set_value(0, 'BuyBoxEligibleOffers_Merch', i.value)

            except AttributeError:
                try:
                    if parsed_data.Summary.BuyBoxEligibleOffers.OfferCount.fulfillmentChannel == 'Amazon' and \
                                    parsed_data.Summary.BuyBoxEligibleOffers.OfferCount.condition == 'new':
                        df.set_value(0, 'BuyBoxEligibleOffers_FBA',
                                     parsed_data.Summary.BuyBoxEligibleOffers.OfferCount.value)
                    if parsed_data.Summary.BuyBoxEligibleOffers.OfferCount.fulfillmentChannel == 'Merchant' and \
                                    parsed_data.Summary.BuyBoxEligibleOffers.OfferCount.condition == 'new':
                        df.set_value(0, 'BuyBoxEligibleOffers_Merch',
                                     parsed_data.Summary.BuyBoxEligibleOffers.OfferCount.value)

                except AttributeError as err:
                    raise ValueError('Error in getFBAandMFNtotal.', err.args)

        return df

    # Get competing offer details, 20 max:
    def getOffers(df, parsed_data):
        # Offers: Up to 20 Offers may be returned
        # Creates new columns for each offer
        # If some data is not provided by Amazon, leaves that field blank
        # If 1 Offer is returned:
        if int(parsed_data.Summary.TotalOfferCount) == 1:
            try:
                df['Ofr_Cond1'] = parsed_data.Offers.Offer.SubCondition
            except KeyError:
                df['Ofr_Cond1'] = ''
            try:
                df['Ofr_FbPct1'] = parsed_data.Offers.Offer.SellerFeedbackRating.SellerPositiveFeedbackRating
            except KeyError:
                df['Ofr_FbPct1'] = ''
            try:
                df['Ofr_FbCt1'] = parsed_data.Offers.Offer.SellerFeedbackRating.FeedbackCount
            except KeyError:
                df['Ofr_FbCt1'] = ''
            try:
                df['Ofr_Price1'] = float(parsed_data.Offers.Offer.Shipping.Amount) + float(
                    parsed_data.Offers.Offer.ListingPrice.Amount)
            except KeyError:
                df['Ofr_Price1'] = ''
            try:
                df['Ofr_IsFBA1'] = parsed_data.Offers.Offer.IsFulfilledByAmazon
            except KeyError:
                df['Ofr_IsFBA1'] = ''
            try:
                df['Ofr_IsBuyBox1'] = parsed_data.Offers.Offer.IsBuyBoxWinner
            except KeyError:
                df['Ofr_IsBuyBox1'] = ''
            try:
                df['Ofr_IsFeatured1'] = parsed_data.Offers.Offer.IsFeaturedMerchant
            except KeyError:
                df['Ofr_IsFeatured1'] = ''

        # If > 1 Offer is returned:
        elif int(parsed_data.Summary.TotalOfferCount) > 1:
            for n, offer in enumerate(parsed_data.Offers.Offer):
                try:
                    df['Ofr_Cond' + str(n + 1)] = offer.SubCondition
                except KeyError:
                    df['Ofr_Cond' + str(n + 1)] = ''
                try:
                    df['Ofr_FbPct' + str(n + 1)] = offer.SellerFeedbackRating.SellerPositiveFeedbackRating
                except KeyError:
                    df['Ofr_FbPct' + str(n + 1)] = ''
                try:
                    df['Ofr_FbCt' + str(n + 1)] = offer.SellerFeedbackRating.FeedbackCount
                except KeyError:
                    df['Ofr_FbCt' + str(n + 1)] = ''
                try:
                    df['Ofr_Price' + str(n + 1)] = float(offer.Shipping.Amount) + float(offer.ListingPrice.Amount)
                except KeyError:
                    df['Ofr_Price' + str(n + 1)] = ''
                try:
                    df['Ofr_IsFBA' + str(n + 1)] = offer.IsFulfilledByAmazon
                except KeyError:
                    df['Ofr_IsFBA' + str(n + 1)] = ''
                try:
                    df['Ofr_IsBuyBox' + str(n + 1)] = offer.IsBuyBoxWinner
                except KeyError:
                    df['Ofr_IsBuyBox' + str(n + 1)] = ''
                try:
                    df['Ofr_IsFeatured' + str(n + 1)] = offer.IsFeaturedMerchant
                except KeyError:
                    df['Ofr_IsFeatured' + str(n + 1)] = ''

        return df

    # Create blank DataFrame:
    cols = ['ASIN', 'TimeOfOfferChange', 'BuyBoxPrice', 'BuyBoxEligibleOffers_Merch',
            'BuyBoxEligibleOffers_FBA']
    df = pd.DataFrame(columns=cols)

    df.set_value(0, 'ASIN', parsed_data.Identifier.ASIN)
    df.set_value(0, 'TimeOfOfferChange', parsed_data.Identifier.TimeOfOfferChange)

    # Get Buy Box price, add to DF:
    df = getBuyBoxPrice(df, parsed_data)

    # Get total number of FBA and MFN offers, add to DF:
    df = getFBAandMFNtotal(df, parsed_data)

    # Get offers (up to 20 returned by API):
    df = getOffers(df, parsed_data)

    return df
