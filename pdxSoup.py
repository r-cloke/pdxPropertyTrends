from bs4 import BeautifulSoup
from pyzillow.pyzillow import ZillowWrapper, GetDeepSearchResults
import urllib, urllib2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as dateformat
import numpy as np
import datetime
from geopy.geocoders import Nominatim
import subprocess

#things to fix
#histomatic broke
#call R script
#write to blog directly
#heat map

def listingScraper(soup,fout):
    listing = soup.find_all("section", itemprop="address", itemscope="", itemtype="http://schema.org/PostalAddress")
    
    for i in range(len(listing)):
        #check on this try statement later
        try:
            prop = str(listing[i].get_text().strip())
        except:
            break
        prop= prop.split('\n')

        for space in prop:
            if space == '':
                prop.remove(space)

        address=''
        whitespace = True
        for i in range(len(prop[1])):
            if prop[1][i] == ' ' and whitespace == True:
                whitespace=True
            else:
                address = address + prop[1][i]
                whitespace=False
        if prop[9] == 'Map':
            fout.write(prop[0] +';'+address+';'+prop[8]+'\n')
        else:
            fout.write(prop[0] +';'+address+';'+prop[9]+'\n')
    print 'writing properties for sale to file'

def zEstimate(pdxPath):
    zillow_data = ZillowWrapper('X1-ZWz19q3ualw00b_anh8k')
    overvalue = float(0.0)
    relOverValue=float(0.0)
    geolocator = Nominatim()

    #initial values
    worked=0
    failed=0
    price=''
    street=''
    zipcode=''
    with open(pdxPath, 'wb') as pdx:
        pdx.write('Listing price ; Address ; Zipcode ; zEstimate ; Overvalue ; %overvalued'+ '\n')
        with open('pdxSoup.txt', 'rb')as fin:
            fin.readline()
            for aline in fin:
                try:
                    #shouldn't group zestimate and address locator together
                    price = aline.split(';')[0].strip('$')
                    price = float(price.strip(',').replace(',',''))

                    street = aline.split(';')[1]
                    zipcode = aline.split(';')[2].strip('\n')
                    deep_search_response = zillow_data.get_deep_search_results(street, zipcode)
                    result = GetDeepSearchResults(deep_search_response).zestimate_amount

                    overvalue = price - float(result)
                    #relOverValue = (overvalue / price)*100
                    relOverValue = 100 - ((float(result) / price)*100)
                    
                    if '#' in street:
                        stop = street.index('#')
                        street = street[:stop]
                        
                    
                    location = geolocator.geocode(street)
                    lat = location.latitude
                    lon = location.longitude
                    
                    if 44 < lat < 46 and -123 < lon < -121:
                        pdx.write(str(price)+';'+street+';'+zipcode+';'+str(result).strip('\n')+';'+str(overvalue)+';'+str(relOverValue)+
                              ';'+str(lat)+';'+str(lon)+'\n')
                        worked = worked + 1
                    else:
                        pdx.write(str(price)+';'+street+';'+zipcode+';'+str(result).strip('\n')+';'+str(overvalue)+';'+str(relOverValue)+'\n')
                        failed = failed + 1
                    
                    
                except:
                    failed = failed +1
                    pdx.write(str(price)+';'+street+';'+zipcode+';'+'zEstimate unavailable'+'\n')

                
    print str(worked)+' addresses were successfully converted to lat,lon \n' + str(failed) +' addresses could not be converted'                   
    fin.close()
    pdx.close()
    
    with open(pdxPath,'rb') as fileIn:
        with open('coords.csv','wb') as coordsFile:
            coordsFile.write('lat'+','+'lon'+','+'Percent_Over_Valued'+'\n')
            for aline in fileIn:
                if len(aline.split(';'))==8 and (-50 < float(aline.split(';')[5]) < 50):
                    coordsFile.write(aline.split(';')[6]+','+aline.split(';')[7].strip('\n')+','+aline.split(';')[5]+'\n')
    fileIn.close()
    coordsFile.close()
    
def histoMatic(pdxPath):
    dataLst=[]
    with open(pdxPath, 'rb') as fin:
        fin.readline()
        for aline in fin:
            if aline.split(';')[3].strip('\n') != 'zEstimate unavailable':
                dataLst.append(float(aline.split(';')[5].strip('\n')))
        fin.close()
    data = np.array(dataLst)
    mu = "{:10.2f}".format(np.mean(data))
    std = "{:10.2f}".format(np.std(data))
    med = "{:10.2f}".format(np.median(data))

    
    plt.hist(data, bins=50, facecolor='g', alpha=0.75)
    plt.xlabel('% Overvalued')
    plt.ylabel('Number of Properties')
    plt.axis([-70,100, 0,250])
    plt.title('Over/Under Valuation of Properties in Portland')
    plt.text(-50,200, 'Mean = ' + mu+'\n'+'Std dev = '+std+'\n'+'Median = '+med)
    plt.savefig(pdxPath+'.png')
    plt.close()

    #update trends file
    dateLst=[]
    meanLst=[]
    medianLst=[]
    with open('pdxTrends.txt', 'rb') as trendin:
        trendin.readline()
        for aline in trendin:
            dateLst.append(aline.split(';')[0])
            meanLst.append(aline.split(';')[1])
            medianLst.append(aline.split(';')[3])

        newline = today+';'+str(mu.strip())+';'+str(std.strip())+';'+str(med.strip())+'\n'        
        if today not in dateLst:
            with open('pdxTrends.txt', 'a') as trends:
                trends.write(newline)
                dateLst.append(today)
                meanLst.append(mu.strip())
                medianLst.append(med.strip())
            trends.close()
        
    x = dateformat.datestr2num(dateLst)
    y = np.array(meanLst)
    
    plt.plot_date(x,y, 'b-')
    plt.autoscale(enable=True, axis='y')
    plt.savefig('trends.png')
    plt.close()           
    
with open('pdxSoup.txt', 'wb') as fout:
    url = urllib2.urlopen("http://www.trulia.com/for_sale/Portland,OR/100000p_price/")
    content = url.read()
    soup = BeautifulSoup(content, "lxml")
    
    listingScraper(soup, fout)

    
    page = 1
    for page in range(2,30):
        page = str(int(page) + 1)
        url = urllib2.urlopen("http://www.trulia.com/for_sale/Portland,OR/100000-1000000_price/SINGLE-FAMILY_HOME_type/"+page+"_p/")
        content = url.read()
        soup = BeautifulSoup(content, "lxml")
        listingScraper(soup, fout)
    
    fout.close()
    
    today = datetime.datetime.today().strftime("%m-%d-%Y")
    pdxPath = 'pdxZestimate_' + today+'.txt'
    zEstimate(pdxPath)
    histoMatic(pdxPath)

    
    
            
        
