from os import listdir
from os.path import expanduser, dirname, isfile, join, basename
from time import time

import gi, glib
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, GLib

from PIL import Image
from PIL.Image import ANTIALIAS

from archive_manager import ArchiveManager

def image2pixbuf(im):
    """Convert Pillow image to GdkPixbuf"""
    data = im.tobytes()
    w, h = im.size
    data = GLib.Bytes.new(data)
    pix = GdkPixbuf.Pixbuf.new_from_bytes(data, GdkPixbuf.Colorspace.RGB,
            False, 8, w, h, w * 3)
    return pix

class Panel(Gtk.Image):
    def __init__(self,parent):
        super(Panel, self).__init__()

        self.Parent = parent

        self.pil_image = None


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

    def next(self,event):
        if self.Parent.current_archive:
            _file = self.Parent.archive_manager.next()
            self.display_page(_file)

    def previous(self,event):
        if self.Parent.current_archive:
            _file = self.Parent.archive_manager.previous()
            self.display_page(_file,next_file=False)

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
        self.pil_image = Image.open(bytes_image)
        #bitmap = self.scale_bitmap(self.pil_image)
        pixbuf = image2pixbuf(self.pil_image)

        allocation = self.Parent.get_allocation()
        desired_width,desired_height = (allocation.width,allocation.height)

        pixbuf = pixbuf.scale_simple(desired_width, desired_height, GdkPixbuf.InterpType.HYPER)

        self.set_from_pixbuf(pixbuf)

    def on_size(self,event):
        if self.pil_image == None:
            return

        bitmap = self.scale_bitmap(self.pil_image)
        bitmap = image2pixbuf(bitmap)
        self.image.SetBitmap(bitmap)
        self.Layout()

    def scale_bitmap(self,image):
        image_width,image_height = image.size
        allocation = self.get_allocation()
        max_width,max_height = (500,500)

        ratio = min(max_width/image_width, max_height/image_height)

        new_width = int(image_width * ratio)
        new_height = int(image_height * ratio)

        image = image.resize((new_width, new_height), ANTIALIAS)

        return image


UI_INFO = """
<ui>
  <toolbar name='ToolBar'>
    <toolitem action='FileNewStandard' />
    <toolitem action='FileQuit' />
  </toolbar>
</ui>
"""

class Application_window(Gtk.Window):
    
    def __init__(self, title):

        self.archive_manager = ArchiveManager()
        self.wildcard = "Zip archive (*.zip)|*.zip|"\
                        "Tar acrhive (*.tar)|*.tar"

        Gtk.Window.__init__(self, title=title)

        self.dirname=expanduser("~")
        # self.SetBackgroundColour('BLACK')

        self.box = Gtk.Box()
        self.box.set_spacing (5)
        self.box.set_orientation(Gtk.Orientation.VERTICAL)

        self.overlay = Gtk.Overlay()
        self.add(self.overlay)

        self.overlay.add_overlay(self.box)

        self.panel = Panel(parent=self)
        self.InitUI()

        self.box.pack_start (self.panel, False, False, 0)
        
        
    def InitUI(self):
        toolbar = Gtk.Toolbar()
        self.box.add(toolbar)
        

        tool_open = Gtk.ToolButton(stock_id=Gtk.STOCK_OPEN)
        tool_open.connect_after('clicked',self.on_open)
        tool_first = Gtk.ToolButton(stock_id=Gtk.STOCK_GOTO_FIRST)
        tool_first.connect_after('clicked',self.previous_archive)
        tool_previous = Gtk.ToolButton(stock_id=Gtk.STOCK_GO_BACK)
        tool_previous.connect_after('clicked',self.panel.previous)
        tool_next = Gtk.ToolButton(stock_id=Gtk.STOCK_GO_FORWARD)
        tool_next.connect_after('clicked',self.panel.next)
        tool_last = Gtk.ToolButton(stock_id=Gtk.STOCK_GOTO_LAST)
        tool_last.connect_after('clicked',self.next_archive)

        toolbar.add(tool_open)
        toolbar.add(tool_first)
        toolbar.add(tool_previous)
        toolbar.add(tool_next)
        toolbar.add(tool_last)



        # self.Bind(wx.EVT_TOOL, self.on_open, tool_open)
        # self.Bind(wx.EVT_TOOL, self.panel.previous, tool_previous)
        # self.Bind(wx.EVT_TOOL, self.panel.next, tool_next)
        # self.Bind(wx.EVT_TOOL, self.previous_archive, tool_first)
        # self.Bind(wx.EVT_TOOL, self.next_archive, tool_last)
        # #
        # self.Bind(wx.EVT_MOUSEWHEEL , self.dispatch_mouse, self)

        # self.SetSize((600, 600))
        # self.SetTitle('Comic reader')
        # self.Centre()
        # self.Show(True)

        self.current_archive = None

    def dispatch_mouse(self,event):
        if event.GetWheelRotation() > 0:
            self.panel.next(event)
        else:
            self.panel.previous(event)
        
    # def OnAbout(self,e):
    #     # Create a message dialog box
    #     dlg = wx.MessageDialog(self, " A sample editor \n in wxPython", "About Sample Editor", wx.OK)
    #     dlg.ShowModal() # Shows it
    #     dlg.Destroy() # finally destroy it when finished.
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