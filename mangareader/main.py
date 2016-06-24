from os import listdir
from os.path import expanduser, dirname, isfile, join, basename
from time import time

import gi, glib
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, GLib, Gdk

from PIL import Image
from PIL.Image import ANTIALIAS

from archive_manager import ArchiveManager

# for i in GdkPixbuf.Pixbuf.get_formats():
#     print(i.get_extentions())


class Panel(Gtk.Image):
    def __init__(self,parent):
        super(Panel, self).__init__()

        self.Parent = parent

        self.current_pixbuf = None


        # self.Bind(wx.EVT_LEFT_UP, self.next)
        # self.Bind(wx.EVT_RIGHT_UP, self.previous )
        # self.Bind(wx.EVT_SIZE, self.on_size)

        # self.image.Bind(wx.EVT_LEFT_UP, self.next)
        # self.image.Bind(wx.EVT_RIGHT_UP, self.previous )

        self.repeat_key = 0
        self.last_action_ts = time()

    def load_first_page(self):
        _file = self.Parent.archive_manager.first_page()
        if _file:
            self.set_image(_file)

    def load_last_page(self):
        _file = self.Parent.archive_manager.last_page()
        if _file:
            self.set_image(_file)

    def display_page(self,_file,next_file=True):
        if _file:
            self.set_image(_file)
            self.last_action_ts = time()
        else:
            if self.repeat_key >= 2:
                delay = time() - self.last_action_ts 
                if delay >= 1: 
                    if not next_file:
                        self.Parent.change_archive(next_file,first_page=False)
                    else:
                        self.Parent.change_archive(next_file)
                self.repeat_key = 0
            else:
                self.repeat_key += 1

    def set_image(self,bytes_image):
        
        loader = GdkPixbuf.PixbufLoader()
        loader.write(bytes_image.getbuffer())
        loader.close()

        self.current_pixbuf = loader.get_pixbuf()
         
        pixbuf = self.scale_pixbuf(self.current_pixbuf)

        self.set_from_pixbuf(pixbuf)

    def resize(self,width,height):
        if self.current_pixbuf == None:
            return

        pixbuf = self.scale_pixbuf(self.current_pixbuf)
        self.set_from_pixbuf(pixbuf)


    def scale_pixbuf(self,pixbuf):
        allocation = self.Parent.get_allocation()
        max_width,max_height = (allocation.width,allocation.height)
        image_width,image_height = (pixbuf.get_width(),pixbuf.get_height())

        #toolbar
        max_height -= 50

        ratio = min(max_width/image_width, max_height/image_height)

        new_width = int(image_width * ratio)
        new_height = int(image_height * ratio)

        pixbuf = pixbuf.scale_simple(new_width, new_height, GdkPixbuf.InterpType.HYPER)

        return pixbuf

class Application_window(Gtk.Window):
    
    def __init__(self, title):

        self.archive_manager = ArchiveManager()
        self.wildcard = "Zip archive (*.zip)|*.zip|"\
                        "Tar acrhive (*.tar)|*.tar"

        Gtk.Window.__init__(self, title=title)

        self.dirname=expanduser("~")
        # self.SetBackgroundColour('BLACK')

        self.box = Gtk.Box()
        self.box.override_background_color(
            Gtk.StateType.NORMAL, 
            Gdk.RGBA(0,0,0,1)
        )

        self.box.set_spacing (5)
        self.box.set_orientation(Gtk.Orientation.VERTICAL)

        self.overlay = Gtk.Overlay()
        self.add(self.overlay)

        self.overlay.add_overlay(self.box)

        self.panel = Panel(parent=self)
        self.InitUI()

        self.box.pack_start (self.panel, False, False, 0)

        self.current_archive = None

        allocation = self.get_allocation()
        self.past_width,self.past_height = allocation.width,allocation.height

        self.connect("check-resize",self.check_resize)
        self.connect("key_press_event",self.manage_key_events)
    
    def manage_key_events(self,widget,event):
        if not self.current_archive:
            return

        if event.keyval not in [Gdk.KEY_Left,Gdk.KEY_Right]:
            return

        if(event.keyval == Gdk.KEY_Left):
            self.previous()
        elif (event.keyval == Gdk.KEY_Right):
            self.next()
            

    def previous(self,event):
        _file = self.archive_manager.previous()
        self.panel.display_page(_file)

    def next(self,event):
        _file = self.archive_manager.next()
        self.panel.display_page(_file)

    def check_resize(self,a):
        allocation = self.get_allocation()
        width,height = allocation.width,allocation.height
        if width != self.past_width or height != self.past_height:
            self.past_width,self.past_height = width,height
            self.panel.resize(width,height)
    
    def InitUI(self):
        toolbar = Gtk.Toolbar()
        self.box.add(toolbar)
        

        tool_open = Gtk.ToolButton(stock_id=Gtk.STOCK_OPEN)
        tool_open.connect_after('clicked',self.on_open)
        tool_first = Gtk.ToolButton(stock_id=Gtk.STOCK_GOTO_FIRST)
        tool_first.connect_after('clicked',self.previous_archive)
        tool_previous = Gtk.ToolButton(stock_id=Gtk.STOCK_GO_BACK)
        tool_previous.connect_after('clicked',self.previous)
        tool_next = Gtk.ToolButton(stock_id=Gtk.STOCK_GO_FORWARD)
        tool_next.connect_after('clicked',self.next)
        tool_last = Gtk.ToolButton(stock_id=Gtk.STOCK_GOTO_LAST)
        tool_last.connect_after('clicked',self.next_archive)

        toolbar.add(tool_open)
        toolbar.add(tool_first)
        toolbar.add(tool_previous)
        toolbar.add(tool_next)
        toolbar.add(tool_last)

    def dispatch_mouse(self,event):
        if event.GetWheelRotation() > 0:
            self.panel.next(event)
        else:
            self.panel.previous(event)
        
    def next_archive(self,e):
        self.change_archive()

    def previous_archive(self,e):
        self.change_archive(next_archive=False)

    def on_open(self,button):
        """ Open a file"""
        dialog = Gtk.FileChooserDialog ("Open archive", button.get_toplevel(), Gtk.FileChooserAction.OPEN);
        dialog.add_button (Gtk.STOCK_CANCEL, 0)
        dialog.add_button (Gtk.STOCK_OK, 1)
        dialog.set_default_response(1)

        filefilter = Gtk.FileFilter()
        filefilter.add_pattern("*.zip")
        filefilter.add_pattern("*.tar")
        dialog.set_filter(filefilter)

        if dialog.run() == 1:
            self.open_archive(dialog.get_filename())

        dialog.destroy()

    def change_archive(self, next_archive=True, first_page=True):
        if self.current_archive:
            file_list = []

            for f in listdir(self.dirname):
                filename = join(self.dirname, f)
                if isfile(filename):
                    file_list.append(filename)

            files = sorted(file_list)
            index = files.index(self.current_archive)
            index = index + 1 if next_archive else index -1

            # if -1 we're a the start of directory, prevent looping to the end
            if index < 0:
                return 

            if index < len(files):
                self.open_archive(files[index],first_page=first_page)

    def open_archive(self,path, first_page=True):
        self.current_archive = path
        self.dirname = dirname(path)

        self.archive_manager.open_zip(path)

        self.set_title(basename(self.current_archive))

        if first_page:
            self.panel.load_first_page()
        else:
            self.panel.load_last_page()


if __name__ == '__main__':
    win = Application_window("comicreader")
    win.connect("delete-event", Gtk.main_quit)
    win.show_all()
    Gtk.main()