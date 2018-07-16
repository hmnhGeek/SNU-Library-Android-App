from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, ScreenManager, SwapTransition
from kivy.lang import Builder
from kivy.app import App
from kivy.clock import Clock

import snu_lib, requests, threading, json

Builder.load_file("blueprint.kv")

reverse = {}

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
                
                self.ids.isbn.text = reversed_isbn
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

sm = ScreenManager(transition=SwapTransition())
sm.add_widget(HomePage(name="home"))
sm.add_widget(BookResultPage(name="books_page"))
sm.add_widget(Loader(name="loading_screen"))
sm.add_widget(BookShelf(name="book_shelf"))
sm.add_widget(NOInternet(name="no_internet"))
sm.add_widget(About(name="about"))
sm.add_widget(DisClaimer(name='disclaims'))

Clock.schedule_interval(sm.get_screen("home").update_developer, 5)

class MainApplication(App):
    def build(self):
        return sm

if __name__ == '__main__':
    MainApplication().run()
