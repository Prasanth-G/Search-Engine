import tkinter
from PIL import Image,ImageTk
import base64
import search_engine
from pytrie import SortedStringTrie
import json
import os

class application(tkinter.Frame):
    top_frame = None
    homepage_frame = None
    results_frame = None
    results_text = None
    __s_engine = search_engine.crawler()
    bg_image = os.path.join('resources', 'background_1.jpg')
    search_history = os.path.join('data', 'search_history.txt')
    search_freq = os.path.join('data', 'search_freq.txt')
    history = SortedStringTrie()
    def __init__(self,master):
        #for GUI
        tkinter.Frame.__init__(self,master)
        self.master = master
        self.search_query = tkinter.StringVar()
        self.search_query.trace("w",self.update_listbox)
        self.initUI()
        #for loading search history
        self.__restore_history()
        #for loading data into crawler
        self.__s_engine.restore()
        self.__s_engine.calc_pagerank(30)

    def initUI(self):
        self.master.title("SPIDER")
        self.master.state('zoomed')
        self.grid()
        
        #set icon
        icon = tkinter.PhotoImage(file = os.path.join('resources', "logo_t.png"))
        self.master.tk.call('wm','iconphoto',self.master._w,icon)

        application.top_frame = tkinter.Frame(self.master,bg = 'black',bd = 3,highlightcolor = 'blue')
        application.top_frame.grid(row = 0)
        
        #tool bar on top of master
        self.tabs = tkinter.Label(application.top_frame,text = "reserved for tabs")
        self.tabs.grid(row = 0)
        
        self.options = tkinter.PhotoImage(file=os.path.join('resources', "options_3.png"))
        self.options = self.options.subsample(20,20)
        self.options_button = tkinter.Button(application.top_frame,relief = 'flat',image = self.options, command = self.hide)
        self.options_button.grid(row = 1,column = 8)

        self.bookmark = tkinter.PhotoImage(file=os.path.join('resources', "bookmark_1.png"))
        self.bookmark = self.bookmark.subsample(40,40)
        self.bookmark_button = tkinter.Button(application.top_frame,relief = 'flat',bg = 'white',image = self.bookmark, command = self.hide)
        self.bookmark_button.grid(row = 1,column = 7)

        self.search_box1 = tkinter.Entry(application.top_frame,textvariable = self.search_query,bg = 'white',fg = 'black',selectborderwidth = 2,width = 200)
        self.search_box1.grid(row = 1,column = 0)
        self.search_box1.bind('<Return>',self.__get)
        #self.search_box.bind('<Configure>',self._resize_search_box)
        
        #homepage
        self.homepage_frame = tkinter.Frame()
        self.homepage = self.create_homepage()
        self.homepage_frame.grid(row = 2)

        #results page
        self.results_frame = tkinter.Frame()

    def hide(self):
        self.frame.pack_forget()
    '''def _resize_search_box(self,event):
        new_width = event.width
        self.search_box.destroy()
        #if new_width > 70:
        self.search_box = tkinter.Entry(application.top_frame,bg = 'white',fg = 'black',selectborderwidth = 1,bd = 10,font = ("COPRGTL.TTF"),relief = 'flat',width = new_width)
        #else:
         #   self.search_box = tkinter.Entry(application.top_frame,bg = 'white',fg = 'black',selectborderwidth = 1,bd = 4,font = ("COPRGTL.TTF"),relief = 'flat',width = 77)'''
    def create_homepage(self):
        
        background_image = Image.open(self.bg_image)
        background_image = background_image.resize((1536,841))
        self.background_photo = ImageTk.PhotoImage(background_image)
        self.background_label = tkinter.Label(self.homepage_frame,image = self.background_photo)
        self.background_label.grid(row = 1)

        #name
        self.name = tkinter.Label(self.homepage_frame,text = "   ADS ",bg = 'black',fg = 'white',font = ("SHOWG.TTF",60))
        self.name.grid()
        self.name.place(x = 620,y = 275)
        #search box
        self.search_box = tkinter.Entry(self.homepage_frame,textvariable = self.search_query,bg = 'white',fg = 'black',selectborderwidth = 1,bd = 6,font = ("COPRGTL.TTF",16),relief = 'flat',width = 40)
        self.search_box.bind('<Return>',self.__get)
        self.search_box.grid()
        self.search_box.place(x = 525,y = 400)  #centre 541,403.5
        #search image
        self.search_image = tkinter.PhotoImage(file=os.path.join('resources', "search_4.png")) #1-16 /4 - 8 
        self.search_image = self.search_image.subsample(8,8)
        self.search_button = tkinter.Button(self.homepage_frame,image = self.search_image,bg = 'white',relief = 'flat')
        self.search_button.grid(row = 1)
        self.search_button.place(x = 1020,y = 400)
        #listbox
        self.listbox = tkinter.Listbox(self.homepage_frame,selectborderwidth = 2,width = 0,height = 0)
        #self.listbox.bind('<Configure>',self.resize_listbox)
        self.listbox.grid(row = 1)
        self.listbox.place(x = 525,y = 439)
    def __get(self,event):
        input_str = self.search_box.get()
        if input_str in self.history:
            self.history[input_str] += 0.1
        else:
            self.history[input_str] = 0.1
        results = self.__s_engine.query(input_str)
        self.homepage_frame.grid_forget()
        self.resultspage = self.create_resultspage(results)
        self.results_frame.grid()
        
    def update_listbox(self,*args):
        text = self.search_query.get()
        if text.isprintable():
            relevent_words = self.__from_history(text) #search the term from history ;return a list
        self.listbox.delete(0,self.listbox.size())
        for each_item in relevent_words:
            self.listbox.insert(self.listbox.size(),each_item)
    def __from_history(self,query):
        if query in self.history:
            return sorted(self.history,key = self.history.values)
        return
    def create_resultspage(self,results):
        if self.results_text:
            self.results_text.grid_forget()
        self.results_text = tkinter.Label(self.results_frame,text = "results\n")
        self.results_text.grid()
        self.results = tkinter.Label(self.results_frame,font = ('',20))
        self.results.grid(row =  1,column = 0)
        s = ''
        for each_url in results:
            s += each_url + '\n'
         #   arr = box(self.results_frame,each_url)
        self.results.config(text = s)
    def __restore_history(self):
        words_file = open(search_history)
        freq_file = open(search_freq)
        words = words_file.read()
        freq = freq_file.read()
        words_list = []
        freq_list = []
        if words:
            words_list = json.loads(words)
        if freq:
            freq_list = json.loads(freq)
        words_file.close()
        freq_file.close()
        for loop_var in range(len(words_list)):
            self.history[words_list[loop_var]] = freq_list[loop_var]
    def store_history(self):
        words_file = open(search_history,'w')
        freq_file = open(search_freq,'w')
        words_list = self.history.keys()
        freq_list = self.history.values()
        words_file.write(json.dumps(words_list))
        freq_file.write(json.dumps(freq_list))
        words_file.close()
        freq_file.close()

#window
window = tkinter.Tk()
app = application(window)
app.store_history()

#window.mainloop()
