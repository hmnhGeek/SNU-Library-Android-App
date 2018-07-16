import requests
import re

"""
    AUTHOR: Himanshu Sharma
    DOC: June 14, 2018

    Description:
    ------------

    Can be used to manipulate library.snu.edu.in. bs4 is NOT used.
"""

library = "http://library.snu.edu.in"
catalog_url = "http://library.snu.edu.in/cgi-bin/koha/opac-search.pl?q={}&offset={}"

def load_book_data(book_url):
    """ Returns the shelf no and other book information provided the book
        url is given.
    """
    source_code = requests.get(book_url).text
    a = source_code

    # ISBN information
    isbn = a[a.find('<span class="results_summary isbn">') \
             :a.find('<span class="results_summary isbn">')+ len('<span class="results_summary isbn">')+54 \
             :1]

    # found this logic through experimentation. ;p
    isbn_counter = -9
    ISBN = ''

    try:
        while isbn[isbn_counter] != ">":
            ISBN += isbn[isbn_counter]
            isbn_counter -= 1
    except IndexError:
        ISBN = None


    # loading the td tags
    l = re.findall(r'<td.*?>(.*?)<\/td>', source_code)

    # this logic now seems too complex but was not at the time it was thought of :D.
    td = []
    for i in l:
        j = i.split(" ")
        for k in j:
            try:
                k = float(k)
                if k not in td:
                    td.append(k)
            except:
                pass

    return ISBN, td

def make_query(query):
    """ Splits on ' ' and joins with '+' """
    return '+'.join(query.split(' '))

def extract_content(tag, source):
    """ Returns content between the tag. """

    start_pt = source.find(tag) + len(tag)
    content = ''

    counter = start_pt
    while source[counter] != '<':
        content += source[counter]
        counter += 1

    return content


def extract_links(anchor_tag):
    """ Returns href from an anchor tag. """

    start_pt = anchor_tag.find("href=") + 6 # 5 = len of href= and one length for '"'
    link = ''
    
    counter = start_pt
    while anchor_tag[counter] != '"':
        link += anchor_tag[counter]
        counter += 1

    return library+link


def get_books_on_page(query, offset=0):
    """ Returns the 20 books on a page with offset equal to offset (defaults to 0). """

    target = catalog_url.format(make_query(query), offset)

    r = requests.get(target)
    source_code = r.text

    # given offset has been obtained, find links on that page.
    links = {}
    hyperlinks = re.findall(r'<a href=\S+ class="title">', source_code)
    
    for hlink in hyperlinks:
        links.update({extract_content(hlink, source_code):extract_links(hlink)})

    return links
    
def catalog_search(query):
    """ Returns search results from the library catalog. """

    r = requests.get(catalog_url.format(make_query(query), 0))
    source_code = r.text

    val = re.findall(r'Your search returned \d+ results.', source_code)
    num_of_results = int(val[0].split(" ")[-2])

    offsets = num_of_results/20
    search_links = {}

    # try for the offsets
    for offset in range(offsets+1):
        search_links.update(get_books_on_page(query, offset*20))

    return search_links
