from tkinter import *
#from idlelib.ToolTip import *
from tkinter import ttk
from tkinter import filedialog
from os import mkdir, chdir, listdir, path, walk, startfile, getcwd, rename
import subprocess as S


owd = getcwd()
Caris = ("C:/Program Files/CARIS/BASE Editor/6.1/bin")
QGIS = ('')
GRASS = ('')


class Application(Frame):

    def __init__(self, master):
        """ Initialize the Frames for Application """

        Frame.__init__(self, master)
        self.grid()
        self.app_widgets()

    def Search_CSAR_Dir(self):
        """This Function allows the user to choose the
        Surfaces dir, then updates the
        Surfaces dir entry box with the selected path"""

        csar = self.CSAR_DIR.get()

        Csar_dir= filedialog.askdirectory(initialdir = csar, title='Select Surface directory ')
        self.CSAR_DIR.set(str(Csar_dir))
        #tip_CSAR = ToolTip(self.CSAR_dir, (self.CSAR_DIR.get()))

    def app_widgets(self):

        ## Create Main Menu Bar
        menu.add_cascade(label = "File", menu = submenu)


        ## Help Submenu
        submenu.add_command(label = "Help", command = self.Help)

        ## Close Submenu
        submenu.add_command(label = "Close Application", command = self.close)

        ## Process Data
        self.Button_P = Button(self, text="RUN", height=0,
                                   command=self.ExporttoGeotiff)
        self.Button_P.grid(row=0, column=2, sticky=W, padx=2)

        self.Polygon_Tools = LabelFrame(self, text="Export Geotiff", foreground="blue")
        self.Polygon_Tools.grid(row=0, column=0, sticky=W)

        self.CSAR_DIR = StringVar()
        self.CSAR_dir = Entry(self.Polygon_Tools, width=32, textvariable=self.CSAR_DIR)
        self.CSAR_dir_text = Label(self.Polygon_Tools, text="CSAR Folder")
        self.CSAR_dir_text.grid(row=0, column=0, sticky=W)
        self.CSAR_dir.grid(row=0, column=1, sticky=W)
        self.ButtonCSAR= Button(self.Polygon_Tools, text="...", height=0,
                                command=self.Search_CSAR_Dir)
        self.ButtonCSAR.grid(row=0, column=2, sticky=W, padx=2)

        


        
    def ExporttoGeotiff(self):
        """ This Function runs processing steps based on user inputs"""

        CSARS = self.CSAR_DIR.get()

        if not CSARS:
            print("No CSAR folder selected")
            return
        
        ListCSAR = listdir(CSARS)

        with open("Exporttogeotiff.bat", "w") as Import:
                Import.write('@ECHO OFF' + '\n')
                Import.write('cd /d "'+ Caris + '"\n')
                Import.write('@ECHO Exporting Geotiffs\n')
                
                for file in ListCSAR:
                    if file.endswith(".csar"):
                        File_Name = file.replace(".csar", "")
                        print("Exporting:", file)

                        input_file = CSARS + '/' + file
                        output_file = CSARS + '/' + File_Name + '.tiff'

                        Import.write(f'carisbatch --run ExportRaster  --output-format GEOTIFF --include-band Depth '
                                     f'"{input_file}" "{output_file}"\n')

        p = S.check_call("Exporttogeotiff.bat", stdin=None, stdout=None, stderr=None, shell=False)
                                    

    def Help(self):
        return

    def close(self):
        self.Exit = 'True'

root = Tk()
root.title("Export Geotiffs")
root.geometry("500x100")
menu = Menu(root)
root.config(menu=menu)
submenu = Menu(menu)
app = Application(root)
root.mainloop()
