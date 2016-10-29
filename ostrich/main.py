import sys
from os import listdir
from os.path import expanduser, dirname, isfile, join, basename, abspath
from time import time

from urllib.parse import urlparse,unquote

try:
    import gi, glib
except Exception as e:
    print("Error: You should install PyGI, apt-get install python3-gi on debian/ubuntu, yum install python3-gobject for fedora")
    sys.exit(0)

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GdkPixbuf, GLib, Gdk

from ostrich.archive_manager import ArchiveManager

# for i in GdkPixbuf.Pixbuf.get_formats():
#     print(i.get_extentions())


class Panel(Gtk.Image):

    def __init__(self,parent):

        super(Panel, self).__init__()

        self.Parent = parent
        self.current_pixbuf = None


    def display_page(self,image_file,nextimage_file=True):
        if image_file:
            self.set_image(image_file)

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

        Gtk.Window.__init__(self, title=title)

        self.archive_manager = ArchiveManager()
        self.wildcard = "Zip archive (*.zip)|*.zip|"\
                        "Tar archive (*.tar)|*.tar"\
                        "Cbz archive (*.cbz)|*.cbz"\
                        "Cbt archive (*.cbz)|*.cbt"


        self.dirname=expanduser("~")
        self.window_is_fullscreen = False

        self.set_default_size(500,700)

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

        self.panel_event_box = Gtk.EventBox()
        self.panel_event_box.set_above_child(True)
        self.panel = Panel(parent=self)
        self.panel_event_box.add(self.panel)

        self.InitUI()

        self.box.pack_start (self.panel_event_box, False, False, 0)

        self.current_archive = None

        allocation = self.get_allocation()

        self.past_width,self.past_height = allocation.width,allocation.height

        self.connect("check-resize",self.check_resize)
        self.connect("key_press_event",self.manage_key_events)
        #self.panel_event_box.connect("scroll-event", self.manage_button_events)
        self.panel_event_box.connect("button-press-event", self.manage_button_events)

        self.connect("window-state-event",self.on_window_state_change )


        #Drag and drop event
        self.connect('drag_data_received', self.on_drag_data_received)
        self.connect('drag_drop', self.drop_cb)
        self.connect('drag-motion', self.motion_cb)

        self.drag_dest_set(0,[],Gdk.DragAction.COPY)

    def motion_cb(self, widget, context, x, y, time):
        Gdk.drag_status(context, Gdk.DragAction.COPY, time)
        return True

    def drop_cb(self, widget, context, x, y, time):
        widget.drag_get_data(context, context.list_targets()[-1], time)

    def on_drag_data_received(self, widget, drag_context, x, y, data, info, time):
        #clean uri path
        files = data.get_text().rstrip('\n').split('\n')
        file = files[0]

        #from URI to Path
        url = urlparse(file)
        final_path = abspath(join(url.netloc, url.path))
        final_path = unquote(final_path)

        self.open_archive(final_path)

    def on_window_state_change(self, widget, event):
        self.window_is_fullscreen = bool(
            Gdk.WindowState.FULLSCREEN & event.new_window_state)

    def manage_button_events(self,widget,event):
        next_key_list = [Gdk.BUTTON_SECONDARY,Gdk.KEY_ScrollUp]
        previous_key_list = [Gdk.BUTTON_PRIMARY,Gdk.KEY_ScrollDown]

        if event.button in next_key_list:
            self.previous()
        elif event.button in previous_key_list:
            self.next()

    def manage_key_events(self,widget,event):
        if(event.keyval == Gdk.KEY_Left):
            self.previous()
        elif (event.keyval == Gdk.KEY_Right):
            self.next()
        if event.keyval == Gdk.KEY_F11:
            if self.window_is_fullscreen:
                self.unfullscreen()
            else:
                self.fullscreen()
            
    def previous(self,button=None):
        if not self.current_archive:
            return

        image_file = self.archive_manager.previous()
        if image_file:
            self.panel.display_page(image_file)

        self.update_title()

    def next(self,button=None):
        if not self.current_archive:
            return

        image_file = self.archive_manager.next()
        if image_file:
            self.panel.display_page(image_file)

        self.update_title()

    def load_first_page(self):
        if not self.current_archive:
            return

        image_file = self.archive_manager.first_page()
        if image_file:
            self.panel.display_page(image_file)

    def load_last_page(self):
        if not self.current_archive:
            return

        image_file = self.archive_manager.last_page()
        if image_file:
            self.panel.display_page(image_file)

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
        tool_delete = Gtk.ToolButton(stock_id=Gtk.STOCK_DELETE)
        tool_delete.connect_after('clicked',self.delete_archive)

        toolbar.add(tool_open)
        toolbar.add(tool_first)
        toolbar.add(tool_previous)
        toolbar.add(tool_next)
        toolbar.add(tool_last)
        toolbar.add(tool_delete)

    def delete_archive(self,event):
        if not self.current_archive:
            return

        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.WARNING,
            Gtk.ButtonsType.OK_CANCEL, "Are you sure ?")

        archive_name = self.archive_manager.get_current_archive_name()
        secondary_text = "The file \"%s\" will be DESTROYED" % archive_name
        dialog.format_secondary_text(secondary_text)

        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            success = self.archive_manager.delete_current_archive()
            if success:
                if self.is_there_next_archive():
                    self.next_archive()
                else:
                    self.previous_archive()
                #we reload only after, otherwise you will not find your archive
                self.reload_file_list()
            else:
                error_box = Gtk.MessageDialog(self, 0, Gtk.MessageType.INFO,
                    Gtk.ButtonsType.OK, "Error while deleting.")
                error_box.format_secondary_text(
                    "Can't delete %s" % archive_name)
                error_box.run()

        dialog.destroy()

    def is_there_next_archive(self):
        index_current_archive = self.file_list.index(self.current_archive)
        last_archive_index = len(self.file_list) - 1
        if index_current_archive == last_archive_index:
            return False
        else:
            return True
        
    def next_archive(self,e=None):
        if not self.current_archive:
            return
        self.change_archive()

    def previous_archive(self,e):
        if not self.current_archive:
            return
        self.change_archive(next_archive=False)

    def on_open(self,button):
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

    #reload all files present in directory
    def reload_file_list(self):
        file_list = []

        for f in listdir(self.dirname):
            filename = join(self.dirname, f)
            if isfile(filename):
                file_list.append(filename)

        self.file_list = sorted(file_list)

    def change_archive(self, next_archive=True, first_page=True):

        index = self.file_list.index(self.current_archive)
        index = index + 1 if next_archive else index -1

        # do nothing
        if index < 0 or index >= len(self.file_list):
            return 

        self.open_archive(self.file_list[index],first_page=first_page)

        self.update_title()

    def open_archive(self,path, first_page=True):

        self.current_archive = path
        self.dirname = dirname(path)

        self.reload_file_list()

        self.archive_manager.open_zip(path)

        self.set_title(basename(self.current_archive))

        if first_page:
            self.load_first_page()
        else:
            self.load_last_page()

        self.update_title()

    def update_title(self):
        title = "%s - [%s]" % (
            basename(self.current_archive),
            self.archive_manager.get_display_counter()
        )
        self.set_title(title)

def start_app(archive_path=None):
    win = Application_window("comicreader")
    win.connect("delete-event", Gtk.main_quit)
    win.show_all()
    Gtk.main()