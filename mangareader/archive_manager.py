import os
import re
from zipfile import ZipFile
from tarfile import TarFile
from io import BytesIO 

regex = re.compile("\d+")

def tryint(s):
    try:
        return int(s)
    except:
        return s

# courtesy of http://stackoverflow.com/questions/4623446/how-do-you-sort-files-numerically
def alphanum_key(s):
    """ Turn a string into a list of string and number chunks.
        "z23a" -> ["z", 23, "a"]
    """
    return [ tryint(c) for c in re.split('([0-9]+)', s) ]

class ArchiveManager:
    def __init__(self):
        self.archive = None
        self.archive_type = None
        self.listfile = None
        self.listfile_index = 0
        self.archive_length = 0

        self.hit_next = 0

    def open_zip(self,archive_path):
        if self.archive:
            self.archive.close()

        filename, file_extension = os.path.splitext(archive_path)

        if file_extension == ".zip" or file_extension == ".cbz":
            self.archive = ZipFile(archive_path , 'r')
            self.archive_type = "zip"
            namelist = self.archive.namelist()
        elif file_extension == ".tar" or file_extension == ".cbt":
            self.archive = TarFile(archive_path , 'r')
            self.archive_type = "tar"
            namelist = self.archive.getnames()
        else:
            raise("archive not supported")

        # we sort the files by decimal found, excluding directories /
        self.listfile = sorted(
            [x for x in namelist if not x.endswith('/')],
            key=lambda name: alphanum_key(name)
        )

        self.archive_length = len(self.listfile)
        self.listfile_index = 0


    def first_page(self):
        return self.get_file(self.listfile[0])

    def last_page(self):
        self.listfile_index = len(self.listfile) - 1
        return self.get_file(self.listfile[self.listfile_index])

    def get_file(self,name):
        image = BytesIO()
        if self.archive_type == "zip":
            image.write(self.archive.read(name))
        elif self.archive_type == "tar":
            tarinfo = self.archive.getmember(name)
            image_file = self.archive.extractfile(tarinfo)
            image.write(image_file.read())
        else:
            return None

        return image


    def next(self):
        if not self.archive:
            return None

        self.listfile_index = self.listfile_index + 1

        if self.listfile_index >= self.archive_length:
            self.listfile_index = self.archive_length - 1
            return None

        filename = self.listfile[self.listfile_index]
        return self.get_file(filename)

    def previous(self):
        if not self.archive:
            return None

        self.listfile_index = self.listfile_index - 1
        if self.listfile_index < 0:
            self.listfile_index = 0
            return None

        filename = self.listfile[self.listfile_index]
        return self.get_file(filename)





