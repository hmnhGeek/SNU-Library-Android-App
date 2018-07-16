from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, ScreenManager, SwapTransition
from kivy.lang import Builder
from kivy.app import App
from kivy.clock import Clock

import snu_lib, requests, threading, json, book_cover, os, pickle, oxford_dictionary

Builder.load_file("blueprint.kv")
maindir = os.path.dirname(os.path.realpath(__file__))
reverse = {}
prev_screen = ''

class HomePage(Screen):
    def dev_notifier(self):
        try:
            r = requests.get("http://dev-notifier.herokuapp.com")
            developer_broadcast = r.json()
            
            if developer_broadcast['notification'] == "":
                self.ids.notifier.text = "\n\n\n\n\n\nNo new notification."
            else:
                self.ids.notifier.text = developer_broadcast['notification']
        except:
            self.ids.notifier.text = "\n\n\n\n\n\nNo internet connection!"

    def update_developer(self, dt):
        threading.Thread(target=self.dev_notifier).start()

    def start_search(self):
        query = self.ids.search_input.text

        if query != "":
            try:
                heading = query
                d = snu_lib.snu_lib.get_books_on_page(query)

                global reverse
                reverse = dict(zip(d.values(), d.keys()))
                
                listvw = '\n\n'
                counter = 1
                for i in d:
                    listvw += "[ref="+str(d[i])+"]"+str(counter)+".) "+i+"[/ref]\n\n"
                    counter += 1

                listvw += "\n"
            except:
                listvw = "No internet connection!"
        else:
            heading = "nothing"
            listvw = "Provide a valid query to get results."
            
        sm.get_screen("books_page").update_results(listvw, heading)
        self.manager.current = "books_page"

    def begin_search_thread(self):
        self.manager.current = "loading_screen"
        threading.Thread(target=self.start_search).start()

    def build_book_info(self):
        try:
            if self.ids.search_input.text == '' or not self.ids.search_input.text.isdigit():
                self.manager.current = "home"
            else:
                book_details = book_cover.book_cover.book_info(int(self.ids.search_input.text))
                sm.get_screen("details").update_details_page(book_details, int(self.ids.search_input.text))
        except:
            self.manager.current = "no_internet"

    def begin_build_thread(self):
        global prev_screen
        prev_screen = self.manager.current
        self.manager.current = "loading_screen"
        threading.Thread(target=self.build_book_info).start()
        
class BookResultPage(Screen):
    def update_results(self, LIST, heading):
        self.ids.title_heading.text = "Search results based on "+heading

        if LIST != "\n\n\n":
            self.ids.results_label.text = LIST
        else:
            self.ids.results_label.text = """Nothing found, try typing the same query a little bit differently.
\nUSEFUL TIP: (Book Name) <space> (Author) will yield best results."""

    def book_data(self, book_link):
        try:
            b = snu_lib.snu_lib.load_book_data(book_link)

            requests.post("http://stat-notifier.herokuapp.com", data=json.dumps({"url":book_link}))
            req = requests.get("http://stat-notifier.herokuapp.com")
            try:
                books_searched = req.json()[book_link]
            except:
                books_searched = 0
            
            global reverse
            sm.get_screen("book_shelf").update_shelf(b, reverse[book_link], books_searched, book_link)
            self.manager.current = "book_shelf"
        except:
            self.manager.current = "no_internet"

    def start_data_thread(self, book_link):
        self.manager.current = "loading_screen"
        threading.Thread(target=lambda: self.book_data(book_link)).start()

class BookShelf(Screen):
    current_url = ''
    def update_shelf(self, tuple_data, book_title, books_searched, link):
        self.ids.book_title.text = book_title
        self.ids.book_search_data.text = "{} search(s) for this book have been made recently.".format(books_searched)
        self.current_url = link
        
        try:
            if tuple_data[0].isdigit():
                # there is a bug in the snu_lib directory which gives the reverse of ISBN
                # to rectify that error, I am reversing the recieved ISBN from snu_lib instead of
                # fixing the library itself.
                reversed_isbn = tuple_data[0]
                reversed_isbn = reversed_isbn[-1:-len(reversed_isbn)-1: -1]
                
                self.ids.isbn.text = "[ref=isbn]"+str(reversed_isbn)+"[/ref]"
            else:
                self.ids.isbn.text = "No ISBN found!"
        except:
            self.ids.isbn.text = "No ISBN found!"

        try:
            self.ids.shelf.text = str(tuple_data[1][0])
        except:
            self.ids.shelf.text = "Unable to find shelf."

        Clock.schedule_interval(self.strip_thread, 1)

    def update_strip(self):
        req = requests.get("http://stat-notifier.herokuapp.com")
        books_searched = req.json()[self.current_url]
        self.ids.book_search_data.text = "{} search(s) for this book have been made recently.".format(books_searched)
        
    def strip_thread(self, dt):
        threading.Thread(target=self.update_strip).start()

    def download_front(self):
        curr = os.path.join(os.path.dirname(os.path.realpath(__file__)), "covers")
        current_isbn = self.get_isbn(self.ids.isbn.text)
        cover = book_cover.book_cover.download(current_isbn, curr)

        if current_isbn != '':
            sm.get_screen("cover_page").update_image(cover)
            self.manager.current = "cover_page"
        else:
            self.manager.current = "book_shelf"

    def download_cover(self):
        self.manager.current = "loading_screen"
        threading.Thread(target=self.download_front).start()

    def build_details(self, isbn_no):
        try:
            d = book_cover.book_cover.book_info(int(isbn_no))
            sm.get_screen("details").update_details_page(d, int(isbn_no))
            self.manager.current = "details"
        except:
            self.manager.current = "book_shelf"

    def get_isbn(self, MarkUp):
        useful = ''
        state = False
        
        for i in MarkUp:
            if i == '[' or i == ']':
                if i == ']' and state == False:
                    state = True
                elif i == '[' and state == True:
                    state = False
            else:
                if state == True:
                    useful += i
        return useful

    def book_details_thread(self):
        global prev_screen
        prev_screen = self.manager.current
        self.manager.current = "loading_screen"
        isbn_no = self.ids.isbn.text
        isbn_no = self.get_isbn(isbn_no)
        threading.Thread(target=lambda:self.build_details(isbn_no)).start()
    
class Loader(Screen):
    pass

class NOInternet(Screen):
    pass

class About(Screen):
    def load_about(self):
        f = open("about.txt", "r")
        s = f.read()
        f.close()

        return s

class DisClaimer(Screen):
    def load_disclaimer(self):
        f = open("disclaimer.txt", "r")
        s = f.read()
        f.close()

        return s

class CoverPage(Screen):
    def update_image(self, image_addr):
        self.ids.cover_image.source = image_addr

class BookDetailsPage(Screen):     
    def update_details_page(self, d, isbn):
        self.ids.book_title.text = "\n"+d['title']+"\n"
        self.ids.book_authors.text = "\n"+'\n'.join(d['authors'])+"\n"
        self.ids.book_pubdate.text = "\n"+d['pubDate']+"\n"
        self.ids.book_pagecount.text = "\n"+str(d['pages'])+"\n"
        self.ids.book_category.text = "\n"+'\n'.join(d['category'])+"\n"
        self.ids.book_description.text = "\n"+d['description']+"\n"

        ## for cover image
        curr = os.path.join(maindir, "covers")
        cover = book_cover.book_cover.download(isbn, curr)
        self.ids.book_cover.source = cover
        self.manager.current = "details"

    def get_previous_screen(self):
        global prev_screen
        return prev_screen

class Dictionary(Screen):
    def clear(self):
        self.ids.dict_input.text = ''

    def credentials(self):
        f = open("oxford_creds.dat", "rb")
        try:
            while True:
                d = pickle.load(f)
        except EOFError:
            f.close()

        return d

    def search_meaning(self):
        creds = self.credentials()

        if creds != {}:
            if self.ids.dict_input.text != '':
                app_id = creds['app_id']
                app_key = creds['app_key']

                try:
                    oxford_returned = oxford_dictionary.oxford_dictionary.meaning_of(self.ids.dict_input.text, app_id, app_key)

                    try:
                        meaning = oxford_returned['meanings']
                    except:
                        meaning = ["NA"]

                    try:
                        examples = oxford_returned['examples']
                    except:
                        examples = "NA"

                    count = 1
                    meaningLabel = ''
                    for i in meaning:
                        meaningLabel += str(count)+".) "+i+"\n"

                    sm.get_screen("dict_results").update_screen(meaningLabel, examples, self.ids.dict_input.text)
                    self.manager.current = "dict_results"
                except:
                    self.manager.current = "no_internet"
            else:
                self.manager.current = "dictionary"
        else:
            self.manager.current = "dict_reg"

    def search_meaning_thread(self):
        self.manager.current = "loading_screen"
        threading.Thread(target=self.search_meaning).start()

    def del_ac(self):
        f = open("temp.dat", "wb")
        pickle.dump({}, f)
        f.close()

        os.remove("oxford_creds.dat")
        os.rename("temp.dat", "oxford_creds.dat")

class DictionaryRegister(Screen):
    def load_about(self):
        f = open("register_policy.txt", "r")
        s = f.read()
        f.close()
        return s

    def register(self):
        f = open("temp.dat", "wb")
        pickle.dump({"app_id":self.ids.app_id.text, "app_key":self.ids.app_key.text}, f)
        f.close()

        os.remove("oxford_creds.dat")
        os.rename("temp.dat", "oxford_creds.dat")
        self.manager.current = "dictionary"

class DictionaryResults(Screen):
    def update_screen(self, meaningLabel, examples, title):
        self.ids.dict_title.text = title
        self.ids.meaning.text = meaningLabel
        self.ids.examples.text = examples

sm = ScreenManager(transition=SwapTransition())
sm.add_widget(HomePage(name="home"))
sm.add_widget(BookResultPage(name="books_page"))
sm.add_widget(Loader(name="loading_screen"))
sm.add_widget(BookShelf(name="book_shelf"))
sm.add_widget(NOInternet(name="no_internet"))
sm.add_widget(About(name="about"))
sm.add_widget(DisClaimer(name='disclaims'))
sm.add_widget(CoverPage(name="cover_page"))
sm.add_widget(BookDetailsPage(name="details"))
sm.add_widget(Dictionary(name="dictionary"))
sm.add_widget(DictionaryRegister(name="dict_reg"))
sm.add_widget(DictionaryResults(name="dict_results"))

Clock.schedule_interval(sm.get_screen("home").update_developer, 5)

class MainApplication(App):
    def build(self):
        self.del_covers()
        return sm

    # deleting previously downloaded covers.
    def del_covers(self):
        try:
            path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "covers")
            files = os.listdir(path)
            for fi in files:
                os.remove(os.path.join(path, fi))
        except:
            os.mkdir("covers")

if __name__ == '__main__':
    MainApplication().run()
