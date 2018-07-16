import requests, json

"""
    AUTHOR: Himanshu Sharma
    DOC: June 18, 2018 9:52 IST

    DESCRIPTION:
    ===========================

    This module utilizes oxford dictionary apis. 
"""

language = "en"

def meaning_of(word, app_id, app_key):
    """ Returns the meaning of the word. """
    
    url = 'https://od-api.oxforddictionaries.com:443/api/v1/entries/' + language + '/' + word.lower()
    r = requests.get(url, headers={"app_id":app_id, "app_key":app_key})

    data = r.json()
    useful_data = {}

    for i in data['results'][0]['lexicalEntries'][0]['entries']:
        for j in i:
            for k in i[j][0]:
                try:
                    subdata = i[j][0][k]
                    if k == 'subsenses':
                        useful_data.update({"meanings":subdata[0]['definitions']})
                    elif k == 'examples':
                        useful_data.update({"examples":subdata[0]['text']})
                    else:
                        pass
                except:
                    pass
    return useful_data
