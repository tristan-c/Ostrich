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