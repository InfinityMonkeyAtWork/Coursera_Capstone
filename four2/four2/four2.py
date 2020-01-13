import os
from datetime import date
from geopy.geocoders import Nominatim 
import requests
from pandas.io.json import json_normalize

def getClient():
	# function docstring
    """
    this function gets client ID and secret from a foursquare file
    and combines them into a string that is usable in URLs that need
    to be assembled in order to send search queries to foursquare.
    requires:
    (an account on https://foursquare.com/)
    import os
    use like so:
    client = four2.getClient()
    """
    # gets the developer account details, i.e. client ID and client secret from file
    path = 'C:\\Users\\' + os.getlogin() + '\\OneDrive\\software\\16\\client.txt'
    with open(path) as f:
        clientText = f.readlines()
    clientID = clientText[0][:-1]
    clientSecret = clientText[1]
    # create the client part of the URI
    client = 'client_id=' + clientID + '&client_secret=' + clientSecret
    return client



def getDateForVersion():
	# function docstring
    """
    gives today's date in a format that is required for the version variable in a foursquare query.
    requires:
    from datetime import date
    use like so:
    version = foursquare.getDateForVersion()
    """
    today = date.today()
    return today.strftime("%Y%m%d")



def getLatLng(address):
	# function docstring
    """
    this will get latitude and longitude of a certain address.
    if no location can be found for the address function will return 'None'.
	requires:
    from geopy.geocoders import Nominatim 
    use like so:
    address = '102 North End Ave, New York, NY'
    lat, lng = four2.getLatLng(address)
    """
    geolocator = Nominatim(user_agent = "foursquare_agent")
    location = geolocator.geocode(address)
    if location is not None:
        lat = location.latitude
        lng = location.longitude
        return lat, lng
    else:
        return None
		



def infoLocation(baseURL, client, group, version, lat, lng, limit, meters, query):
    # function docstring
    """
    this function builds a URL to allow searching foursquare (method=get)
    run foursquare.getClient function to get the client information, i.e. ID and secret (client).
    group could be "venues", "tips", "users".
    version is simply a date which selects the last version before e.g. "20181018" (18th Oct 2018).
    if version is "-1" then today's date will be used.
    lat and lng are latitude and longitude of the location around which you want to search/explore.
    limit is the maximum number of results. meters is the search range in meters.
    query is the actual search query/ string you would like to send to foursquare (endpoint=search).
    if query is "-1", then endpoint=explore, if query is "0", then endpoint=trending.
    in both of the above cases we get information on places around location. explore is more general.
    trending gives info on places with the highest foottraffic at the time the query is sent.
    this will return a .json file.
    requires:
    import requests
    from datetime import date
    use like so:
    results = four2.infoLocation(baseURL, client, group, version, lat, lng, limit, meters, query)
    """
    # check if endpoint should be search or explore
    if query == -1:
        endpoint = 'explore'
    elif query == 0:
        endpoint = 'trending'
    else:
        endpoint = 'search'
    # get today's date for the version variable if it is set to -1
    if version == -1:
        version = getDateForVersion()
    # now we can put together the URL to send for our search query
    URL = baseURL + '/' + group + '/' + endpoint + '?' + client \
        + '&v=' + version + '&ll=' + str(lat) + ',' + str(lng) \
        + '&radius=' + str(meters) + '&limit=' + str(limit)
    if query!=-1:
        # search -> append the search query
        URL = URL + '&query=' + query
    results = requests.get(URL).json()
    return results



def getVenueCategory(row):
	# function docstring
    """
    function that extracts the category of the venue,
	i.e. one row of data within a pandas dataframe
    """
    try:
        categories_list = row['categories']
    except:
        categories_list = row['venue.categories']
        
    if len(categories_list) == 0:
        return None
    else:
        return categories_list[0]['name']


    
def infoUniqueID(baseURL, client, group, version, unqID):
    # function docstring
    """
    get information about a user or venue from foursquare.
    group could be "users" or "venues"
    endpoint could be "", "" or ""
    unqID is the users or venues unique identifier.
    requires:
    import requests
    from datetime import date
    use like so:
    result = four2.infoUniqueID(baseURL, client, group, endpoint, version, unqID)
    """
    # get today's date for the version variable if it is set to -1
    if version == -1:
        version = getDateForVersion()
    #
    URL = baseURL + '/' + group + '/' + unqID + '?' + client + \
        '&v=' + version
    result = requests.get(URL).json()
    return result



def getVenueRating(result):
	# function docstring
    """
    this function returns the rating of a foursquare search result.
    output type is float if place is rated and string if there is no rating.
    use like so:
    rating = four2.getVenueRating(result)
    """
    try:
        rating = result['response']['venue']['rating']
    except:
        rating = 'venue not rated yet.'
    return rating
	
	
	
def json2pdDF(results, colFilter):
    # function docstring
    """
    this function takes 'results' from a four2.infoLocation query, i.e. a .json file
    and converts it into a pandas data frame containing the columns defined in 'colFilter'
    requires:
    from pandas.io.json import json_normalize
    use like so:
    df = four2.json2pdDF(results, colFilter = ['venue.name', \
        'venue.categories', 'venue.location.lat', 'venue.location.lng'])
    """
    # 
    venues = results['response']['groups'][0]['items']
    # flatten JSON
    nearbyVenues = json_normalize(venues)
    # filter columns
    nearbyVenues = nearbyVenues.loc[:, colFilter]
    # filter the category for each row
    nearbyVenues['venue.categories'] = nearbyVenues.apply(getVenueCategory, axis=1)
    # clean columns
    nearbyVenues.columns = [col.split(".")[-1] for col in nearbyVenues.columns]
    # return result which is a pandas dataframe
    return nearbyVenues
	
	
	
def getNearbyVenues(baseURL, client, names, latitudes, longitudes, meters=500):
    # function docstring
    """
    explore a list of names (plus lat and lng) and get nearby venues as a pandas dataframe.
    the dataframe contains nearby venues for each entry in the name, lat, lng data set.
    supply baseURL(usually 'https://api.foursquare.com/v2/') and client (from getClient()).
    meters is the search radius in meters.
    requires:
    import pandas as pd
    use like so:
    nearby_venues = four2.getNearbyVenues(baseURL, client, names, latitudes, longitudes, meters)
    """
    # define parameters for the explore
    group = 'venues'
    version = -1
    limit = 100
    query = -1
    venues_list=[]
    for name, lat, lng in zip(names, latitudes, longitudes):
        print(name)
        results = infoLocation(baseURL, client, group, version, lat, lng, limit, meters, query)
        #
        results = results["response"]['groups'][0]['items']
        # return only relevant information for each nearby venue
        venues_list.append([(
            name, 
            lat, 
            lng, 
            v['venue']['name'], 
            v['venue']['location']['lat'], 
            v['venue']['location']['lng'],  
            v['venue']['categories'][0]['name']) for v in results])
    #
    nearby_venues = pd.DataFrame([item for venue_list in venues_list for item in venue_list])
    #
    nearby_venues.columns = ['Neighborhood', 
                  'Neighborhood Latitude', 
                  'Neighborhood Longitude', 
                  'Venue', 
                  'Venue Latitude', 
                  'Venue Longitude', 
                  'Venue Category']
    #
    return(nearby_venues)