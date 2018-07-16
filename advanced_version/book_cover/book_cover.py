import requests, os

"""
    AUTHOR: Himanshu Sharma
    DOC: July 1, 2018

    DESCRIPTION:
    ============
    Returns the book cover image from ISBN.
"""


def download(isbn, directory):
    pic = "https://pictures.abebooks.com/isbn/{}-us-300.jpg".format(isbn)
    r = requests.get(pic)

    with open(os.path.join(directory,os.path.basename(pic)), "wb") as f:
        f.write(r.content)
       
    return os.path.join(os.path.join(directory, os.path.basename(pic)))
    
def book_info(isbn):
    url = "https://www.googleapis.com/books/v1/volumes?q=isbn:{}".format(isbn)
    r = requests.get(url)
    d = r.json()

    try:
        title = d["items"][0]["volumeInfo"]['title']
    except:
        title = 'title not available'

    try:
        authors = d["items"][0]["volumeInfo"]['authors']
    except:
        authors = ['authors not available']

    try:
        pubDate = d["items"][0]["volumeInfo"]['publishedDate']
    except:
        pubDate = 'published date not available'

    try:
        pagecount = d["items"][0]["volumeInfo"]['pageCount']
    except:
        pagecount = 'page count not available'

    try:
        category = d["items"][0]["volumeInfo"]['categories']
    except:
        category = ['categories not available']

    try:
        description = d["items"][0]["volumeInfo"]['description']
    except:
        description = 'description not available'

    return {"title":title, "authors":authors, "pubDate":pubDate, "pages":pagecount, "category":category, "description":description}
