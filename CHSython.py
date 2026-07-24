from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from tkcalendar import DateEntry
import pandas as pd
import numpy as np
from tkinter import filedialog
from os import mkdir, chdir, listdir, path, walk, startfile, getcwd, rename, startfile, remove
from docx import Document
import datetime as DATES
import subprocess as S
import matplotlib.pyplot as plt
from math import sqrt, pi
import openpyxl
import re
import time
import shapefile
import fileinput
import sys
import json
import os
from datetime import datetime
from copy import deepcopy
#sys.path.append('C:/Program Files/CARIS/HIPS and SIPS/11.4/python/3.11')
sys.path.append('C:/Program Files/CARIS/HIPS and SIPS/12.1/python/3.11')
sys.path.append(r'C:\Tools\CHSython-main\chs_lib')
import caris.coverage as cov
import caris
import warnings
import shutil
warnings.simplefilter("ignore")
from hips_project import *
import create_bounding_polygon as BP

owd = getcwd()

APPLICATION_PATH = os.path.dirname(__file__)

with open(os.path.join(APPLICATION_PATH, 'Software_Paths.json'), "r") as f:
    soft_par = json.load(f)

Python = soft_par["paths"]["PYTHON"]
Caris = soft_par["paths"]["CARIS"]
CATools = soft_par["paths"]["CATOOLS"]
QCTools = soft_par["paths"]["QCTOOLS"]


def CONV_DOY():
    """ Opens and Run Julian Day Convertor"""
    chdir(owd)
    S.check_call(f'"{sys.executable}" -W ignore "{owd}/JD.py"', shell=True)
    #p = S.check_call(Python + "/python.exe " + owd + "/JD.py", shell=True)


def CSARtoGEOTIFF():
    chdir(owd)
    S.check_call(f'"{sys.executable}" -W ignore "{owd}/ExportGeotiffs.py"', shell=True)
    #p = S.check_call(Python + "/python.exe " + owd + "/ExportGeotiffs.py", shell=True)

def RefractionEditor():
    chdir(owd)
    S.check_call(f'"{sys.executable}" -W ignore "{owd}/Refract.py"', shell=True)
    #p = S.check_call(Python + "/python.exe " + owd + "/Refract.py", shell=True)

def RetrievalApp():
    S.check_call(f'"{sys.executable}" -W ignore "{owd}/CHS_Product_Retrieval_App.py"', shell=True)

    
def DMS_to_DD(coords_DMS):
    """Converts DMS to DD"""

    Sep_DMS = coords_DMS.split('-')
    coords_DD = (float(Sep_DMS[2])/3600) + (float(Sep_DMS[1])/60) + float(Sep_DMS[0])
    return(coords_DD)

def DD_to_Rads(coords_DD):
    """Converts DD to Radians"""
    coords_rads = coords_DD*(pi/180)
    return(coords_rads)


def TPU(order, Depth):
    """Allowable Vertical and Horizontal Uncertainty Calculation for each
    IHO and CHS order"""

    if order == 'EXCLUSIVE':
        a = 0.15
        b = 0.0075
        THU_v = 1

    elif order =='SPECIAL':
        a = 0.25
        b = 0.0075
        THU_v = 2

    elif order == '1A' or order == '1B':
        a = 0.5
        b = 0.013
        THU_v = 5 + 0.05 * Depth

    elif order == '2' or order == '3':
        a = 1.0
        b = 0.023
        THU_v = 20 + 0.10 * Depth


    TVU_v = round(sqrt(a**2 + (b * Depth)**2),3)
    return(TVU_v, THU_v) ## Return Expected Total Vertical Uncertainty SOUACC and Postional Uncertainty POSACC


class Application(Frame):


    def __init__(self, master):
        """ Initialize the Frames for CHSython"""

        Frame.__init__(self, master)
        self.grid()
        self.general_hips_options()
        self.Load_Auxiliary_Par()
        self.Load_Hips_Project_Par()
        self.Sub_Rep()
        self.Sub_Final()
        self.app_widgets()
        self.Load_GRID_Par()
        #self.Copy_HIPS()


    def app_widgets(self):
        """Defines GUI Widgets"""

        ## Create Main Menu Bar
        menu.add_cascade(label = "File", menu = submenu)

        ## Create Submission Menu Bar
        menu.add_cascade(label = "Additional Tools", menu = submenu2)

        ## Create Project Dir
        submenu2.add_command(label = "Create Proj Dir", command = self.Create_Project_Dir)

        ## Convert DOY to JD
        submenu2.add_command(label = "DOY to JD", command = CONV_DOY)

        ## Convert CSAR to GEOTIFF
        submenu2.add_command(label = "CSAR Surface to GEOTIFF", command = CSARtoGEOTIFF)

        ## Convert CSAR to Refraction Editor
        submenu2.add_command(label = "Refraction Editor", command = RefractionEditor)

        ## Retrieve Chart Products based off Extent Shapefiles
        submenu2.add_command(label = "CHS Product Retrieval App", command = RetrievalApp)

        ## Save User Parameters
        submenu.add_command(label = "Save Parameters", command = self.Save_Par)

        ## Help Submenu
        submenu.add_command(label = "Help", command = self.Help)

        ## Close Submenu
        submenu.add_command(label = "Close Application", command = self.close)

        ## Process Data
        self.Button_P = Button(self, text="Process Data", height=0,
                               command=self.CHS_Proccessing)
        self.Button_P.grid(row=2, column=2, sticky=W, padx=2)


    def CHS_Proccessing(self):
        """Processing steps based on user inputs"""

        chdir(str(self.OUT_F.get()))
        if path.exists(str(self.JULIAN_D.get())):
            pass
        else:
            mkdir(str(self.JULIAN_D.get())) ## Create a Julian Day dump folder for CHSython Output

        chdir(owd)

        if self.S_T.get()==1 or self.S_T.get()==2 or self.S_T.get()==3 or self.S_T.get()==4 or self.S_T.get()==5:
            self.IMPORT_TO_HIPS() ## Imports RAW data through Import HIPS Process

        if self.A_T.get()==1 or self.A_T.get()==2:
            self.Import_Auxiliary() ## Imports POSMV or SBET Data through Import Applanix Data Proccess

        if (self.T_T.get()==1 or self.T_T.get()==2) or self.COMP_TPU.get()==1:
            self.GEOREFERENCE_HIPS() ## Runs Georeferencing steps through Georeferenceing Process

        if self.GRID.get()==1 or self.GRID.get()==2:
            self.Create_Addto_Hips_Grid() ## Creates or adds Hips data to surfaces using HIPS Gridding

        self.Combine_Caris_Output() ## Combines all Output logs into 1 File and saves to Julian Day dump folder

        if self.D_R.get() == 1:
            self.Run_Daily_Report() ## Run Reporting Script for Daily and Weekly Reports

        if self.CATOOLS.get() == 1:
            print("Running CA Tools")
            self.Run_CATools_UI() ## Run NAVWARN Processing in CA Tools


    def Search_RAW_Data(self):
        """Allows the user to choose the
        dir where RAW sonar files live, then updates the
        Raw file entry box with the selected dir path"""

        raw = self.RAW_F.get()

        RAW_Filedir = filedialog.askdirectory(title='Select Raw Sensor File ' +
                                              'Directory', initialdir=raw)
        self.RAW_F.set(RAW_Filedir)


    def Search_HDCS_Data(self):
        """Allows the user to choose the
        dir with the HDCS Data (Proccessing Folder), then updates the
        Proccessing entry box with the selected dir path"""

        hdcs = self.HDCS_D.get()

        HDCS_Filedir = filedialog.askdirectory(title='Select Processing folder' +
                                               'Directory', initialdir=hdcs)
        self.HDCS_D.set(HDCS_Filedir)


    def Search_VesselFile(self):
        """Allows the user to choose the
        Vessel Config file, then updates the
        Vessel file entry box with the selected Vessel file path"""

        vessel = self.VESSEL_N.get()
        V = path.split(vessel)

        VESSEL_File = filedialog.askopenfilename(initialdir = V[0],
                                       title = 'Select Vessel File',
                                       filetypes = (("Vessel Config","*.hvf"),("Vessel Config",".*vessel"),("all files","*.*")))
        self.VESSEL_N.set(VESSEL_File)
        


    def Search_Aux_Data(self):
        """Allows the user to choose the
        dir with the POS files"""

        Aux = self.AUX_F.get()

        AUX_Filedir = filedialog.askdirectory(title='Select Folder ' +
                                                'Directory', initialdir=Aux)
        self.AUX_F.set(AUX_Filedir)
        self.POSDIR.set(AUX_Filedir)


    def Search_Aux_Data2(self):
        """Allows the user to choose the
        dir with the RMS File, then updates the
        RMS file entry box with the selected dir path"""

        fdir2 = self.AUX_F2.get()
        fd2 = path.split(fdir2)

        AUX_Filedir = filedialog.askopenfilename(initialdir = fd2[0],
                                       title = 'Select RMS File',
                                       filetypes = (("RMS","*.out"),("all files","*.*")))
        self.AUX_F2.set(AUX_Filedir)


    def Search_Aux_Data3(self):
        """Allows the user to choose the
        dir with the SBET File, then updates the
        SBET file entry box with the selected dir path"""

        fdir3 = self.AUX_F3.get()
        fd3 = path.split(fdir3)


        AUX_Filedir = filedialog.askopenfilename(initialdir = fd3[0],
                                    title = 'Select SBET File',
                                    filetypes = (("SBET","*.out"),("all files","*.*")))
        self.AUX_F3.set(AUX_Filedir)


    def Search_OUTPUT(self):
        """Allows the user to choose an Output
        dir for the Caris log information to be saved as text files,
        then updates the Output entry box with the selected dir path"""

        out = self.OUT_F.get()

        OUTPUT_Filedir = filedialog.askdirectory(title='Select Output Folder ', initialdir=out)
        self.OUT_F.set(str(OUTPUT_Filedir))
    

    def Search_SVP(self): #ML Remove
        """Allows the user to choose a SVP dir
        for runing Caris SVP in Georeferencing"""

        svp = self.SVPDir.get()

        #svp = path.split(sv)

        SVP_Filedir = filedialog.askdirectory(initialdir = svp ,
                                              title='Select SVP File ' +
                                              'Directory')
        self.SVPDir.set(SVP_Filedir)


    def Search_Sub_dir_file(self):
        """Allows the user to choose the
        ATL ISO Submission File"""


        Sub_dir = filedialog.askdirectory(initialdir = "/", title='Select Submission Directory ')
        self.SUB_D.set(str(Sub_dir))


    def Search_dir(self):
        """Allows the user to choose a Project
        dir for creating Project folder structure"""

        self.PF = filedialog.askdirectory(initialdir = "/", title='Select Project directory ')


    def Search_TIDE_File(self):
        """Allows the user to choose the
        Tide file, then updates the
        Tide file entry box with the selected Tide file path"""

        tf = self.T_f.get()
        tfp = path.split(tf)

        Tide_File = filedialog.askopenfilename(initialdir = tfp[0],
                                       title = 'Select Tide File',
                                       filetypes = (("Tide Files","*.tid"),("all files","*.*")))
        self.T_F.set(Tide_File)


    def Search_Model_File(self):
        """Allows the user to choose the
        Tide Model file, then updates the
        Tide file entry box with the selected Tide Model file path"""

        mf = self.M_F.get()
        mfp = path.split(mf)

        Model_File = filedialog.askopenfilename(initialdir = mfp[0],
                                       title = 'Select Model File',
                                       filetypes = (("all files","*.*"), ("Text Model File","*.txt"),("CSV","*.csv"), ("XYZ","*.xyz"),
                                                    ("Raster Model File","*.csar")))
        self.M_F.set(Model_File)


    def Search_Info_File(self):
        """Allows the user to choose the
        Tide Model info file, then updates the
        Tide file entry box with the selected Tide Model info file path"""

        info = self.INFO_F.get()
        infop = path.split(info)

        INFO_File = filedialog.askopenfilename(initialdir = infop[0],
                                       title = 'Select Model Info File',
                                       filetypes = (("Tide Info Files","*.info"),("all files","*.*")))
        self.INFO_F.set(INFO_File)


    def Search_Grid_Dir(self):
        """Allows the user to choose the
        Surfaces dir, then updates the
        Surfaces dir entry box with the selected path"""

        grid = self.GRID_DIR.get()
        Grid_dir = filedialog.askdirectory(initialdir = grid, title='Select Surface directory ')
        self.GRID_DIR.set(str(Grid_dir))


    def Search_CSAR_File(self):
        """Allows the user to choose the
        Csar file for input into QCTools"""

        CSAR_File = filedialog.askopenfilename(initialdir = "/",
                                       title = 'Select CSAR File',
                                       filetypes = (("Csar File","*.csar"),
                                                    ("all files","*.*")))
        CSAR_File = CSAR_File.replace("/", "\\")
        self.CSAR_F.set(CSAR_File)


    def Search_GEOTIFF_File(self):  ## Not running Code
        """Allows the user to choose the
        Geotiff or Geotif file for input into CATools"""

        GEOTIFF_File = filedialog.askopenfilename(initialdir = "/",
                                       title = 'Select Geotiff File',
                                       filetypes = (("Geotiff File","*.tiff"),
                                                    ("Geotif File","*.tif"),
                                                    ("all files","*.*")))
        GEOTIFF_File = GEOTIFF_File.replace("/", "\\")
        self.GEOTIFF_F.set(GEOTIFF_File)


    def Search_LINE_File(self):
        """Allows the user to choose the
        Caris Line Report - Created using HIPS"""

        line = self.LINE_F.get()
        linep = path.split(line)

        LINE_File = filedialog.askopenfilename(initialdir = linep[0],
                                       title = 'Select Caris Line Report',
                                       filetypes = (("ASCII Text","*.txt"),
                                                    ("all files","*.*")))
        self.LINE_F.set(LINE_File)


    def Search_SpreadSheet_File(self):
        """Allows the user to choose the
        Daily Report Spreadsheet"""

        rf = self.REP_F.get()
        rfp = path.split(rf)

        REP_File = filedialog.askopenfilename(initialdir = "/",
                                       title = 'Select Line Report Spreadsheet',
                                       filetypes = (("Spread Sheet","*.xlsx"),
                                                    ("all files","*.*")))
        self.REP_F.set(REP_File)


    def Search_SpreadSheet_File2(self):
        """Allows the user to choose the
        Weekly Report Spreadsheet"""

        Wrf = self.WREP_F.get()
        Wrfp = path.split(Wrf)

        WREP_File = filedialog.askopenfilename(initialdir = "/",
                                       title = 'Select Line Report Spreadsheet',
                                       filetypes = (("Spread Sheet","*.xlsx"),
                                                    ("all files","*.*")))
        self.WREP_F.set(WREP_File)


    def Search_VALSRC_Folder(self):
        """Allows the user to choose the
        dir with the VALSRC surfaces, then updates the
        VALSRC entry box with the selected dir path"""

        Valsrc = self.VALSRC_F.get()
        VALSRC_Filedir = filedialog.askdirectory(title='Select VALSRC folder' +
                                               'Directory', initialdir=Valsrc)
        self.VALSRC_F.set(VALSRC_Filedir)


    def Search_DTMFolder(self):
        Valsrc = self.DTM_DIR.get()
        VALSRC_Filedir = filedialog.askdirectory(title='Select VALSRC folder' +
                                               'Directory', initialdir=Valsrc)
        self.DTM_DIR.set(VALSRC_Filedir)



    def Search_QC_OUT(self): ## Not running Code
        """Allows the user to set the
        Output dir for QCTools and CATools"""

        OUTPUT_QC = filedialog.askdirectory(title='Select QC Tools Output Folder')
        OUTPUT_QC = OUTPUT_QC.replace("/", "\\")
        self.QC_OUT.set(OUTPUT_QC)


    def Search_ENC_Dir(self):  ## Not running Code
        """Allows the user to choose the
        ENC Directory for input into CATools"""

        ENC_DIR = filedialog.askdirectory(title='Select QC Tools Output Folder')
        ENC_DIR = ENC_DIR.replace("/", "\\")
        self.ENC_DIR.set(ENC_DIR)


    def Search_TrackLines (self):
        """Search for Trackline Folder"""
        Dir = filedialog.askdirectory(initialdir = "/", title='Select Track Line Directory')
        self.TL_Dir.set(Dir)

        TL_Dir_list = listdir(Dir)

        self.listbox.delete(0,'end')
        for item in TL_Dir_list:
            if not item.startswith('JD') and not item.endswith(".rawdataindex"): 
                self.listbox.insert(END, item)


    def Save_Par(self):
        """"Allows user to save all CHSython Parameters to a CSV file to be
        loaded on application startup"""

        chdir(owd) ## Application Dir

        ## General Parameters
        RAW = self.RAW_f.get() ## RAW File Dir
        HDCS = self.HDCS_d.get() ## HDCS_Data Dir
        PROJECT = self.PROJECT_n.get() ## Project Name
        VESSEL = self.VESSEL_n.get() ## Vessel Config File
        CRS = self.CRS_op.get() ## Project CRS
        CRS2 = self.CRS_Import.get() ## Raw File CRS
        JULIAN = self.JULIAN_d.get() ## Julian Day of survey RAW Files
        YEAR = self.Year.get() ## Year of Survey
        OUT = self.OUT_F.get() ## Output folder for Caris Batch cmd Output
        if self.CONVERT_N.get()==1: ## Convert Navigation check box from Import to HIPS Proccess
            CONNAV = '1'
        else:
            CONNAV='0'

        ## Save General Parameters to Parameters.txt
        GenPar_List = [RAW, HDCS, PROJECT, VESSEL, CRS, JULIAN, YEAR, CONNAV, OUT, CRS2,'N/A','N/A']
        Parameters = pd.read_csv('Parameters.txt', delimiter=',', header=None)
        Parameters.iloc[0] = GenPar_List
        Parameters.to_csv('Parameters.txt', mode='w', index=False, header=False)

        ## Auxillairy Parameters
        if self.ALLOW_P.get()==1: ## Allow Partially Covered
            ApC = '1'
        else:
            ApC = '0'
        MaG = self.MAG.get() ## Maximum Allowable Gap
        CrsAux = self.CRS_POS.get()

        if self.A_T.get()==2:
            AUX_F3 = self.AUX_F3.get()
            AUX_F2 = self.AUX_F2.get()
            App_List1 = [ApC, MaG,'N/A',AUX_F2,AUX_F3,CrsAux,'N/A','N/A','N/A','N/A','N/A','N/A']
        else:
            AUX_F = self.AUX_F.get() ## Aux File Directory
            App_List1 = [ApC, MaG, AUX_F, 'N/A','N/A',CrsAux,'N/A','N/A','N/A','N/A','N/A','N/A']
        
        ## Save General POS/SBET/RMS Parameters to Parameters.txt
        Parameters = pd.read_csv('Parameters.txt', delimiter=',', header=None)
        Parameters.iloc[1] = App_List1
        Parameters.to_csv('Parameters.txt', mode='w', index=False, header=False)

        if self.A_T.get()==1 or self.A_T.get()==2:
            if self.NAV.get()==1: ## Navigation
                N = '1'
            else:
                N ='0'
            G = self.GYRO.get() ## Gyro
            P = self.PITCH.get() ## Pitch
            R = self.ROLL.get() ## Roll
            GPSH = self.GPS_H.get() ## GPSH
            DH = self.D_H.get() ## Delayed Heave
            N_RMS = self.NAV_RMS.get() ## Naviagtion RMS
            G_RMS = self.GYRO_RMS.get() ## Gyro RMS
            P_RMS = self.PITCH_RMS.get() ## Pitch RMS
            R_RMS = self.ROLL_RMS.get() ## Roll RMS
            GPS_RMS = self.GPSH_RMS.get() ## GPSH RMS
            D_RMS = self.DH_RMS.get() ## Delayed Heave RMS

            ## Save POS/SBET/RMS Parameters to Parameters.txt
            App_List2 = [N, G, P, R, GPSH, DH, N_RMS, G_RMS, P_RMS, R_RMS, GPS_RMS, D_RMS]
            Parameters = pd.read_csv('Parameters.txt', delimiter=',', header=None)
            Parameters.iloc[2] = App_List2
            Parameters.to_csv('Parameters.txt', mode='w', index=False, header=False)

            ## Save type of postions data to apply in Import to Applanix Proccess
            if self.POS_GYRO.get()==1:
                Gc = 1
            else:
                Gc = 0

            if  self.POS_PITCH.get==1:
                Pc = 1
            else:
                Pc = 0

            if self.POS_ROLL.get()==1:
                Rc = 1
            else:
                Rc = 0

            if self.POS_GPSH.get()==1:
                GPSHc = 1
            else:
                GPSHc = 0

            if self.POS_DH.get()==1:
                DHc = 1
            else:
                DHc = 0

            if self.POS_NRMS.get()==1:
                NRMSc = 1
            else:
                NRMSc = 0

            if self.POS_GRMS.get()==1:
                GRMSc = 1
            else:
                GRMSc= 0

            if self.POS_PRMS.get()==1:
                PRMSc = 1
            else:
                PRMSc = 0

            if self.POS_RRMS.get()==1:
                RRMSc = 1
            else:
                RRMSc = 0

            if self.POS_GPSHRMS.get()==1:
               GPSHRMSc = 1
            else:
                GPSHRMSc = 0

            if self.POS_DHRMS.get()==1:
                DHRMSc = 1
            else:
                DHRMSc = 0

            App_List3 = [Gc, Pc, Rc, GPSHc, DHc, NRMSc, GRMSc, PRMSc, RRMSc, GPSHRMSc, DHRMSc, 'N/A']
            Parameters = pd.read_csv('Parameters.txt', delimiter=',', header=None, dtype=object)
            Parameters.iloc[12] = App_List3
            Parameters.to_csv('Parameters.txt', mode='w', index=False, header=False)


        ## RAW Sonar Parameters
        ## Kongsberg .all
        if self.S_T.get()==1:
            NAV_D = self.Nav_D.get() ## Navigation Device
            GPSH_D = self.GPSH_D.get() ## GPSH Device
            Heave_D = self.Heave_D.get() ## Heave Device
            Heading_D = self.Heading_D.get() ## Heading Device
            GPS_T = self.GPS_T.get() ## GPS Time
            Pitch_D = self.Pitch_D.get() ## Pitch Device
            Roll_D = self.Roll_D.get() ## Roll Device
            SSP_D = self.SSP_D.get() ## Surface Sound Speed Device

            ## Save Kongsberg .all Parameters to Parameters.txt
            Raw_List = [NAV_D, GPSH_D, Heave_D, Heading_D, GPS_T, Pitch_D, Roll_D, SSP_D,'N/A','N/A','N/A','N/A']
            Parameters = pd.read_csv('Parameters.txt', delimiter=',', header=None)
            Parameters.iloc[3] = Raw_List
            Parameters.to_csv('Parameters.txt', mode='w', index=False, header=False)

        elif self.S_T.get()==2:
            ## R2Sonic .gsf
            D_S = self.D_S.get() ## Depth Source
            IN_OFF = self.IN_OFF.get() ## Include Offline
            REJ_OFF = self.REJ_OFF.get() ## Reject Offline

            ## Save R2Sonic .gsf Parameters to Parameters.txt
            Raw_List = [D_S, IN_OFF, REJ_OFF,'N/A','N/A','N/A','N/A','N/A','N/A','N/A','N/A','N/A']
            Parameters = pd.read_csv('Parameters.txt', delimiter=',', header=None)
            Parameters.iloc[4] = Raw_List
            Parameters.to_csv('Parameters.txt', mode='w', index=False, header=False)

        elif self.S_T.get()==3:
            ## Triton .xtf
            NAV_DX = self.Nav_DX.get() ## Navigation Device
            GPSH_DX = self.GPSH_DX.get() ## GPS Height Device
            M_D = self.M_D.get() ## Motion Device
            C_B = self.C_B.get() ## Convert Bathymetry
            Heading_DX = self.Heading_DX.get() ## Heading Device
            CONV_SS = self.CONV_SS.get() ## Convert Side Scan
            SSWF = self.SSWF.get() ## Side Scan Weighting Factor
            SS_NAV = self.SS_NAV.get() ## Side Scan Navigation Device
            SS_HEAD = self.SS_HEAD.get() ## Side Scan Heading Device
            TIME_S = self.TIME_S.get() ## Time Stamps

            ## Save Triton .xtf Parameters to Parameters.txt
            Raw_List = [NAV_DX, GPSH_DX, M_D, C_B, Heading_DX, CONV_SS, SSWF, SS_NAV, SS_HEAD, TIME_S,'N/A','N/A']
            Parameters = pd.read_csv('Parameters.txt', delimiter=',', header=None)
            Parameters.iloc[5] = Raw_List
            Parameters.to_csv('Parameters.txt', mode='w', index=False, header=False)

        elif self.S_T.get()==4:
            ## Teledyne .s7k
            CB = self.CB.get() ## Convert Bathymetry
            NAV_D = self.NAV_D.get() ## Navigation Device
            HEAD_D = self.HEAD_D.get() ## Heading Device
            MOTION_D = self.MOTION_D.get() ## Motion Device
            SWATH_D = self.SWATH_D.get() ## Swath Device

            ## Save Teledyne .s7k Parameters to Parameters.txt
            Raw_List = [CB, NAV_D, HEAD_D, MOTION_D, SWATH_D,'N/A','N/A','N/A','N/A','N/A','N/A','N/A']
            Parameters = pd.read_csv('Parameters.txt', delimiter=',', header=None)
            Parameters.iloc[15] = Raw_List
            Parameters.to_csv('Parameters.txt', mode='w', index=False, header=False)

        elif self.S_T.get()==5:
            NAV_D = self.Nav_D.get() ## Navigation Device
            GPSH_D = self.GPSH_D.get() ## GPSH Device
            Heave_D = self.Heave_D.get() ## Heave Device
            Heading_D = self.Heading_D.get() ## Heading Device
            Pitch_D = self.Pitch_D.get() ## Pitch Device
            Roll_D = self.Roll_D.get() ## Roll Device
            DelHeave_D = self.DelHeave_D.get() ## Delayed Heave Device
            GPS_T = self.GPS_T.get()

            ## Save Kongsberg .all Parameters to Parameters.txt
            Raw_List = [NAV_D, GPSH_D, Heave_D, Heading_D, Pitch_D, Roll_D, DelHeave_D, GPS_T, 'N/A','N/A','N/A','N/A']
            Parameters = pd.read_csv('Parameters.txt', delimiter=',', header=None)
            Parameters.iloc[16] = Raw_List
            Parameters.to_csv('Parameters.txt', mode='w', index=False, header=False)

        ## Tide Parameters
        if self.T_T.get()==1:
            ## Compute GPS Tide
            C_GPS_ADJ = self.C_GPS_ADJ.get() ## Compute GPS Tide Adjustment
            SD_OFF = self.SD_OFF.get() ##
            M_F = self.M_F.get() ## Tide Model File
            W_L = self.W_L.get() ## Water Level

            ## Check if Model File is Raster (.Csar) or Text File (.txt)
            if (M_F.endswith('.txt') or M_F.endswith('.csv')
                or M_F.endswith('.xyz')):
                INFO_F = self.INFO_F.get() ## Tide Model Info File
                INFO_CRS = self.INFO_CRS.get() ## Tide Model CRS
            else:
                INFO_F = ('N/A')
                INFO_CRS = ('N/A')

            ## Save Compute GPS Tide Parameters to Parameters.txt
            GPST_List = [C_GPS_ADJ, SD_OFF, M_F, INFO_F,  INFO_CRS, W_L,'N/A','N/A','N/A','N/A','N/A','N/A']
            Parameters = pd.read_csv('Parameters.txt', delimiter=',', header=None)
            Parameters.iloc[7] = GPST_List
            Parameters.to_csv('Parameters.txt', mode='w', index=False, header=False)

        elif self.T_T.get()==2:
            if not self.T_F.get():
                pass

            ## Observed/ Predicted Tides
            else:
                T_F = self.T_F.get() ## Tide File
                W_Ave = self.W_Ave.get() ## Wieghted Ave
                COMP_Errors = self.COMP_Errors.get() ## Compute Errors

                ## Save Tide Parameters to Parameters.txt
                Tides_List = [T_F, W_Ave, COMP_Errors,'N/A','N/A','N/A','N/A','N/A','N/A','N/A', 'N/A', 'N/A']
                Parameters = pd.read_csv('Parameters.txt', delimiter=',', header=None, dtype=object)
                Parameters.iloc[6] = Tides_List
                Parameters.to_csv('Parameters.txt', mode='w', index=False, header=False)

        ## TPU Parameters
        if self.COMP_TPU.get()==1:
            ## Compute TPU
            TIDE_M = self.TIDE_M.get() ## Measured Tide
            SV_M = self.SV_M.get() ## Measured Sound Velocity
            SS_V = self.SS_V.get() ## Surface Sound Velocity
            S_N = self.S_N.get() ## Navigation Source
            S_G = self.S_G.get() ## Gyro Source
            S_S = self.S_S.get() ## Sonar Source
            S_P = self.S_P.get() ## Pitch Source
            S_R = self.S_R.get() ## Roll Source
            S_H = self.S_H.get() ## Heave Source
            S_Tide = self.S_Tide.get() ## Tide Source
            ## Merge
            H_Merged = self.H_MERGED.get() ## Heave Type
            V_REF = self.VERT_REF.get() ## Vertical Reference Meta Data

            ## Save TPU Parameters to Parameters.txt
            TPU_List = [TIDE_M, SV_M, SS_V, S_N, S_G, S_S, S_P, S_R, S_H, S_Tide, 'N/A','N/A']
            Parameters = pd.read_csv('Parameters.txt', delimiter=',', header=None)
            Parameters.iloc[9] = TPU_List
            Parameters.to_csv('Parameters.txt', mode='w', index=False, header=False)

            ## Save Merged & TPU Parameters to Parameters.txt
            Parameters = pd.read_csv('Parameters.txt', delimiter=',', header=None)
            Parameters.iloc[8,0] = H_Merged
            Parameters.iloc[8,1] = V_REF
            Parameters.to_csv('Parameters.txt', mode='w', index=False, header=False)

        ## Surface Gridding Parameters
        if self.GRID.get()==1 or self.GRID.get()==2:
            RES = self.RES.get()
            GRID_DIR = self.GRID_DIR.get()
            IHO_O = self.IHO_ORDER.get()

            ## Save Gridding Parameters to Parameters.txt
            GRID_List = [RES, IHO_O, GRID_DIR, 'N/A','N/A','N/A','N/A','N/A','N/A','N/A', 'N/A', 'N/A']
            Parameters = pd.read_csv('Parameters.txt', delimiter=',', header=None)
            Parameters.iloc[10] = GRID_List
            Parameters.to_csv('Parameters.txt', mode='w', index=False, header=False)

        ## CATools Parameters
        if self.CATOOLS.get()==1:
            CA_List = [self.CA_algo.get(), self.CA_mode.get(), self.CA_input_mode.get(), self.CA_ENC_var.get(), self.CA_OUT_var.get(), '15.0', '0.3', '10', 'N/A', 'N/A', 'N/A', 'N/A']
            Parameters = pd.read_csv('Parameters.txt', delimiter=',', header=None, dtype=object)
            Parameters.loc[17] = CA_List
            Parameters.to_csv('Parameters.txt', mode='w', index=False, header=False)

        if self.D_R.get() == 1:
            ## Reporting Parameters to Parameters.txt
            Daily = self.REP_F.get() ## Daily Report Spreadsheet
            Weekly = self.WREP_F.get() ## Weekly Report Spreadsheet
            Week = self.WeekNO.get() ## Week number/name
            IHOOrder = self.IHO_ORDER2.get() ## IHO Order
            QC = 'Yes' if self.TPUQC.get() == 1 else 'No' ## QC Type (Surface or HIPS)
            
            ## Reporting Parameters to Parameters.txt
            Reporting_List = ['N/A',Daily,Weekly,IHOOrder,Week,QC,'N/A','N/A','N/A','N/A','N/A','N/A']
            Parameters = pd.read_csv('Parameters.txt', delimiter=',', header=None)
            Parameters.iloc[14] = Reporting_List
            Parameters.to_csv('Parameters.txt', mode='w', index=False, header=False)

        self.Exit = 'False'
        self.popup_SavePar()  ## Provide output window to User


    def popup_SavePar(self):
        """Creates a window alerting the user that all parameters
        have been saved"""

        msg = "Parameters Are Saved"
        popup= Tk()


        def leavemini():
            if self.Exit == 'True':
                popup.destroy()
                root.destroy()
            else:
                 popup.destroy()

        popup.wm_title("Save Parameteres")
        label = Label(popup, text=msg)
        label.grid(row=1, column=1)
        B1 = Button(popup, text="Okay", command = leavemini)
        B1.grid(row=2, column=1)
        popup.mainloop()


    def Load_Auxiliary_Par(self):
        """Loads deafult user input options for Importing Auxilliary Data"""

        chdir(owd) ##Application Dir

        STATE = 'normal'

        ##Creating General Import Auxilliary Data User Input Options
        Aux_op = LabelFrame(frame3, text="Applanix Import", foreground="blue")
        Aux_op.grid(row=0, column=0, padx=1, sticky=N)

        ## Applanix Dir
        self.AUX_F = StringVar()
        self.AUX_f = Entry(Aux_op, width=38, textvariable=self.AUX_F)

        ## Allow Partial Covered
        self.ALLOW_P = IntVar()
        self.ALLOW_n = Checkbutton(Aux_op, variable=self.ALLOW_P,
                                   text= "Allow Partially Covered", state='disabled')
        self.ALLOW_n.grid(row=0, column=0, sticky=W)

        ## Max Allowable GAP (Default 2sec)
        self.MAG = StringVar()
        self.Mag = Entry(Aux_op, width=7, textvariable=self.MAG, state=STATE)
        self.MAG_text = Label(Aux_op, text="Maximum Allowable Gap")
        self.MAG_text.grid(row=1, column=0, sticky=W)
        self.Mag.grid(row=1, column=1, sticky=W, padx=2)

        self.Refweek = DateEntry(Aux_op, width=25, background= "magenta3", foreground= "white", bd=2)
        self.Refweek_text = Label(Aux_op, text="GPS Refference Week")
        self.Refweek_text.grid(row=2, column=0, sticky=W)
        self.Refweek.grid(row=2, column=1, sticky=W, padx=2)

        ##Project and Hips Data CSRS
        self.CRS_POS = StringVar()
        crs_POS = ['ITRF2014: EPSG:7912@2010',
                  'NAD83(CSRS)v6: EPSG:8252@2010']

        self.CRS_pos = ttk.Combobox(Aux_op, values=crs_POS, width=35, textvariable=self.CRS_POS)
        self.CRS_pos_text = Label(Aux_op, text="Choose CRS")
        self.CRS_pos_text.grid(row=6, column=0, sticky=W)
        self.CRS_pos.grid(row=6, column=1, sticky=W+E, padx=0)

        ## Setting default Auxilliary Parameters
        Parameters = pd.read_csv('Parameters.txt', delimiter=',', header=None)
        APC = int(Parameters.iloc[1,0])
        M_AG = Parameters.iloc[1,1]
        crs_pos = Parameters.iloc[1,5]
        self.ALLOW_P.set(APC)
        self.MAG.set(M_AG)
        self.CRS_POS.set(crs_pos)
        

        self.Aux_msg = LabelFrame(frame3, text="Applanix User Warning", foreground="blue")
        self.Aux_msg.grid(row=0, column=1, padx=1, sticky=N+W)

        msg = ('For regular processing\nleave default values 0sec\n' +
               'and an allowable gap of\n2sec only change when\n' +
               'errors or warnings arise.\n' +
               'For SBET ensure Navigation\n' +
               'is selected.\n') ## User Reminder for Proccessing

        self.User_Msg = Text(self.Aux_msg, width=28, height=7)
        self.User_Msg.insert(END, msg)
        self.User_Msg.config(state='disabled')
        self.User_Msg.grid(row=0, column=0, padx=1, sticky=W)

        msg2 = ('Please check POS or \n' +
                'SBET CRS \n' +
                'MarineStar - \n' +
                'ITRF 2014 Epoch 2010 \n' +
                'Cannet - NAD83(CSRS)v6 \n' +
                'Epoch 2010')

        self.User_Msg2 = Text(self.Aux_msg, width=28, height=6)
        self.User_Msg2.insert(END, msg2)
        self.User_Msg2.config(state='disabled')
        self.User_Msg2.grid(row=1, column=0, padx=1, sticky=W)


        ## User Inputs for POSMV Data
        if self.A_T.get()==1:

            self.AUX_F = StringVar()
            self.AUX_f = Entry(Aux_op, width=38, textvariable=self.AUX_F)
            self.AUX_text = Label(Aux_op, text="POS Files")
            self.AUX_text.grid(row=3, column=0, sticky=W)
            self.AUX_f.grid(row=3, column=1, sticky=W)
            self.Button_AUX = Button(Aux_op, text="...", height=0,
                                command=self.Search_Aux_Data)
            self.Button_AUX.grid(row=3, column=2, sticky=W, padx=2)


            ## Creating Import POSMV User Input Options
            self.POSMV_op = LabelFrame(frame3, text="Import POSMV", foreground="blue")
            self.POSMV_op.grid(row=2, column=0, padx=1, sticky=W)

            ## Navigation
            self.NAV = IntVar()
            self.Nav = Checkbutton(self.POSMV_op, variable=self.NAV,
                                   text= "Navigation")
            self.Nav.grid(row=1, column=0, sticky=W)

            ## Gyro
            self.GYRO = StringVar()
            self.Gyro = Entry(self.POSMV_op, width=7, textvariable=self.GYRO, state=STATE)
            self.Gyro.grid(row=2, column=1, sticky=W, padx=2)
            self.POS_GYRO = IntVar()
            self.POS_gyro = Checkbutton(self.POSMV_op, onvalue=1, offvalue=0, variable=self.POS_GYRO,
                                        command=None, text= "Gyro")
            self.POS_gyro.grid(row=2, column=0, sticky=W)

            ## Pitch
            self.PITCH = StringVar()
            self.Pitch = Entry(self.POSMV_op, width=7, textvariable=self.PITCH, state=STATE)
            self.Pitch.grid(row=3, column=1, sticky=W, padx=2)
            self.POS_PITCH = IntVar()
            self.POS_pitch = Checkbutton(self.POSMV_op, onvalue=1, offvalue=0, variable=self.POS_PITCH,
                                        command=None, text= "Pitch")
            self.POS_pitch.grid(row=3, column=0, sticky=W)

            ## Roll
            self.ROLL = StringVar()
            self.Roll = Entry(self.POSMV_op, width=7, textvariable=self.ROLL, state=STATE)
            self.Roll.grid(row=4, column=1, sticky=W, padx=2)
            self.POS_ROLL = IntVar()
            self.POS_roll = Checkbutton(self.POSMV_op, onvalue=1, offvalue=0, variable=self.POS_ROLL,
                                        command=None, text='Roll')
            self.POS_roll.grid(row=4, column=0, sticky=W)

            ## GPS Height
            self.GPS_H = StringVar()
            self.GPS_h = Entry(self.POSMV_op, width=7, textvariable=self.GPS_H, state=STATE)
            self.GPS_h.grid(row=5, column=1, sticky=W, padx=2)
            self.POS_GPSH = IntVar()
            self.POS_gpsh = Checkbutton(self.POSMV_op, onvalue=1, offvalue=0, variable=self.POS_GPSH,
                                        command=None, text='GPS Height')
            self.POS_gpsh.grid(row=5, column=0, sticky=W)

            ## Delayed Heave
            self.D_H = StringVar()
            self.D_h = Entry(self.POSMV_op, width=7, textvariable=self.D_H, state=STATE)
            self.D_h.grid(row=6, column=1, sticky=W, padx=2)
            self.POS_DH = IntVar()
            self.POS_dh = Checkbutton(self.POSMV_op, onvalue=1, offvalue=0, variable=self.POS_DH,
                                        command=None, text='Delayed Heave')
            self.POS_dh.grid(row=6, column=0, sticky=W)

            ## Navigation RMS
            self.NAV_RMS = StringVar()
            self.NAV_rms = Entry(self.POSMV_op, width=7, textvariable=self.NAV_RMS, state=STATE)
            self.NAV_rms.grid(row=7, column=1, sticky=W, padx=2)
            self.POS_NRMS = IntVar()
            self.POS_nrms = Checkbutton(self.POSMV_op, onvalue=1, offvalue=0, variable=self.POS_NRMS,
                                        command=None, text='Navigation RMS')
            self.POS_nrms.grid(row=7, column=0, sticky=W)

            ## Gyro RMS
            self.GYRO_RMS = StringVar()
            self.GYRO_rms = Entry(self.POSMV_op, width=7, textvariable=self.GYRO_RMS, state=STATE)
            self.GYRO_rms.grid(row=8, column=1, sticky=W, padx=2)
            self.POS_GRMS = IntVar()
            self.POS_grms = Checkbutton(self.POSMV_op, onvalue=1, offvalue=0, variable=self.POS_GRMS,
                                        command=None, text='Gyro RMS')
            self.POS_grms.grid(row=8, column=0, sticky=W)

            ## Pitch RMS
            self.PITCH_RMS = StringVar()
            self.PITCH_rms = Entry(self.POSMV_op, width=7, textvariable=self.PITCH_RMS, state=STATE)
            self.PITCH_rms.grid(row=9, column=1, sticky=W, padx=2)
            self.POS_PRMS = IntVar()
            self.POS_prms = Checkbutton(self.POSMV_op, onvalue=1, offvalue=0, variable=self.POS_PRMS,
                                        command=None, text='Pitch RMS')
            self.POS_prms.grid(row=9, column=0, sticky=W)

            ## Roll RMS
            self.ROLL_RMS = StringVar()
            self.ROLL_rms = Entry(self.POSMV_op, width=7, textvariable=self.ROLL_RMS, state=STATE)
            self.ROLL_rms.grid(row=10, column=1, sticky=W, padx=2)
            self.POS_RRMS = IntVar()
            self.POS_rrms = Checkbutton(self.POSMV_op, onvalue=1, offvalue=0, variable=self.POS_RRMS,
                                        command=None, text='Roll RMS')
            self.POS_rrms.grid(row=10, column=0, sticky=W)

            ## GPS Height RMS
            self.GPSH_RMS = StringVar()
            self.GPSH_rms = Entry(self.POSMV_op, width=7, textvariable=self.GPSH_RMS, state=STATE)
            self.GPSH_rms.grid(row=11, column=1, sticky=W, padx=2)
            self.POS_GPSHRMS = IntVar()
            self.POS_gpshrms = Checkbutton(self.POSMV_op, onvalue=1, offvalue=0, variable=self.POS_GPSHRMS,
                                        command=None, text='GPS Height RMS')
            self.POS_gpshrms.grid(row=11, column=0, sticky=W)

            ## Delayed Heave RMS
            self.DH_RMS = StringVar()
            self.DH_rms = Entry(self.POSMV_op, width=7, textvariable=self.DH_RMS, state=STATE)
            self.DH_rms.grid(row=12, column=1, sticky=W, padx=2)
            self.POS_DHRMS = IntVar()
            self.POS_dhrms = Checkbutton(self.POSMV_op, onvalue=1, offvalue=0, variable=self.POS_DHRMS,
                                        command=None, text='Delayed Heave RMS')
            self.POS_dhrms.grid(row=12, column=0, sticky=W)

            ## Reading defaults from saved inputs for POSMV
            Parameters = pd.read_csv('Parameters.txt', delimiter=',', header=None)
            Na = int(Parameters.iloc[2,0])
            G = Parameters.iloc[2,1]
            P = Parameters.iloc[2,2]
            R = Parameters.iloc[2,3]
            GPSH = Parameters.iloc[2,4]
            DH = Parameters.iloc[2,5]
            N_RMS = Parameters.iloc[2,6]
            G_RMS = Parameters.iloc[2,7]
            P_RMS = Parameters.iloc[2,8]
            R_RMS = Parameters.iloc[2,9]
            GPS_RMS = Parameters.iloc[2,10]
            D_RMS = Parameters.iloc[2,11]

            Gc = Parameters.iloc[12,0]
            Pc = Parameters.iloc[12,1]
            Rc = Parameters.iloc[12,2]
            GPSHc = Parameters.iloc[12,3]
            DHc = Parameters.iloc[12,4]
            N_RMSc = Parameters.iloc[12,5]
            G_RMSc = Parameters.iloc[12,6]
            P_RMSc = Parameters.iloc[12,7]
            R_RMSc = Parameters.iloc[12,8]
            GPS_RMSc = Parameters.iloc[12,9]
            D_RMSc = Parameters.iloc[12,10]

            ## Setting defaults from Parameters file for POSMV
            self.NAV.set(Na)
            self.GYRO.set(G)
            self.PITCH.set(P)
            self.ROLL.set(R)
            self.GPS_H.set(GPSH)
            self.D_H.set(DH)
            self.NAV_RMS.set(N_RMS)
            self.GYRO_RMS.set(G_RMS)
            self.PITCH_RMS.set(P_RMS)
            self.ROLL_RMS.set(R_RMS)
            self.GPSH_RMS.set(GPS_RMS)
            self.DH_RMS.set(D_RMS)

            self.POS_GYRO.set(Gc)
            self.POS_PITCH.set(Pc)
            self.POS_ROLL.set(Rc)
            self.POS_GPSH.set(GPSHc)
            self.POS_DH.set(DHc)
            self.POS_NRMS.set(N_RMSc)
            self.POS_GRMS.set(G_RMSc)
            self.POS_PRMS.set(P_RMSc)
            self.POS_RRMS.set(R_RMSc)
            self.POS_GPSHRMS.set(GPS_RMSc)
            self.POS_DHRMS.set(D_RMSc)

            A_F = Parameters.iloc[1,2]
            self.AUX_F.set(A_F)

            try:
                ## Forget the SBET & RMS Options
                self.SBET_RMS_op.grid_forget()
                self.AUX_f2.grid_forget()
                self.Button_AUX2.grid_forget()
                self.AUX_text2.grid_forget()
            except AttributeError:
                pass

        ## User Inputs for SBET/ RMS Data
        elif self.A_T.get()==2:

            self.AUX_F2 = StringVar()
            self.AUX_f2 = Entry(Aux_op, width=38, textvariable=self.AUX_F2)
            self.AUX_text2 = Label(Aux_op, text="RMS Files")
            self.AUX_text2.grid(row=4, column=0, sticky=W)
            self.AUX_f2.grid(row=4, column=1, sticky=W)
            self.Button_AUX2 = Button(Aux_op, text="...", height=0,
                              command=self.Search_Aux_Data2)
            self.Button_AUX2.grid(row=4, column=2, sticky=W, padx=2)

            self.AUX_F3 = StringVar()
            self.AUX_f3 = Entry(Aux_op, width=38, textvariable=self.AUX_F3)
            self.AUX3_text = Label(Aux_op, text="SBET Files")
            self.AUX3_text.grid(row=3, column=0, sticky=W)
            self.AUX_f3.grid(row=3, column=1, sticky=W)
            self.Button_AUX3 = Button(Aux_op, text="...", height=0,
                                  command=self.Search_Aux_Data3)
            self.Button_AUX3.grid(row=3, column=2, sticky=W, padx=2)


            ## Creating Import SBET User Input Options
            self.SBET_RMS_op = LabelFrame(frame3, text="Import SBET and RMS", foreground="blue")
            self.SBET_RMS_op.grid(row=2, column=0, padx=1, sticky=W)

            ## Navigation
            self.NAV = IntVar()
            self.Nav = Checkbutton(self.SBET_RMS_op, variable=self.NAV,
                                   text= "Navigation")
            self.Nav.grid(row=1, column=0, sticky=W)

            ## Gyro
            self.GYRO = StringVar()
            self.Gyro = Entry(self.SBET_RMS_op, width=7, textvariable=self.GYRO, state=STATE)
            self.Gyro.grid(row=2, column=1, sticky=W, padx=2)
            self.POS_GYRO = IntVar()
            self.POS_gyro = Checkbutton(self.SBET_RMS_op, onvalue=1, offvalue=0, variable=self.POS_GYRO,
                                        command=None, text= "Gyro")
            self.POS_gyro.grid(row=2, column=0, sticky=W)

            ## Pitch
            self.PITCH = StringVar()
            self.Pitch = Entry(self.SBET_RMS_op, width=7, textvariable=self.PITCH, state=STATE)
            self.Pitch.grid(row=3, column=1, sticky=W, padx=2)
            self.POS_PITCH = IntVar()
            self.POS_pitch = Checkbutton(self.SBET_RMS_op, onvalue=1, offvalue=0, variable=self.POS_PITCH,
                                        command=None, text= "Pitch")
            self.POS_pitch.grid(row=3, column=0, sticky=W)

            ## Roll
            self.ROLL = StringVar()
            self.Roll = Entry(self.SBET_RMS_op, width=7, textvariable=self.ROLL, state=STATE)
            self.Roll.grid(row=4, column=1, sticky=W, padx=2)
            self.POS_ROLL = IntVar()
            self.POS_roll = Checkbutton(self.SBET_RMS_op, onvalue=1, offvalue=0, variable=self.POS_ROLL,
                                        command=None, text='Roll')
            self.POS_roll.grid(row=4, column=0, sticky=W)

            ## GPS Height
            self.GPS_H = StringVar()
            self.GPS_h = Entry(self.SBET_RMS_op, width=7, textvariable=self.GPS_H, state=STATE)
            self.GPS_h.grid(row=5, column=1, sticky=W, padx=2)
            self.POS_GPSH = IntVar()
            self.POS_gpsh = Checkbutton(self.SBET_RMS_op, onvalue=1, offvalue=0, variable=self.POS_GPSH,
                                        command=None, text='GPS Height')
            self.POS_gpsh.grid(row=5, column=0, sticky=W)

            ## Delayed Heave
            self.D_H = StringVar()
            self.D_h = Entry(self.SBET_RMS_op, width=7, textvariable=self.D_H, state='normal')
            self.D_h.grid(row=6, column=1, sticky=W, padx=2)

            self.POS_DH = IntVar()
            self.POS_dh = Checkbutton(self.SBET_RMS_op, onvalue=1, offvalue=0, variable=self.POS_DH,
                                        command=None, text='Delayed Heave')
            self.POS_dh.grid(row=6, column=0, sticky=W)

            ## Navigation RMS
            self.NAV_RMS = StringVar()
            self.NAV_rms = Entry(self.SBET_RMS_op, width=7, textvariable=self.NAV_RMS, state=STATE)
            self.NAV_rms.grid(row=7, column=1, sticky=W, padx=2)
            self.POS_NRMS = IntVar()
            self.POS_nrms = Checkbutton(self.SBET_RMS_op, onvalue=1, offvalue=0, variable=self.POS_NRMS,
                                        command=None, text='Navigation RMS')
            self.POS_nrms.grid(row=7, column=0, sticky=W)

            ## Gyro RMS
            self.GYRO_RMS = StringVar()
            self.GYRO_rms = Entry(self.SBET_RMS_op, width=7, textvariable=self.GYRO_RMS, state=STATE)
            self.GYRO_rms.grid(row=8, column=1, sticky=W, padx=2)
            self.POS_GRMS = IntVar()
            self.POS_grms = Checkbutton(self.SBET_RMS_op, onvalue=1, offvalue=0, variable=self.POS_GRMS,
                                        command=None, text='Gyro RMS')
            self.POS_grms.grid(row=8, column=0, sticky=W)

            ## Pitch RMS
            self.PITCH_RMS = StringVar()
            self.PITCH_rms = Entry(self.SBET_RMS_op, width=7, textvariable=self.PITCH_RMS, state=STATE)
            self.PITCH_rms.grid(row=9, column=1, sticky=W, padx=2)
            self.POS_PRMS = IntVar()
            self.POS_prms = Checkbutton(self.SBET_RMS_op, onvalue=1, offvalue=0, variable=self.POS_PRMS,
                                        command=None, text='Navigation RMS')
            self.POS_prms.grid(row=9, column=0, sticky=W)

            ## Roll RMS
            self.ROLL_RMS = StringVar()
            self.ROLL_rms = Entry(self.SBET_RMS_op, width=7, textvariable=self.ROLL_RMS, state=STATE)
            self.ROLL_rms.grid(row=10, column=1, sticky=W, padx=2)
            self.POS_RRMS = IntVar()
            self.POS_rrms = Checkbutton(self.SBET_RMS_op, onvalue=1, offvalue=0, variable=self.POS_RRMS,
                                        command=None, text='Roll RMS')
            self.POS_rrms.grid(row=10, column=0, sticky=W)

            ## GPS Height RMS
            self.GPSH_RMS = StringVar()
            self.GPSH_rms = Entry(self.SBET_RMS_op, width=7, textvariable=self.GPSH_RMS, state=STATE)
            self.GPSH_rms.grid(row=11, column=1, sticky=W, padx=2)
            self.POS_GPSHRMS = IntVar()
            self.POS_gpshrms = Checkbutton(self.SBET_RMS_op, onvalue=1, offvalue=0, variable=self.POS_GPSHRMS,
                                        command=None, text='GPS Height RMS')
            self.POS_gpshrms.grid(row=11, column=0, sticky=W)

            ## Delayed Heave RMS
            self.DH_RMS = StringVar()
            self.DH_rms = Entry(self.SBET_RMS_op, width=7, textvariable=self.DH_RMS, state=STATE)
            self.DH_rms.grid(row=12, column=1, sticky=W, padx=2)
            self.POS_DHRMS = IntVar()
            self.POS_dhrms = Checkbutton(self.SBET_RMS_op, onvalue=1, offvalue=0, variable=self.POS_DHRMS,
                                        command=None, text='Delayed Heave RMS')
            self.POS_dhrms.grid(row=12, column=0, sticky=W)

            ## Reading defaults inputs for SBET
            Parameters = pd.read_csv('Parameters.txt', delimiter=',', header=None)
            Na = int(Parameters.iloc[2,0])
            G = Parameters.iloc[2,1]
            P = Parameters.iloc[2,2]
            R = Parameters.iloc[2,3]
            GPSH = Parameters.iloc[2,4]
            DH = Parameters.iloc[2,5]

            Gc = Parameters.iloc[12,0]
            Pc = Parameters.iloc[12,1]
            Rc = Parameters.iloc[12,2]
            GPSHc = Parameters.iloc[12,3]
            DHc = Parameters.iloc[12,4]

            ## Setting defaults from Parameter file for SBET
            self.NAV.set(Na)
            self.GYRO.set(G)
            self.PITCH.set(P)
            self.ROLL.set(R)
            self.GPS_H.set(GPSH)
            self.D_H.set(DH)

            self.POS_GYRO.set(Gc)
            self.POS_PITCH.set(Pc)
            self.POS_ROLL.set(Rc)
            self.POS_GPSH.set(GPSHc)
            self.POS_DH.set(DHc)

            ## Reading the defaults inputs for RMS
            Parameters = pd.read_csv('Parameters.txt', delimiter=',', header=None)
            N_RMS = Parameters.iloc[2,6]
            G_RMS = Parameters.iloc[2,7]
            P_RMS = Parameters.iloc[2,8]
            R_RMS = Parameters.iloc[2,9]
            GPS_RMS = Parameters.iloc[2,10]
            D_RMS = Parameters.iloc[2,11]

            N_RMSc = Parameters.iloc[12,5]
            G_RMSc = Parameters.iloc[12,6]
            P_RMSc = Parameters.iloc[12,7]
            R_RMSc = Parameters.iloc[12,8]
            GPS_RMSc = Parameters.iloc[12,9]
            D_RMSc = Parameters.iloc[12,10]

            ## Setting defaults from Parameter file for RMS
            self.NAV_RMS.set(N_RMS)
            self.GYRO_RMS.set(G_RMS)
            self.PITCH_RMS.set(P_RMS)
            self.ROLL_RMS.set(R_RMS)
            self.GPSH_RMS.set(GPS_RMS)
            self.DH_RMS.set(D_RMS)

            self.POS_NRMS.set(N_RMSc)
            self.POS_GRMS.set(G_RMSc)
            self.POS_PRMS.set(P_RMSc)
            self.POS_RRMS.set(R_RMSc)
            self.POS_GPSHRMS.set(GPS_RMSc)
            self.POS_DHRMS.set(D_RMSc)

            ## ToolTips For Applanix Data
            A_F2 = Parameters.iloc[1,3]
            self.AUX_F2.set(A_F2)
            A_F3 = Parameters.iloc[1,4]
            self.AUX_F3.set(A_F3)

            try:
                ## Forget the POSMV Options
                self.POSMV_op.grid_forget()

            except AttributeError:
                pass


    def split_Project_Name(self):
        """Splits the Project name into 2 character strings
        Projectno_Location_Year_Vessel_Sytstem
        1. Projectno_Location_Year 2. Vessel_System"""

        Project_N = self.PROJECT_n.get()

        if not Project_N:
            messagebox.showerror("Error", "Project name is empty.")
            return None, None, None
        
        P_split = Project_N.split('_')

        if len(P_split) < 5:
            messagebox.showerror("Error", f"Invalid project name:\n\n{Project_N}\n\nExpected format:\nProject_Location_Year_Vessel_System")
            return None, None, None
        
        try:
            Project = "_".join(P_split[:3])
            HIPSFILE = "_".join(P_split[3:5])
            return Project, HIPSFILE, P_split
        
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error:\n{e}")
            return None, None, None


    def Import_Auxiliary(self):
        """"""
        ## Get Default Values from Use Input
        PH = self.split_Project_Name()
        Project_N = PH[0]
        HIPSFILE = PH[1]

        HDCS_Folder = self.HDCS_D.get() ## HDCS_Data Dir
        crs = self.CRS_POS.get() ## Coordinate Ref System
        CRS = crs.partition(": ")[2]
        Vessel_F = self.VESSEL_N.get() ## Vessel File
        Vessel = path.basename(Vessel_F)
        Vessel = path.splitext(Vessel)[0]
        Year = self.Year.get() ## Survey Year
        JD = self.JULIAN_D.get() ## Julian Day
        Out = self.OUT_F.get() ## Processing Window Output Dir
        Allow_P = self.ALLOW_P.get() ## Allow Partially Covered Data
        Maximum_Gap = self.MAG.get() ## Maximum Allowable Gap
        AUX_F = self.AUX_F.get() ## AUX Dir
        REFWEEK = pd.to_datetime(DATES.datetime.strptime((self.Refweek.get()), "%m/%d/%y").strftime("%Y-%m-%d")).date() ## GPS Refference Week

        ## Getting Import POSMV Parameters
        if self.A_T.get()==1:
            L_POSF = listdir(AUX_F)

            Nav = self.NAV.get() ## Navigation
            Gyro = self.GYRO.get() ## Gyro
            Pitch = self.PITCH.get() ## Pitch
            Roll = self.ROLL.get() ## Roll
            GPS_h = self.GPS_H.get() ## GPS Height
            D_h = self.D_H.get() ## Delayed
            N_rms = self.NAV_RMS.get() ## Navigation RMS
            G_rms = self.GYRO_RMS.get() ## Gyro RMS
            P_rms = self.PITCH_RMS.get() ## Pitch RMS
            R_rms = self.ROLL_RMS.get() ## Roll RMS
            GPSH_rms = self.GPSH_RMS.get() ## GPS Height RMS
            DH_rms = self.DH_RMS.get() ## Delayed Heave RMS


            ## Creating Import_Aux.bat with POSMV Parameters
            A_Format = ('APP_POSMV')## Import Fromate - Applanix POSMV

            with open("Import_Aux_POSMV.bat", "w") as Import:
                    Import.write('@ECHO OFF' + '\n')
                    Import.write('@ECHO Importing POS' + '\n')
                    Import.write('cd '+ Caris + '\n')

                    Import.write('carisbatch --run ImportHIPSFromAuxiliary --input-format ' +
                                A_Format +  ' --input-crs ' + CRS + ' --maximum-gap ' +
                                Maximum_Gap + ' --reference-week ' +  str(REFWEEK) + ' --allow-partial')
                    if Nav==1:
                        Import.write(' --navigation ')
                    if self.POS_GYRO.get()==1:
                         Import.write(' --gyro ' + Gyro)
                    if  self.POS_PITCH.get==1:
                        Import.write( ' --pitch '+ Pitch)
                    if self.POS_ROLL.get()==1:
                        Import.write(' --roll ' + Roll)
                    if self.POS_GPSH.get()==1:
                        Import.write(' --gps-height ' + GPS_h)
                    if self.POS_DH.get()==1:
                        Import.write(' --delayed-heave ' + D_h)
                    if self.POS_NRMS.get()==1:
                        Import.write(' --navigation-rms ' + N_rms)
                    if self.POS_GRMS.get()==1:
                        Import.write(' --gyro-rms ' + G_rms)
                    if self.POS_PRMS.get()==1:
                        Import.write(' --pitch-rms ' + P_rms)
                    if self.POS_RRMS.get()==1:
                        Import.write(' --roll-rms ' + R_rms)
                    if self.POS_GPSHRMS.get()==1:
                        Import.write(' --gps-height-rms ' + GPSH_rms)
                    if self.POS_DHRMS.get()==1:
                        Import.write(' --delayed-heave-rms ' + DH_rms)

                    for file in L_POSF:
                        Import.write(' "' + AUX_F + '/' + file + '"')
                    Import.write(r' file:///' + HDCS_Folder + '/' + HIPSFILE + '/' + HIPSFILE + '.hips?Vessel=' +
                                 Vessel + ';Day=' + str(Year) + '-' + str(JD))
                    Import.write(' > ' + Out + '/' + JD + '/2.Import_POSMV' + JD + '_' + Year + '.txt' + '\n')

            ## Import Auxillairy Data using Caris Batch Through cmd
            p = S.Popen(['Import_Aux_POSMV.bat'])
            p.communicate()

        ## Getting Import SBET and RMS Parameters
        if self.A_T.get()==2:
            SBETF = self.AUX_F3.get()
            RMSF = self.AUX_F2.get()

            Nav = self.NAV.get() ## Navigation
            Gyro = self.GYRO.get() ## Gyro
            Pitch = self.PITCH.get() ## Pitch
            Roll = self.ROLL.get() ## Roll
            GPS_h = self.GPS_H.get() ## GPS Height
            D_h = self.D_H.get() ## Delayed
            N_rms = self.NAV_RMS.get() ## Navigation RMS
            G_rms = self.GYRO_RMS.get() ## Gyro RMS
            P_rms = self.PITCH_RMS.get() ## Pitch RMS
            R_rms = self.ROLL_RMS.get() ## Roll RMS
            GPSH_rms = self.GPSH_RMS.get() ## GPS Height RMS
            DH_rms = self.DH_RMS.get() ## Delayed Heave RMS

            ## Creating Import_Aux.bat with SBET Parameters
            A_Format = ('APP_SBET')
            A_Format2 = ('APP_RMS')
            with open("Import_Aux_SBET_RMS.bat", "w") as Import:
                    Import.write('@ECHO OFF' + '\n')
                    Import.write('@ECHO Importing SBET and RMS' + '\n')
                    Import.write('cd '+ Caris + '\n')

                    Import.write('carisbatch --run ImportHIPSFromAuxiliary --input-format ' +
                                 A_Format +  ' --input-crs ' + CRS + ' --maximum-gap ' +
                                 Maximum_Gap + ' --reference-week ' +  str(REFWEEK) + ' --allow-partial')
                    if Nav==1:
                        Import.write(' --navigation ')
                    if self.POS_GYRO.get()==1:
                         Import.write(' --gyro ' + Gyro)
                    if  self.POS_PITCH.get==1:
                        Import.write( ' --pitch '+ Pitch)
                    if self.POS_ROLL.get()==1:
                        Import.write(' --roll ' + Roll)
                    if self.POS_GPSH.get()==1:
                        Import.write(' --gps-height ' + GPS_h)

                    Import.write(' ' + SBETF)
                    Import.write(r' file:///' + HDCS_Folder + '/' + HIPSFILE + '/' + HIPSFILE + '.hips')
                    Import.write(' > ' + Out + '/' + JD + '/2.Import_SBET' + JD + '_' + Year + '.txt' + '\n')

            ## Creating RMS Parameters
                    Import.write('carisbatch --run ImportHIPSFromAuxiliary --input-format ' +
                                 A_Format2)
                    if self.POS_NRMS.get()==1:
                        Import.write(' --navigation-rms ' + N_rms)
                    if self.POS_GRMS.get()==1:
                        Import.write(' --gyro-rms ' + G_rms)
                    if self.POS_PRMS.get()==1:
                        Import.write(' --pitch-rms ' + P_rms)
                    if self.POS_RRMS.get()==1:
                        Import.write(' --roll-rms ' + R_rms)
                    if self.POS_GPSHRMS.get()==1:
                        Import.write(' --gps-height-rms ' + GPSH_rms)

                    Import.write(' ' + RMSF)
                    Import.write(r' file:///' + HDCS_Folder + '/' + HIPSFILE + '/' + HIPSFILE + '.hips')
                    Import.write(' > ' + Out + '/' + JD + '/2.Import_RMS' + JD + '_' + Year + '.txt' + '\n')

            p = S.Popen(['Import_Aux_SBET_RMS.bat'])
            p.communicate()


    def Load_Hips_Project_Par(self):
        """Loads default or user saved parameters for Caris HIPS Proccesing."""

        chdir(owd)##Application Dir

        ###Reading defaults or user saved inputs for HIPS Proccessing
        Parameters = pd.read_csv('Parameters.txt', delimiter=',', header=None)
        RAW = Parameters.iloc[0,0]
        HDCS = Parameters.iloc[0,1]
        PROJECT = Parameters.iloc[0,2]
        VESSEL = Parameters.iloc[0,3]
        CRS = Parameters.iloc[0,4]
        JULIAN_DAY = Parameters.iloc[0,5]
        YEAR = Parameters.iloc[0,6]
        CON_NAV = int(Parameters.iloc[0,7])
        OUT = Parameters.iloc[0,8]
        CRS2 = Parameters.iloc[0,9]

        ##Setting defaults from Parameter file for HIPS Proccessing
        self.RAW_F.set(RAW)
        self.HDCS_D.set(HDCS)
        self.PROJECT_N.set(PROJECT)
        self.VESSEL_N.set(VESSEL)
        self.CRS_O.set(CRS)
        self.JULIAN_D.set(JULIAN_DAY)
        self.YEAR.set(YEAR)
        self.CONVERT_N.set(CON_NAV)
        self.OUT_F.set(OUT)
        self.CRS_Import.set(CRS2)

    def general_hips_options(self):
        """Sets user inputs for Caris Project Parameters"""

        chdir(owd)##Application Directory
        w_E = 45

        ##Creating HIPS Processing User Input Options
        hips_op = LabelFrame(frame1, text="Hips Project", foreground="blue")
        hips_op.grid(row=0, column=0, padx=1, sticky=W)

        ##RAW Sonar Data (.all,.gsf,.xtf)
        self.RAW_F = StringVar()
        self.RAW_f = Entry(hips_op, width=w_E, textvariable=self.RAW_F,)
        self.RAW_text = Label(hips_op, text="Raw Files")
        self.RAW_text.grid(row=0, column=0, sticky=W)
        self.RAW_f.grid(row=0, column=1, sticky=W)
        self.Button1 = Button(hips_op, text="...", height=0,
                              command=self.Search_RAW_Data)
        self.Button1.grid(row=0, column=2, sticky=W, padx=2)


        ## HDCS_Data Folder Location
        self.HDCS_D = StringVar()
        self.HDCS_d = Entry(hips_op, width=w_E, textvariable=self.HDCS_D)
        self.HDCS_text = Label(hips_op, text="Processing folder")
        self.HDCS_text.grid(row=1, column=0, sticky=W)
        self.HDCS_d.grid(row=1, column=1, sticky=W)
        self.Button2 = Button(hips_op, text="...", height=0,
                              command=self.Search_HDCS_Data)
        self.Button2.grid(row=1, column=2, sticky=W, padx=2)

        ## Output Folder for Script Output
        self.OUT_F = StringVar()
        self.OUT_f = Entry(hips_op, width=w_E, textvariable=self.OUT_F)
        self.OUT_f_text = Label(hips_op, text="Output Folder")
        self.OUT_f_text.grid(row=2, column=0, sticky=W)
        self.OUT_f.grid(row=2, column=1, sticky=W)
        self.Button2 = Button(hips_op, text="...", height=0,
                              command=self.Search_OUTPUT)
        self.Button2.grid(row=2, column=2, sticky=W, padx=2)

        ## CHS Project Number
        self.PROJECT_N = StringVar()
        self.PROJECT_n = Entry(hips_op, width=w_E, textvariable=self.PROJECT_N)
        self.PROJECT_text = Label(hips_op, text="Project Name")
        self.PROJECT_text.grid(row=3, column=0, sticky=W)
        self.PROJECT_n.grid(row=3, column=1, sticky=W)

        ## Vessel File Name (inlcuing .hvf)
        self.VESSEL_N = StringVar()
        self.VESSEL_n = Entry(hips_op, width=w_E, textvariable=self.VESSEL_N)
        self.VESSEL_text = Label(hips_op, text="Select Vessel File")
        self.VESSEL_text.grid(row=4, column=0, sticky=W)
        self.VESSEL_n.grid(row=4, column=1, sticky=W)
        self.Button3 = Button(hips_op, text="...", height=0,
                              command=self.Search_VesselFile)
        self.Button3.grid(row=4, column=2, sticky=W, padx=2)

        ##Project and Hips Data CSRS
        self.CRS_O = StringVar()
        crs_op = ['NAD83(CSRS)/UTM Zone 19N: EPSG:2960@2010',
                  'NAD83(CSRS)/UTM Zone 20N: EPSG:2961@2010',
                  'NAD83(CSRS)/UTM Zone 21N: EPSG:2962@2010',
                  'WGS84/World Mercator: EPSG:3395@2010',
                  'WGS84/EPSG Canada Polar Stereographic: EPSG:5937@2010',
                  'WGS84/UTM Zone 19N: EPSG:32619@2010',
                  'WGS84/UTM Zone 20N: EPSG:32620@2010',
                  'WGS84/UTM Zone 21N: EPSG:32621@2010']

        self.CRS_op = ttk.Combobox(hips_op, values=crs_op, width=42, textvariable=self.CRS_O)
        self.CRS_text = Label(hips_op, text="CRS Of Project")
        self.CRS_text.grid(row=5, column=0, sticky=W)
        self.CRS_op.grid(row=5, column=1, sticky=W+E, padx=0)

           
        ## Import CRS
        self.CRS_Import = StringVar()
        crs_import = ['ITRF2014: EPSG:7912@2010',
                  'NAD83(CSRS)v6: EPSG:8252@2010']

        self.CRS_pos = ttk.Combobox(hips_op, values=crs_import, width=35, textvariable=self.CRS_Import)
        self.CRS_pos_text = Label(hips_op, text="CRS Of Raw Files")
        self.CRS_pos_text.grid(row=6, column=0, sticky=W)
        self.CRS_pos.grid(row=6, column=1, sticky=W+E, padx=0)

        ##Julian Day of RAW
        self.JULIAN_D = StringVar()
        self.JULIAN_d = Entry(hips_op, width=5, textvariable=self.JULIAN_D)
        self.JULIAN_text = Label(hips_op, text="Julian Day")
        self.JULIAN_text.grid(row=7, column=0, sticky=W)
        self.JULIAN_d.grid(row=8, column=0, sticky=W)

        ##Year of RAW
        self.YEAR = StringVar()
        self.Year = Entry(hips_op, width=5, textvariable=self.YEAR)
        self.Year_text = Label(hips_op, text="Year")
        self.Year_text.grid(row=7, column=1, sticky=W)
        self.Year.grid(row=8, column=1, sticky=W)

        ##Covert Navigation
        self.CONVERT_N = IntVar()
        self.CONVERT_n = Checkbutton(hips_op, variable=self.CONVERT_N, text= "Convert Navigation",
                                     state='disabled')
        self.CONVERT_n.grid(row=9, column=0, sticky=W)

        ##Intial Run to Create HIPS File
        self.IntialRun = IntVar()
        self.Intial_Run = Checkbutton(hips_op, variable=self.IntialRun, text= "Intial Run")
        self.Intial_Run.grid(row=9, column=1, sticky=W)

        ##Creating Radio Box for Sensor Data Import
        self.Sensor_type = LabelFrame(frame1, text="Sensor Data", foreground="blue")
        self.Sensor_type.grid(row=1, column=0, padx=1, sticky=W)


        self.STYPE = IntVar()
        self.Stype = Checkbutton(self.Sensor_type, onvalue=1, offvalue=0, variable=self.STYPE, text= "Import RAW Files",
                                    command=self.RAW_Sensor)
        self.Stype.grid(row=0, column=0, sticky=W)

        self.S_T=IntVar()

        self.rb1 = Radiobutton(self.Sensor_type, text= "KONGSBERG\nALL", variable=self.S_T,
                    value=1, command=
                    self.Load_RAW_Par, state='disabled').grid(row=1, column=0, sticky= W)
        self.rb2 = Radiobutton(self.Sensor_type, text= "R2 SONIC\nGSF", variable=self.S_T,
                    value=2, command=
                    self.Load_RAW_Par, state='disabled').grid(row=1, column=2, sticky=W)
        self.rb3 = Radiobutton(self.Sensor_type, text= "TRITON\nXTF", variable=self.S_T,
                    value=3, command=
                    self.Load_RAW_Par,state='disabled').grid(row=1, column=3, sticky=W)
        self.rb4 = Radiobutton(self.Sensor_type, text= "Teledyne\nS7K", variable=self.S_T,
                    value=4, command=
                    self.Load_RAW_Par,state='disabled').grid(row=1, column=4, sticky=W)
        self.rb5 = Radiobutton(self.Sensor_type, text= "KONGSBERG\nKMALL", variable=self.S_T,
                    value=5, command=
                    self.Load_RAW_Par, state='disabled').grid(row=1, column=5, sticky= W)

        ##Creating Check Box for Applanix Data Import
        self.Applanix_Data = LabelFrame(frame1, text="Applanix Data", foreground="blue")
        self.Applanix_Data.grid(row=2, column=0, padx=1, sticky=W)

        self.ATYPE = IntVar()
        self.Atype = Checkbutton(self.Applanix_Data, onvalue=1, offvalue=0, variable=self.ATYPE, text= "Import POS",
                                    command=self.Applanix)
        self.Atype.grid(row=0, column=0, sticky=W)

        self.A_T=IntVar()
        self.rb4 = Radiobutton(self.Applanix_Data, text= "POSMV", variable=self.A_T,
                    value=1, command=
                    self.Load_Auxiliary_Par, state='disabled').grid(row=1, column=0, sticky= W, padx=1)
        self.rb5 = Radiobutton(self.Applanix_Data, text= "SBET & RMS", variable=self.A_T,
                    value=2, command=
                    self.Load_Auxiliary_Par, state='disabled').grid(row=1, column=2, sticky=W, padx=1)

        ##Creating Radio Box for Tide Type
        self.GEO_REF = LabelFrame(frame1, text="Geo-Referencing", foreground="blue")
        self.GEO_REF.grid(row=3, column=0, padx=1, sticky=W)

        self.TTYPE = IntVar()
        self.Ttype = Checkbutton(self.GEO_REF, onvalue=1, offvalue=0, variable=self.TTYPE, text= "Apply Tide",
                                    command=self.TIDES)
        self.Ttype.grid(row=0, column=0, sticky=W)

        self.T_T=IntVar()
        self.rb6 = Radiobutton(self.GEO_REF, text= "GPS Tide", variable=self.T_T,
                    value=1, command=
                    self.Load_Tide_Par, state='disabled').grid(row=1, column=0, sticky= W, padx=1)
        self.rb7 = Radiobutton(self.GEO_REF, text= "Observed/Predicted", variable=self.T_T,
                    value=2, command=
                    self.Load_Tide_Par, state='disabled').grid(row=1, column=1, sticky=W, padx=1)

        ##Compute TPU
        self.COMP_TPU = IntVar()
        self.Comp_TPU = Checkbutton(self.GEO_REF, onvalue=1, offvalue=0, variable=self.COMP_TPU, text= "Compute\nTPU",
                                    command=self.Load_TPU_Par)
        self.Comp_TPU.grid(row=2, column=0, sticky=W)

        ##Create/Add to HIPS Grid
        self.H_GRID = LabelFrame(frame1, text="HIPS Coverage (Surface Creation)", foreground="blue")
        self.H_GRID.grid(row=5, column=0, padx=1, sticky=W)

        self.GRIDS = IntVar()
        self.Grids = Checkbutton(self.H_GRID, onvalue=1, offvalue=0, variable=self.GRIDS, text= "Create Grids",
                                    command=self.SURFACE)
        self.Grids.grid(row=0, column=0, sticky=W)

        self.GRID = IntVar()
        self.rb8 = Radiobutton(self.H_GRID, text= "Create HIPS Grid", variable=self.GRID,
                    value=1, command=
                    self.Load_GRID_Par, state='disabled').grid(row=1, column=0, sticky= W, padx=1)
        self.rb9 = Radiobutton(self.H_GRID, text= "Create/Add to HIPS Grid", variable=self.GRID,
                    value=2, command=
                    self.Load_GRID_Par, state='disabled').grid(row=1, column=2, sticky=W, padx=1)

        ##Create CA Tools Option
        self.CATOOLS_frame = LabelFrame(frame1, text="CA Tools", foreground="blue")
        self.CATOOLS_frame.grid(row=6, column=0, padx=1, sticky=W)

        ##Creating CATools Checkbox
        self.CATOOLS = IntVar()
        self.CATOOLS_cb = Checkbutton(self.CATOOLS_frame, text="Run CA Tools", variable=self.CATOOLS, command=self.Load_CATOOLS_Par)
        self.CATOOLS_cb.grid(row=0, column=0, sticky=W)


    def SURFACE(self):
        
        if self.GRIDS.get()==1:
            self.GRID = IntVar()
            self.rb8 = Radiobutton(self.H_GRID, text= "Create HIPS Grid", variable=self.GRID,
                    value=1, command=
                    self.Load_GRID_Par).grid(row=1, column=0, sticky= W, padx=1)
            self.rb9 = Radiobutton(self.H_GRID, text= "Create/Add to HIPS Grid", variable=self.GRID,
                    value=2, command=
                    self.Load_GRID_Par).grid(row=1, column=2, sticky=W, padx=1)
        else:
            self.GRID = IntVar()
            self.rb8 = Radiobutton(self.H_GRID, text= "Create HIPS Grid", variable=self.GRID,
                    value=1, command=
                    self.Load_GRID_Par, state='disabled').grid(row=1, column=0, sticky= W, padx=1)
            self.rb9 = Radiobutton(self.H_GRID, text= "Create/Add to HIPS Grid", variable=self.GRID,
                    value=2, command=
                    self.Load_GRID_Par, state='disabled').grid(row=1, column=2, sticky=W, padx=1)

            try:
                ##Forget Create Grid
                self.CREATEGRID_op.grid_forget()
            except AttributeError:
                pass
            try:
                ## Forget Create Grid 2
                self.CREATEGRID2_op.grid_forget()
            except AttributeError:
                pass

      
    def TIDES(self):

        if self.TTYPE.get()==1:
            self.T_T=IntVar()
            self.rb6 = Radiobutton(self.GEO_REF, text= "GPS Tide", variable=self.T_T,
                        value=1, command=
                        self.Load_Tide_Par).grid(row=1, column=0, sticky= W, padx=1)
            self.rb7 = Radiobutton(self.GEO_REF, text= "Observed/Predicted", variable=self.T_T,
                        value=2, command=
                        self.Load_Tide_Par).grid(row=1, column=1, sticky=W, padx=1)
        else:
            
            self.T_T=IntVar()
            self.rb6 = Radiobutton(self.GEO_REF, text= "GPS Tide", variable=self.T_T,
                        value=1, command=
                        self.Load_Tide_Par, state='disabled').grid(row=1, column=0, sticky= W, padx=1)
            self.rb7 = Radiobutton(self.GEO_REF, text= "Observed/Predicted", variable=self.T_T,
                        value=2, command=
                        self.Load_Tide_Par, state='disabled').grid(row=1, column=1, sticky=W, padx=1)
            try:
                ## Forget the Observed/Predicted Tides
                self.OPTide_op.grid_forget()
            except AttributeError:
                pass

            try:
                ## Forget the GPS Tide Options
                self.GPSTide_op.grid_forget()
            except AttributeError:
                pass

    
    def Applanix(self):

        if self.ATYPE.get()==1:
            
            self.A_T=IntVar()
        
            self.rb4 = Radiobutton(self.Applanix_Data, text= "POSMV", variable=self.A_T,
                        value=1, command=
                        self.Load_Auxiliary_Par).grid(row=1, column=0, sticky= W, padx=1)
            self.rb5 = Radiobutton(self.Applanix_Data, text= "SBET & RMS", variable=self.A_T,
                        value=2, command=
                        self.Load_Auxiliary_Par).grid(row=1, column=2, sticky=W, padx=1)
        else:
            self.A_T=IntVar()
            self.rb4 = Radiobutton(self.Applanix_Data, text= "POSMV", variable=self.A_T,
                    value=1, command=
                    self.Load_Auxiliary_Par, state='disabled').grid(row=1, column=0, sticky= W, padx=1)
            self.rb5 = Radiobutton(self.Applanix_Data, text= "SBET & RMS", variable=self.A_T,
                    value=2, command=
                    self.Load_Auxiliary_Par, state='disabled').grid(row=1, column=2, sticky=W, padx=1)

            try:
                ## Forget the SBET & RMS Options
                self.SBET_RMS_op.grid_forget()
                self.AUX_f2.grid_forget()
                self.Button_AUX2.grid_forget()
                self.AUX_text2.grid_forget()
                
            except AttributeError:
                pass

            try:
                ## Forget the POSMV Options
                self.POSMV_op.grid_forget()

            except AttributeError:
                pass
            

    def RAW_Sensor(self):

        if self.STYPE.get()==1:
            
            self.S_T=IntVar()
            self.rb1 = Radiobutton(self.Sensor_type, text= "KONGSBERG\nALL", variable=self.S_T,
                        value=1, command=
                        self.Load_RAW_Par).grid(row=1, column=0, sticky= W)
            self.rb2 = Radiobutton(self.Sensor_type, text= "R2 SONIC\nGSF", variable=self.S_T,
                        value=2, command=
                        self.Load_RAW_Par).grid(row=1, column=2, sticky=W)
            self.rb3 = Radiobutton(self.Sensor_type, text= "TRITON\nXTF", variable=self.S_T,
                        value=3, command=
                        self.Load_RAW_Par).grid(row=1, column=3, sticky=W)
            self.rb4 = Radiobutton(self.Sensor_type, text= "Teledyne\nS7K", variable=self.S_T,
                        value=4, command=
                        self.Load_RAW_Par).grid(row=1, column=4, sticky=W)
            self.rb5 = Radiobutton(self.Sensor_type, text= "KONGSBERG\nKMALL", variable=self.S_T,
                        value=5, command=
                        self.Load_RAW_Par).grid(row=1, column=5, sticky=W)
    
        else:
            self.S_T=IntVar()

            self.rb1 = Radiobutton(self.Sensor_type, text= "KONGSBERG\nALL", variable=self.S_T,
                        value=1, command=
                        self.Load_RAW_Par, state='disabled').grid(row=1, column=0, sticky= W)
            self.rb2 = Radiobutton(self.Sensor_type, text= "R2 SONIC\nGSF", variable=self.S_T,
                        value=2, command=
                        self.Load_RAW_Par, state='disabled').grid(row=1, column=2, sticky=W)
            self.rb3 = Radiobutton(self.Sensor_type, text= "TRITON\nXTF", variable=self.S_T,
                        value=3, command=
                        self.Load_RAW_Par,state='disabled').grid(row=1, column=3, sticky=W)
            self.rb4 = Radiobutton(self.Sensor_type, text= "Teledyne\nS7K", variable=self.S_T,
                        value=34, command=
                        self.Load_RAW_Par,state='disabled').grid(row=1, column=4, sticky=W)
            self.rb5 = Radiobutton(self.Sensor_type, text= "KONGSBERG\nKMALL", variable=self.S_T,
                        value=34, command=
                        self.Load_RAW_Par,state='disabled').grid(row=1, column=5, sticky=W)
            
            try:
                ## Forget R2 Sonic options
                self.R2_op.grid_forget()
            except AttributeError:
                pass
            try:
                ## Forget XTF 0ptions
                 self.X_op.grid_forget()
            except AttributeError:
                pass
            try:
                ## Forget Kongsberg 0ptions
                 self.K_op.grid_forget()
            except AttributeError:
                pass
            try:
                ## Forget Teledyne S7K 0ptions
                 self.S7K_op.grid_forget()
            except AttributeError:
                pass
            try:
                ## Forget KMALL Options
                self.KMALL_op.grid_forget()
            except:
                pass
            

    def Load_RAW_Par(self):

        chdir(owd) ##Application Dir

        if self.S_T.get()==1:

            ##Creating IMPORT TO HIPS Options
            self.K_op = LabelFrame(frame2, text="Import Kongsberg (.all) to HIPS", foreground="blue")
            self.K_op.grid(row=0, column=0, padx=1, sticky=W)

            ##Navigation Device
            self.Nav_D = StringVar()
            self.Nav_d = Entry(self.K_op, width=10, textvariable=self.Nav_D, state='disabled')
            self.Nav_d_text = Label(self.K_op, text="Navigation Device")
            self.Nav_d_text.grid(row=1, column=0, sticky=W)
            self.Nav_d.grid(row=1, column=1, sticky=W, padx=1)

            ##GPS Height Device
            self.GPSH_D = StringVar()
            self.GPS_h = Entry(self.K_op, width=10, textvariable=self.GPSH_D, state='disabled')
            self.GPS_h_text = Label(self.K_op, text="GPS Height Device")
            self.GPS_h_text.grid(row=2, column=0, sticky=W)
            self.GPS_h.grid(row=2, column=1, sticky=W, padx=1)

            ##GPS Height Device
            self.Heave_D = StringVar()
            self.Heave_d = Entry(self.K_op, width=10, textvariable=self.Heave_D, state='disabled')
            self.Heave_d_text = Label(self.K_op, text="Heave Device")
            self.Heave_d_text.grid(row=3, column=0, sticky=W)
            self.Heave_d.grid(row=3, column=1, sticky=W, padx=1)

            ##Heading Device
            self.Heading_D = StringVar()
            self.Heading_d = Entry(self.K_op, width=10, textvariable=self.Heading_D, state='disabled')
            self.Heading_d_text = Label(self.K_op, text="Heading Device")
            self.Heading_d_text.grid(row=4, column=0, sticky=W)
            self.Heading_d.grid(row=4, column=1, sticky=W, padx=1)

            ##GPS Time Stamps
            self.GPS_T = StringVar()
            self.GPS_t = Entry(self.K_op, width=10, textvariable=self.GPS_T, state='disabled')
            self.GPS_t_text = Label(self.K_op, text="GPS Time Stamps")
            self.GPS_t_text.grid(row=5, column=0, sticky=W)
            self.GPS_t.grid(row=5, column=1, sticky=W, padx=1)

            ##Pitch Device
            self.Pitch_D = StringVar()
            self.Pitch_d = Entry(self.K_op, width=10, textvariable=self.Pitch_D, state='disabled')
            self.Pitch_d_text = Label(self.K_op, text="Pitch Device")
            self.Pitch_d_text.grid(row=6, column=0, sticky=W)
            self.Pitch_d.grid(row=6, column=1, sticky=W, padx=1)

            ##Roll Device
            self.Roll_D = StringVar()
            self.Roll_d = Entry(self.K_op, width=10, textvariable=self.Roll_D, state='disabled')
            self.Roll_d_text = Label(self.K_op, text="Roll Device")
            self.Roll_d_text.grid(row=7, column=0, sticky=W)
            self.Roll_d.grid(row=7, column=1, sticky=W, padx=1)

            ##Sound Speed Device
            self.SSP_D = StringVar()
            self.SSP_d = Entry(self.K_op, width=10, textvariable=self.SSP_D, state='disabled')
            self.SSP_d_text = Label(self.K_op, text="Sound Speed Device")
            self.SSP_d_text.grid(row=8, column=0, sticky=W)
            self.SSP_d.grid(row=8, column=1, sticky=W, padx=1)

            ##Reading the defaults or user saved inputs for Kongsberg (.all)
            Parameters = pd.read_csv('Parameters.txt', delimiter=',', header=None)
            NAV_D = Parameters.iloc[3,0]
            GPSH_D = Parameters.iloc[3,1]
            Heave_D = Parameters.iloc[3,2]
            Heading_D = Parameters.iloc[3,3]
            GPS_T = Parameters.iloc[3,4]
            Pitch_D = Parameters.iloc[3,5]
            Roll_D = Parameters.iloc[3,6]
            SSP_D = Parameters.iloc[3,7]

            self.Nav_D.set(NAV_D)
            self.GPSH_D.set(GPSH_D)
            self.Heave_D.set(Heave_D)
            self.Heading_D.set(Heading_D)
            self.GPS_T.set(GPS_T)
            self.Pitch_D.set(Pitch_D)
            self.Roll_D.set(Roll_D)
            self.SSP_D.set(SSP_D)

            try:
                ## Forget R2 Sonic options
                self.R2_op.grid_forget()
            except AttributeError:
                pass
            try:
                ## Forget XTF 0ptions
                self.X_op.grid_forget()
            except AttributeError:
                pass
            try:
                ## Forget S7K 0ptions
                self.S7K_op.grid_forget()
            except AttributeError:
                pass
            try:
                ## Forget Kongsberg .kmall 0ptions
                self.KMALL_op.grid_forget()
            except AttributeError:
                pass

        elif self.S_T.get()==2:

            self.R2_op = LabelFrame(frame2, text="Import R2 Sonic (.gsf) to HIPS", foreground="blue")
            self.R2_op.grid(row=1, column=0, padx=1, sticky=W)

            self.D_S = StringVar()
            self.D_s = Entry(self.R2_op, width=10, textvariable=self.D_S, state='disabled')
            self.D_s_text = Label(self.R2_op, text="Depth Source")
            self.D_s_text.grid(row=1, column=0, sticky=W)
            self.D_s.grid(row=1, column=1, sticky=W,  padx=1)

            self.IN_OFF = IntVar()
            self.IN_off = Checkbutton(self.R2_op, variable=self.IN_OFF, text= "Include Offline", state='disabled')
            self.IN_off.grid(row=2, column=0, sticky=W)

            self.REJ_OFF = IntVar()
            self.REJ_off = Checkbutton(self.R2_op, variable=self.REJ_OFF, text= "Reject Offline", state='disabled')
            self.REJ_off.grid(row=3, column=0, sticky=W)

            Parameters = pd.read_csv('Parameters.txt', delimiter=',', header=None)
            DS = Parameters.iloc[4,0]
            IN_O = Parameters.iloc[4,1]
            R_O = Parameters.iloc[4,2]

            self.D_S.set(DS)
            self.IN_OFF.set(IN_O)
            self.REJ_OFF.set(R_O)

            try:
                ## Forget Konsberg options
                self.K_op.grid_forget()
            except AttributeError:
                pass
            try:
                ## Forget XTF 0ptions
                self.X_op.grid_forget()
            except AttributeError:
                pass
            try:
                ## Forget S7K 0ptions
                self.S7K_op.grid_forget()
            except AttributeError:
                pass
            try:
                ## Forget Kongsberg .kmall 0ptions
                self.KMALL_op.grid_forget()
            except AttributeError:
                pass

        elif self.S_T.get()==3:

            self.X_op = LabelFrame(frame2, text="Import ILRIS (.xtf) to HIPS", foreground="blue")
            self.X_op.grid(row=2, column=0, padx=1, sticky=W)

            self.Nav_DX = StringVar()
            self.Nav_dX = Entry(self.X_op, width=15, textvariable=self.Nav_DX, state='disabled')
            self.Nav_dX_text = Label(self.X_op, text="Navigation Device")
            self.Nav_dX_text.grid(row=1, column=0, sticky=W)
            self.Nav_dX.grid(row=1, column=1, sticky=W, padx=1)

            self.GPSH_DX = StringVar()
            self.GPS_hX = Entry(self.X_op, width=15, textvariable=self.GPSH_DX, state='disabled')
            self.GPS_hX_text = Label(self.X_op, text="GPS Height Device")
            self.GPS_hX_text.grid(row=2, column=0, sticky=W)
            self.GPS_hX.grid(row=2, column=1, sticky=W, padx=1)

            self.M_D = StringVar()
            self.M_d = Entry(self.X_op, width=10, textvariable=self.M_D, state='disabled')
            self.M_d_text = Label(self.X_op, text="Motion Device")
            self.M_d_text.grid(row=3, column=0, sticky=W)
            self.M_d.grid(row=3, column=1, sticky=W, padx=1)

            self.C_B = StringVar()
            self.C_b = Entry(self.X_op, width=15, textvariable=self.C_B, state='disabled')
            self.C_b_text = Label(self.X_op, text="Convert Bathymetry")
            self.C_b_text.grid(row=4, column=0, sticky=W)
            self.C_b.grid(row=4, column=1, sticky=W, padx=1)

            self.Heading_DX = StringVar()
            self.Heading_dX = Entry(self.X_op, width=15, textvariable=self.Heading_DX, state='disabled')
            self.Heading_dX_text = Label(self.X_op, text="Heading Device")
            self.Heading_dX_text.grid(row=5, column=0, sticky=W)
            self.Heading_dX.grid(row=5, column=1, sticky=W, padx=1)

            self.CONV_SS = StringVar()
            self.CONV_ss = Entry(self.X_op, width=15, textvariable=self.CONV_SS, state='disabled')
            self.CONV_ss_text = Label(self.X_op, text="Convert Side Scan")
            self.CONV_ss_text.grid(row=6, column=0, stick=W)
            self.CONV_ss.grid(row=6, column=1, sticky=W, padx=1)

            self.SSWF = StringVar()
            self.sswf = Entry(self.X_op, width=15, textvariable=self.SSWF, state='disabled')
            self.sswf_text = Label(self.X_op, text="Side Scan Weighting Factor")
            self.sswf_text.grid(row=7, column=0, stick=W)
            self.sswf.grid(row=7, column=1, sticky=W, padx=1)

            self.SS_NAV = StringVar()
            self.ss_nav = Entry(self.X_op, width=15, textvariable=self.SS_NAV, state='disabled')
            self.ss_nav_text = Label(self.X_op, text="Side Scan Navigation Device")
            self.ss_nav_text.grid(row=8, column=0, stick=W)
            self.ss_nav.grid(row=8, column=1, sticky=W, padx=1)

            self.SS_HEAD = StringVar()
            self.ss_head = Entry(self.X_op, width=15, textvariable=self.SS_HEAD, state='disabled')
            self.ss_head_text = Label(self.X_op, text="Side Scan Heading Device")
            self.ss_head_text.grid(row=9, column=0, stick=W)
            self.ss_head.grid(row=9, column=1, sticky=W, padx=1)

            self.TIME_S = StringVar()
            self.time_s = Entry(self.X_op, width=15, textvariable=self.TIME_S, state='disabled')
            self.time_s_text = Label(self.X_op, text="Time Stamps")
            self.time_s_text.grid(row=10, column=0, stick=W)
            self.time_s.grid(row=10, column=1, sticky=W, padx=1)

            ##Reading the defaults or user saved inputs for KongsBerg (.all)
            Parameters = pd.read_csv('Parameters.txt', delimiter=',', header=None)
            NAV_DX = Parameters.iloc[5,0]
            GPSH_DX = Parameters.iloc[5,1]
            M_D = Parameters.iloc[5,2]
            C_B = Parameters.iloc[5,3]
            Heading_DX = Parameters.iloc[5,4]
            CONV_SS = Parameters.iloc[5,5]
            SSWF = Parameters.iloc[5,6]
            SS_NAV = Parameters.iloc[5,7]
            SS_HEAD = Parameters.iloc[5,8]
            TIME_S = Parameters.iloc[5,9]

            ##Setting the defaults or user saved inputs for KongsBerg (.all)
            self.Nav_DX.set(NAV_DX)
            self.GPSH_DX.set(GPSH_DX)
            self.M_D.set(M_D)
            self.C_B.set(C_B)
            self.Heading_DX.set(Heading_DX)
            self.CONV_SS.set(CONV_SS)
            self.SSWF.set(SSWF)
            self.SS_NAV.set(SS_NAV)
            self.SS_HEAD.set(SS_HEAD)
            self.TIME_S.set(TIME_S)

            try:
                ## Forget R2 Sonic options
                self.R2_op.grid_forget()
            except AttributeError:
                pass
            try:
                ## Forget Kongsberg .all 0ptions
                self.K_op.grid_forget()
            except AttributeError:
                pass
            try:
                ## Forget S7K 0ptions
                self.S7K_op.grid_forget()
            except AttributeError:
                pass
            try:
                ## Forget Kongsberg .kmall 0ptions
                self.KMALL_op.grid_forget()
            except AttributeError:
                pass

        elif self.S_T.get()==4:
            self.S7K_op = LabelFrame(frame2, text="Import Teledyne S7K to HIPS", foreground="blue")
            self.S7K_op.grid(row=3, column=0, padx=1, sticky=W)

            self.CB = StringVar()
            self.cb = Entry(self.S7K_op, width=15, textvariable=self.CB, state='disabled')
            self.cb_text = Label(self.S7K_op, text="Convert Bathymetry")
            self.cb_text.grid(row=1, column=0, sticky=W)
            self.cb.grid(row=1, column=1, sticky=W, padx=1)

            self.NAV_D = StringVar()
            self.nav_d = Entry(self.S7K_op, width=15, textvariable=self.NAV_D, state='disabled')
            self.nav_d_text = Label(self.S7K_op, text="Navigation Device")
            self.nav_d_text.grid(row=2, column=0, sticky=W)
            self.nav_d.grid(row=2, column=1, sticky=W, padx=1)

            self.HEAD_D = StringVar()
            self.head_d = Entry(self.S7K_op, width=15, textvariable=self.HEAD_D, state='disabled')
            self.head_d_text = Label(self.S7K_op, text="Heading Device")
            self.head_d_text.grid(row=3, column=0, sticky=W)
            self.head_d.grid(row=3, column=1, sticky=W, padx=1)

            self.MOTION_D = StringVar()
            self.motion_d = Entry(self.S7K_op, width=15, textvariable=self.MOTION_D, state='disabled')
            self.motion_d_text = Label(self.S7K_op, text="Motion Device")
            self.motion_d_text.grid(row=4, column=0, sticky=W)
            self.motion_d.grid(row=4, column=1, sticky=W, padx=1)

            self.SWATH_D = StringVar()
            self.swath_d = Entry(self.S7K_op, width=15, textvariable=self.SWATH_D, state='disabled')
            self.swath_d_text = Label(self.S7K_op, text="Swath Device")
            self.swath_d_text.grid(row=5, column=0, sticky=W)
            self.swath_d.grid(row=5, column=1, sticky=W, padx=1)

            ##Reading the defaults or user saved inputs for Teledyne (.S7K)
            Parameters = pd.read_csv('Parameters.txt', delimiter=',', header=None)
            C_B = Parameters.iloc[15,0]
            N_D = Parameters.iloc[15,1]
            H_D = Parameters.iloc[15,2]
            M_D = Parameters.iloc[15,3]
            S_D = Parameters.iloc[15,4]

            ##Setting the defaults or user saved inputs for Teledyne (.S7K)
            self.CB.set(C_B)
            self.NAV_D.set(N_D)
            self.HEAD_D.set(H_D)
            self.MOTION_D.set(M_D)
            self.SWATH_D.set(S_D)

            try:
                ## Forget R2 Sonic options
                self.R2_op.grid_forget()
            except AttributeError:
                pass
            try:
                ## Forget Kongsberg 0ptions
                self.K_op.grid_forget()
            except AttributeError:
                pass
            try:
                ## Forget XTF 0ptions
                self.X_op.grid_forget()
            except AttributeError:
                pass
            try:
                ## Forget Kongsberg .kmall 0ptions
                self.KMALL_op.grid_forget()
            except AttributeError:
                pass


        if self.S_T.get()== 5:

            ##Creating IMPORT TO HIPS Options
            self.KMALL_op = LabelFrame(frame2, text="Import Kongsberg (.kmall) to HIPS", foreground="blue")
            self.KMALL_op.grid(row=0, column=0, padx=1, sticky=W)

            ##Navigation Device
            self.Nav_D = StringVar()
            self.Nav_d = Entry(self.KMALL_op, width=10, textvariable=self.Nav_D, state='disabled')
            self.Nav_d_text = Label(self.KMALL_op, text="Navigation Device")
            self.Nav_d_text.grid(row=1, column=0, sticky=W)
            self.Nav_d.grid(row=1, column=1, sticky=W, padx=1)

            ##GPS Height Device
                   ##Project and Hips Data CSRS
            self.GPSH_D = StringVar()
            gpsh_devs = ['EM_Height', 'SPO']

            self.CRS_pos = ttk.Combobox(self.KMALL_op, values=gpsh_devs, width=10, textvariable=self.GPSH_D)
            self.CRS_pos_text = Label(self.KMALL_op, text="GPS Height Device")
            self.CRS_pos_text.grid(row=2, column=0, sticky=W)
            self.CRS_pos.grid(row=2, column=1, sticky=W, padx=0)

            ##Heave Device
            self.Heave_D = StringVar()
            self.Heave_d = Entry(self.KMALL_op, width=10, textvariable=self.Heave_D, state='disabled')
            self.Heave_d_text = Label(self.KMALL_op, text="Heave Device")
            self.Heave_d_text.grid(row=3, column=0, sticky=W)
            self.Heave_d.grid(row=3, column=1, sticky=W, padx=1)

            ##Heading Device
            self.Heading_D = StringVar()
            self.Heading_d = Entry(self.KMALL_op, width=10, textvariable=self.Heading_D, state='disabled')
            self.Heading_d_text = Label(self.KMALL_op, text="Heading Device")
            self.Heading_d_text.grid(row=4, column=0, sticky=W)
            self.Heading_d.grid(row=4, column=1, sticky=W, padx=1)

            ##Pitch Device
            self.Pitch_D = StringVar()
            self.Pitch_d = Entry(self.KMALL_op, width=10, textvariable=self.Pitch_D, state='disabled')
            self.Pitch_d_text = Label(self.KMALL_op, text="Pitch Device")
            self.Pitch_d_text.grid(row=6, column=0, sticky=W)
            self.Pitch_d.grid(row=6, column=1, sticky=W, padx=1)

            ##Roll Device
            self.Roll_D = StringVar()
            self.Roll_d = Entry(self.KMALL_op, width=10, textvariable=self.Roll_D, state='disabled')
            self.Roll_d_text = Label(self.KMALL_op, text="Roll Device")
            self.Roll_d_text.grid(row=7, column=0, sticky=W)
            self.Roll_d.grid(row=7, column=1, sticky=W, padx=1)

            ##Delayed Heave Device
            self.DelHeave_D = StringVar()
            self.DelHeave_d = Entry(self.KMALL_op, width=10, textvariable=self.Heave_D, state='disabled')
            self.DelHeave_d_text = Label(self.KMALL_op, text="Delayed Heave Device")
            self.DelHeave_d_text.grid(row=8, column=0, sticky=W)
            self.DelHeave_d.grid(row=8, column=1, sticky=W, padx=1)

            ##GPS Time Stamps
            self.GPS_T = StringVar()
            self.GPS_t = Entry(self.KMALL_op, width=10, textvariable=self.GPS_T, state='disabled')
            self.GPS_t_text = Label(self.KMALL_op, text="GPS Time Stamps")
            self.GPS_t_text.grid(row=9, column=0, sticky=W)
            self.GPS_t.grid(row=9, column=1, sticky=W, padx=1)

            Parameters = pd.read_csv('Parameters.txt', delimiter=',', header=None)
            NAV_D = Parameters.iloc[16,0]
            GPSH_D = Parameters.iloc[16,1]
            Heave_D = Parameters.iloc[16,2]
            Heading_D = Parameters.iloc[16,3]
            Pitch_D = Parameters.iloc[16,4]
            Roll_D = Parameters.iloc[16,5]
            DelHeave_D = Parameters.iloc[16,6]
            GPS_T = Parameters.iloc[16,7]

            self.Nav_D.set(NAV_D)
            self.GPSH_D.set(GPSH_D)
            self.Heave_D.set(Heave_D)
            self.Heading_D.set(Heading_D)
            self.Pitch_D.set(Pitch_D)
            self.Roll_D.set(Roll_D)
            self.DelHeave_D.set(DelHeave_D)
            self.GPS_T.set(GPS_T)

            try:
                ## Forget R2 Sonic options
                self.R2_op.grid_forget()
            except AttributeError:
                pass
            try:
                ## Forget Kongsberg 0ptions
                self.K_op.grid_forget()
            except AttributeError:
                pass
            try:
                ## Forget XTF 0ptions
                self.X_op.grid_forget()
            except AttributeError:
                pass
            try:
                ## Forget S7K 0ptions
                self.S7K_op.grid_forget()
            except AttributeError:
                pass


    def IMPORT_TO_HIPS(self):

        PH = self.split_Project_Name()
        Project_N = PH[0]
        HIPSFILE = PH[1]
        HDCS_Folder = self.HDCS_D.get()
        RAW_F = self.RAW_F.get()
        L_R = listdir(RAW_F)
        crs = self.CRS_Import.get()
        CRS = crs.partition(": ")[2]
        Vessel_F = self.VESSEL_N.get()
        Vessel = path.basename(Vessel_F)
        Vessel = path.splitext(Vessel)[0]
        Year = (self.Year.get())
        JD = self.JULIAN_D.get()
        Out = self.OUT_F.get()

        if self.IntialRun.get()==1:

            with open("CreateHIPSFile.bat", "w") as Import:
                Import.write('@ECHO OFF' + '\n')
                Import.write('@ECHO Creating HIPS File' + '\n')
                Import.write('cd '+ Caris + '\n')
                Import.write('carisbatch --run CreateHIPSFile --output-crs ' +
                             CRS +
                             r' file:///' + HDCS_Folder + '/' + HIPSFILE + '/' + HIPSFILE + '.hips' +
                             '> ' + Out + '/' + 'CreateHIPSFile.txt')

            p = S.Popen(['CreateHIPSFile.bat'])
            p.communicate()


        if self.S_T.get()==1:
            nav_d = self.Nav_D.get()
            gpsh_d = self.GPSH_D.get()
            heading_d = self.Heading_D.get()
            gps_t = self.GPS_T.get()
            pitch_d = self.Pitch_D.get()
            roll_d = self.Roll_D.get()
            ssp_d = self.SSP_D.get()
            H_Format = ('KONGSBERG')
            with open("Import_To_Hips.bat", "w") as Import:
                Import.write('@ECHO OFF' + '\n')
                Import.write('@ECHO Importing RAW KongsBerg .all' + '\n')
                Import.write('cd '+ Caris + '\n')
                raw_f = []
                for file in L_R:
                    if file.endswith(".all"):
                        ## Rename ALL files to not have spaces
                        r = file.replace(" ", "")
                        if(r != file):
                            File = (RAW_F + '/' + file)
                            Rename = (RAW_F + '/' + r)
                            rename(File, Rename)
                            raw_f.append(Rename)
                        else:
                           raw_f.append(RAW_F + '/' + file)

                Import.write('carisbatch --run ImportToHIPS --input-format ' +
                             H_Format + ' --convert-navigation ' + '--input-crs ' + CRS +
                             ' --vessel-file ' + Vessel_F +
                             ' --navigation-device ' + nav_d + ' --gps-height-device ' + gpsh_d +
                             ' --heading-device ' + heading_d +  ' --gps-timestamps ' + gps_t +
                             ' --pitch-device ' + pitch_d + ' --roll-device ' + roll_d +
                             ' --ssp-device ' + ssp_d + ' ')
                for file in raw_f:
                    Import.write(file + ' ')
                Import.write(r'file:///' + HDCS_Folder + '/' +  HIPSFILE + '/' + HIPSFILE + '.hips?Vessel=' + Vessel +
                             ';Day=' + str(Year) + '-' + str(JD) + ' > ' + Out + '/' + JD + '/' +
                             '1.Import_To_Hips_ALL_' + JD + '_' + Year + '.txt' + '\n')

        elif self.S_T.get()==5:
            nav_d = self.Nav_D.get()
            gpsh_d = self.GPSH_D.get()
            heave_d = self.Heave_D.get()
            heading_d = self.Heading_D.get()
            pitch_d = self.Pitch_D.get()
            roll_d = self.Roll_D.get()
            delheave_d = self.DelHeave_D.get()
            gps_t = self.GPS_T.get()
            H_Format = ('KONGSBERGKMALL')
            with open("Import_To_Hips.bat", "w") as Import:
                Import.write('@ECHO OFF' + '\n')
                Import.write('@ECHO Importing RAW KongsBerg .kmall' + '\n')
                Import.write('cd '+ Caris + '\n')
                raw_f = []
                for file in L_R:
                    if file.endswith(".kmall"):
                        ## Rename KMALL files to not have spaces
                        r = file.replace(" ", "")
                        if(r != file):
                            File = (RAW_F + '/' + file)
                            Rename = (RAW_F + '/' + r)
                            rename(File, Rename)
                            raw_f.append(Rename)
                        else:
                           raw_f.append(RAW_F + '/' + file)

                Import.write('carisbatch --run ImportToHIPS --input-format ' +
                             H_Format + ' --convert-navigation ' + '--input-crs ' + CRS +
                             ' --vessel-file ' + Vessel_F +
                             ' --navigation-device ' + nav_d + ' --gps-height-device ' + gpsh_d +
                             ' --heading-device ' + heading_d +  ' --heave-device ' + heave_d +
                             ' --pitch-device ' + pitch_d + ' --roll-device ' + roll_d +
                             ' --delayed-heave-device ' + delheave_d +
                             ' --gps-timestamps ' + gps_t + ' ')
                
                for file in raw_f:
                    Import.write(file + ' ')
                Import.write(r'file:///' + HDCS_Folder + '/' +  HIPSFILE + '/' + HIPSFILE + '.hips?Vessel=' + Vessel +
                             ';Day=' + str(Year) + '-' + str(JD) + ' > ' + Out + '/' + JD + '/' +
                             '1.Import_To_Hips_ALL_' + JD + '_' + Year + '.txt' + '\n')

        elif self.S_T.get()==2:

            depth_s = self.D_S.get()
            H_Format = ('GSF')
            with open("Import_To_Hips.bat", "w") as Import:
                Import.write('@ECHO OFF' + '\n')
                Import.write('@ECHO Importing RAW R2 Sonic .gsf' + '\n')
                Import.write('cd '+ Caris + '\n')
                raw_f = []
                for file in L_R:
                    if file.endswith(".gsf"):
                        ## Rename GSf files to not have spaces
                        r = file.replace(" ", "")
                        if(r != file):
                            File = (RAW_F + '/' + file)
                            Rename = (RAW_F + '/' + r)
                            rename(File, Rename)
                            raw_f.append(Rename)
                        else:
                           raw_f.append(RAW_F + '/' + file)

                Import.write('carisbatch --run ImportToHIPS --input-format ' +
                             H_Format + ' --input-crs ' + CRS +
                             ' --vessel-file ' + Vessel_F +
                             ' --depth-source ' + depth_s + ' --include-offline ' + ' ')
                for file in raw_f:
                    Import.write(file + ' ')
                Import.write(r'file:///' + HDCS_Folder + '/' + HIPSFILE + '/' + HIPSFILE + '.hips?Vessel=' + Vessel +
                             ';Day=' + str(Year) + '-' + str(JD) + ' > ' + Out + '/' + JD + '/' +
                             '1.Import_To_Hips_GSF_' + JD + '_' + Year + '.txt' + '\n')

        elif self.S_T.get()==3:

            nav_dx = self.Nav_DX.get()
            gpsh_dx = self.GPSH_DX.get()
            m_d = self.M_D.get()
            c_b = self.C_B.get()
            heading_dx = self.Heading_DX.get()
            conv_ss = self.CONV_SS.get()
            sswf = self.SSWF.get()
            ss_nav = self.SS_NAV.get()
            ss_head = self.SS_HEAD.get()
            time_s = self.TIME_S.get()
            H_Format = ('XTF')
            with open("Import_To_Hips.bat", "w") as Import:
                Import.write('@ECHO OFF' + '\n')
                Import.write('@ECHO Importing RAW Triton .xtf' + '\n')
                Import.write('cd '+ Caris + '\n')
                raw_f = []
                for file in L_R:
                    if file.endswith(".xtf"):
                        ##Rename XTF files to not have spaces
                        r = file.replace(" ", "")
                        if(r != file):
                            File = (RAW_F + '/' + file)
                            Rename = (RAW_F + '/' + r)
                            rename(File, Rename)
                            raw_f.append(Rename)
                        else:
                           raw_f.append(RAW_F + '/' + file)

                Import.write('carisbatch --run ImportToHIPS --input-format ' +
                             H_Format + ' --input-crs ' + CRS +
                             ' --vessel-file ' + Vessel_F +
                             ' --navigation-device ' + nav_dx + ' --gps-height-device ' + gpsh_dx +
                             ' --heading-device ' + heading_dx +
                             ' --motion-device ' + m_d + ' --convert-bathymetry ' + c_b +
                             ' --convert-side-scan ' + conv_ss + ' --ss-weighting-factor ' + sswf +
                             ' --ss-navigation-device ' + ss_nav + ' --ss-heading-device ' + ss_head +
                             ' --timestamps ' + time_s + ' ')
                for file in raw_f:
                    Import.write(file + ' ')
                Import.write(r'file:///' + HDCS_Folder + '/' + HIPSFILE + '/' + HIPSFILE + '.hips?Vessel=' + Vessel +
                            ';Day=' + str(Year) + '-' + str(JD) + ' > ' + Out + '/' + JD + '/' +
                            '1.Import_To_Hips_XTF_' + JD + '_' + Year + '.txt' + '\n' 'Pause')

        elif self.S_T.get()==4:

            CB = self.CB.get()
            ND = self.NAV_D.get()
            HD = self.HEAD_D.get()
            MD = self.MOTION_D.get()
            SD = self.SWATH_D.get()
            H_Format = ('TELEDYNE_7K')
            with open("Import_To_Hips.bat", "w") as Import:
                Import.write('@ECHO OFF' + '\n')
                Import.write('@ECHO Importing RAW Teledyne .S7K' + '\n')
                Import.write('cd '+ Caris + '\n')
                raw_f = []
                for file in L_R:
                    if file.endswith(".s7k"):
                        ## Rename S7K files to not have spaces
                        r = file.replace(" ", "")
                        if(r != file):
                            File = (RAW_F + '/' + file)
                            Rename = (RAW_F + '/' + r)
                            rename(File, Rename)
                            raw_f.append(Rename)
                        else:
                           raw_f.append(RAW_F + '/' + file)
                Import.write('carisbatch --run ImportToHIPS --input-format ' +
                             H_Format + ' --input-crs ' + CRS +
                             ' --convert-bathymetry ' + CB + ' --navigation-device ' +
                             ND + ' --heading-device ' + HD + ' --motion-device ' + MD +
                             ' --swath-device ' + SD + ' ')
                for file in raw_f:
                    Import.write(file + ' ')
                Import.write(r'file:///' + HDCS_Folder + '/' +  HIPSFILE + '/' + HIPSFILE + '.hips?Vessel=' + Vessel +
                             ';Day=' + str(Year) + '-' + str(JD) + ' > ' + Out + '/' + JD + '/' +
                             '1.Import_To_Hips_S7K_' + JD + '_' + Year + '.txt' + '\n')

        p = S.Popen(['Import_To_Hips.bat'])
        p.communicate()


    def Load_Tide_Par(self):


        if self.T_T.get()==1:
            self.GPSTide_op = LabelFrame(frame4, text="Import GPS Tides", foreground="blue")
            self.GPSTide_op.grid(row=0, column=0, sticky=W)

            self.C_GPS_ADJ = IntVar()
            self.C_GPS_Adj = Checkbutton(self.GPSTide_op, variable=self.C_GPS_ADJ, text= "Compute GPS \n Vertical Adjustment \n Errors"
                                         , state='disabled')
            self.C_GPS_Adj.grid(row=7, column=0, sticky=W)

            self.M_F = StringVar()
            self.M_f = Entry(self.GPSTide_op, width=25, textvariable=self.M_F)
            self.M_f_text = Label(self.GPSTide_op, text="Model File")
            self.M_f_text.grid(row=0, column=0, sticky=W)
            self.M_f.grid(row=0, column=1, sticky=W)
            self.ButtonMF = Button(self.GPSTide_op, text="...", height=0,
                              command=self.Search_Model_File)
            self.ButtonMF.grid(row=0, column=2, sticky=W, padx=2)

            self.INFO_F = StringVar()
            self.Info_f = Entry(self.GPSTide_op, width=25, textvariable=self.INFO_F)
            self.Info_f_text = Label(self.GPSTide_op, text="Info File")
            self.Info_f_text.grid(row=1, column=0, sticky=W)
            self.Info_f.grid(row=1, column=1, sticky=W)
            self.ButtonMF1 = Button(self.GPSTide_op, text="...", height=0,
                              command=self.Search_Info_File)
            self.ButtonMF1.grid(row=1, column=2, sticky=W, padx=2)

            self.INFO_CRS = StringVar()
            infocrs_op = ['EPSG:4617@2010', 'EPSG:7912@2010']
            self.CRS_inf = ttk.Combobox(self.GPSTide_op, values=infocrs_op, width=15, textvariable=self.INFO_CRS)
            self.CRS_inf_text = Label(self.GPSTide_op, text="Model CRS")
            self.CRS_inf_text.grid(row=3, column=0, sticky=W)
            self.CRS_inf.grid(row=3, column=1, sticky=W)

            self.SD_OFF = StringVar()
            self.SD_Off = Entry(self.GPSTide_op, width=15, textvariable=self.SD_OFF, state='disabled')
            self.SD_Off_text = Label(self.GPSTide_op, text="Sounding Datum \n Offset")
            self.SD_Off_text.grid(row=4, column=0, sticky=W)
            self.SD_Off.grid(row=4, column=1, sticky=W)


            self.W_L = StringVar()
            WL_op = ['VESSEL',
                  'REALTIME',
                  'NONE']

            self.W_l = ttk.Combobox(self.GPSTide_op, values=WL_op, width=15, textvariable=self.W_L)
            self.W_l_text = Label(self.GPSTide_op, text="Waterline")
            self.W_l_text.grid(row=5, column=0, sticky=W)
            self.W_l.grid(row=5, column=1, sticky=W+E, padx=0)

            self.H_MERGED = StringVar()
            self.H_Merged = Entry(self.GPSTide_op, width=15, textvariable=self.H_MERGED, state='disabled')
            self.H_Merged_text = Label(self.GPSTide_op, text="Heave Type")
            self.H_Merged_text.grid(row=6, column=0, sticky=W)
            self.H_Merged.grid(row=6, column=1, sticky=W, padx=1)

            Parameters = pd.read_csv('Parameters.txt', delimiter=',', header=None)
            CGPSVA = Parameters.iloc[7,0]
            SDO = Parameters.iloc[7,1]
            MF = Parameters.iloc[7,2]
            INFO = Parameters.iloc[7,3]
            CRS_INFO = Parameters.iloc[7,4]
            WL = Parameters.iloc[7,5]
            HEAVE_M = Parameters.iloc[8,0]

            self.M_F.set(MF)
            self.INFO_F.set(INFO)
            self.INFO_CRS.set(CRS_INFO)
            self.SD_OFF.set(SDO)
            self.C_GPS_ADJ.set(CGPSVA)
            self.W_L.set(WL)
            self.H_MERGED.set(HEAVE_M)

            try:
                ## Forget the Observed/Predicted Tides
                self.OPTide_op.grid_forget()
            except AttributeError:
                pass

        elif self.T_T.get()==2:
            self.OPTide_op = LabelFrame(frame4, text="Import Observed/Pedicted Tides", foreground="blue")
            self.OPTide_op.grid(row=1, column=0, sticky=W)

            self.T_F = StringVar()
            self.T_f = Entry(self.OPTide_op, width=15, textvariable=self.T_F)
            self.T_f_text = Label(self.OPTide_op, text="Tide File")
            self.T_f_text.grid(row=0, column=0, sticky=W)
            self.T_f.grid(row=0, column=1, sticky=W)
            self.ButtonTF = Button(self.OPTide_op, text="...", height=0,
                              command=self.Search_TIDE_File)
            self.ButtonTF.grid(row=0, column=2, sticky=W, padx=2)

            self.W_Ave = IntVar()
            self.W_ave = Checkbutton(self.OPTide_op, variable=self.W_Ave, text= "Weighted Average", state='disabled')
            self.W_ave.grid(row=1, column=0, sticky=W)

            self.COMP_Errors = IntVar()
            self.COMP_errors = Checkbutton(self.OPTide_op, variable=self.COMP_Errors, text= "Compute Errors", state='disabled')
            self.COMP_errors.grid(row=2, column=0, sticky=W)

            self.H_MERGED = StringVar()
            self.H_Merged = Entry(self.OPTide_op, width=15, textvariable=self.H_MERGED, state='disabled')
            self.H_Merged_text = Label(self.OPTide_op, text="Heave Type")
            self.H_Merged_text.grid(row=3, column=0, sticky=W)
            self.H_Merged.grid(row=3, column=1, sticky=W, padx=1)

            Parameters = pd.read_csv('Parameters.txt', delimiter=',', header=None)
            TF = Parameters.iloc[6,0]
            WAVE = Parameters.iloc[6,1]
            COMPE = Parameters.iloc[6,2]
            HEAVE_M = Parameters.iloc[8,0]

            self.T_F.set(TF)
            self.W_Ave.set(WAVE)
            self.COMP_Errors.set(COMPE)
            self.H_MERGED.set(HEAVE_M)

            try:
                ## Forget the GPS Tide Options
                self.GPSTide_op.grid_forget()
            except AttributeError:
                pass


    def Load_TPU_Par(self):

        self.TPU_msg = LabelFrame(frame5, text="TPU User Message", foreground="blue")
        self.TPU_msg.grid(row=0, column=1, padx=1, sticky=N+W)

        msg = 'Situation\nPOS - VESSEL\nSBET - REALTIME'

        self.User_Msg_TPU = Text(self.TPU_msg, width=15, height=3)
        self.User_Msg_TPU.insert(END, msg)
        self.User_Msg_TPU.config(state='disabled')
        self.User_Msg_TPU.grid(row=0, column=0, padx=1, sticky=W)

        if self.COMP_TPU.get()==1:

            self.Comptpu_op = LabelFrame(frame5, text="Compute TPU", foreground="blue")
            self.Comptpu_op.grid(row=1, column=0, sticky=N+W)

            TPU_op = ['VESSEL',
                  'REALTIME']

            self.TIDE_M = StringVar()
            self.TIDE_m = Entry(self.Comptpu_op, width=10, textvariable=self.TIDE_M, state='normal')
            self.TIDE_m_text = Label(self.Comptpu_op, text="Measured Tide")
            self.TIDE_m_text.grid(row=0, column=0, sticky=W)
            self.TIDE_m.grid(row=0, column=1, sticky=W, padx=1)

            self.SV_M = StringVar()
            self.SV_m = Entry(self.Comptpu_op, width=10, textvariable=self.SV_M, state='normal')
            self.SV_m_text = Label(self.Comptpu_op, text="Measured Sound Velocity")
            self.SV_m_text.grid(row=1, column=0, sticky=W)
            self.SV_m.grid(row=1, column=1, sticky=W, padx=1)

            self.SS_V = StringVar()
            self.SS_v = Entry(self.Comptpu_op, width=10, textvariable=self.SS_V, state='normal')
            self.SS_v_text = Label(self.Comptpu_op, text="Surface Sound Velocity")
            self.SS_v_text.grid(row=3, column=0, sticky=W)
            self.SS_v.grid(row=3, column=1, sticky=W, padx=1)

            self.S_N = StringVar()
            self.S_n = ttk.Combobox(self.Comptpu_op, values=TPU_op, width=15, textvariable=self.S_N)
            self.S_n_text = Label(self.Comptpu_op, text="Navigation Source")
            self.S_n_text.grid(row=4, column=0, sticky=W)
            self.S_n.grid(row=4, column=1, sticky=W, padx=1)

            self.S_G = StringVar()
            self.S_g = ttk.Combobox(self.Comptpu_op, values=TPU_op, width=15, textvariable=self.S_G)
            self.S_g_text = Label(self.Comptpu_op, text="GYRO Source")
            self.S_g_text.grid(row=5, column=0, sticky=W)
            self.S_g.grid(row=5, column=1, sticky=W, padx=1)

            self.S_S = StringVar()
            self.S_s = ttk.Combobox(self.Comptpu_op, values=TPU_op, width=15, textvariable=self.S_S)
            self.S_s_text = Label(self.Comptpu_op, text="Sonar Source")
            self.S_s_text.grid(row=6, column=0, sticky=W)
            self.S_s.grid(row=6, column=1, sticky=W, padx=1)

            self.S_P = StringVar()
            self.S_p = ttk.Combobox(self.Comptpu_op, values=TPU_op, width=15, textvariable=self.S_P)
            self.S_p_text = Label(self.Comptpu_op, text="Pitch Source")
            self.S_p_text.grid(row=7, column=0, sticky=W)
            self.S_p.grid(row=7, column=1, sticky=W, padx=1)

            self.S_R = StringVar()
            self.S_r = ttk.Combobox(self.Comptpu_op, values=TPU_op, width=15, textvariable=self.S_R)
            self.S_r_text = Label(self.Comptpu_op, text="Roll Source")
            self.S_r_text.grid(row=8, column=0, sticky=W)
            self.S_r.grid(row=8, column=1, sticky=W, padx=1)

            self.S_H = StringVar()
            self.S_h = ttk.Combobox(self.Comptpu_op, values=TPU_op, width=15, textvariable=self.S_H)
            self.S_h_text = Label(self.Comptpu_op, text="Heave Source")
            self.S_h_text.grid(row=9, column=0, sticky=W)
            self.S_h.grid(row=9, column=1, sticky=W, padx=1)

            self.S_Tide = StringVar()
            self.S_tide = Entry(self.Comptpu_op, width=10, textvariable=self.S_Tide, state='disabled')
            self.S_tide_text = Label(self.Comptpu_op, text="Tide Source")
            self.S_tide_text.grid(row=10, column=0, sticky=W)
            self.S_tide.grid(row=10, column=1, sticky=W, padx=1)

            self.Merge_op = LabelFrame(frame5, text="Merge", foreground="blue")
            self.Merge_op.grid(row=0, column=0, sticky=N+W)

            self.H_MERGED = StringVar()
            self.H_Merged = Entry(self.Merge_op, width=20, textvariable=self.H_MERGED, state='disabled')
            self.H_Merged_text = Label(self.Merge_op, text="Heave Type")
            self.H_Merged_text.grid(row=0, column=0, sticky=W)
            self.H_Merged.grid(row=0, column=1, sticky=W, padx=1)

            self.VERT_REF = StringVar()
            vert_ref = ['NONE',
                        'GPS',
                        'TIDE']

            self.VREF_op = ttk.Combobox(self.Merge_op, values=vert_ref, width=7, textvariable=self.VERT_REF)
            self.VREF_text = Label(self.Merge_op, text="Choose Vertical Reference")
            self.VREF_text.grid(row=1, column=0, sticky=W)
            self.VREF_op.grid(row=1, column=1, sticky=W+E, padx=0)

            Parameters = pd.read_csv('Parameters.txt', delimiter=',', header=None)
            MEAS_TIDE = Parameters.iloc[9,0]
            MEAS_SP = Parameters.iloc[9,1]
            SSP = Parameters.iloc[9,2]
            NAV_S = Parameters.iloc[9,3]
            SONAR_S = Parameters.iloc[9,4]
            GYRO_S = Parameters.iloc[9,5]
            PITCH_S = Parameters.iloc[9,6]
            ROLL_S = Parameters.iloc[9,7]
            HEAVE_S = Parameters.iloc[9,8]
            TIDE_S = Parameters.iloc[9,9]
            HEAVE_M = Parameters.iloc[8,0]
            VERT_R = Parameters.iloc[8,1]

            self.TIDE_M.set(MEAS_TIDE)
            self.SV_M.set(MEAS_SP)
            self.SS_V.set(SSP)
            self.S_N.set(NAV_S)
            self.S_S.set(SONAR_S)
            self.S_G.set(GYRO_S)
            self.S_P.set(PITCH_S)
            self.S_R.set(ROLL_S)
            self.S_H.set(HEAVE_S)
            self.S_Tide.set(TIDE_S)
            self.H_MERGED.set(HEAVE_M)
            self.VERT_REF.set(VERT_R)

        if self.COMP_TPU.get()==0:
            try:
                ## Forget TPU Options
                self.Comptpu_op.grid_forget()
                self.Merge_op.grid_forget()
            except AttributeError:
                pass


    def GEOREFERENCE_HIPS(self):

        PH = self.split_Project_Name()
        Project_N = PH[0]
        HIPSFILE = PH[1]
        HDCS_Folder = self.HDCS_D.get()

        Vessel_F = self.VESSEL_N.get()
        Vessel = path.basename(Vessel_F)
        Vessel = path.splitext(Vessel)[0]
        Year = (self.Year.get())
        JD = self.JULIAN_D.get()
        Out = self.OUT_F.get()

        if self.T_T.get()==1:
            Model_File = self.M_F.get()
            Info_File = self.INFO_F.get()
            Info_CRS = self.INFO_CRS.get()
            self.SD_OFF.get()
            self.C_GPS_ADJ.get()
            Water_Line = self.W_L.get()

            with open("Import_Tides.bat", "w") as Import:
                Import.write('@ECHO OFF' + '\n')
                Import.write('@ECHO Importing GPS Tides' + '\n')
                Import.write('cd '+ Caris + '\n')
                Import.write('carisbatch --run GeoreferenceHIPSBathymetry --vertical-datum-reference GPS' +
                             ' --datum-model-file ' + Model_File)
                if (Model_File.endswith('.txt') or Model_File.endswith('.csv')
                    or Model_File.endswith('.xyz')):
                    Import.write(' --info-file ' + Info_File)
                    Import.write(' --input-crs ' + Info_CRS)
                else:
                    Import.write(' --datum-model-band DEPTH')
                if self.C_GPS_ADJ.get()==1:
                    Import.write(' --compute-gps-vertical-adjustment --GPS-Vertical-Components CUSTOM --GPS-Component-Waterline ' + Water_Line)
                    Import.write(' --GPS-Component-Dynamic-Heave DELAYED_HEAVE --heave-source DELAYED_HEAVE' +
                                 ' --output-components')
                Import.write(r' file:///' + HDCS_Folder + '/' + HIPSFILE + '/' + HIPSFILE + '.hips?Vessel=' + Vessel +
                            ';Day=' + str(Year) + '-' + str(JD) + ' > ' + Out + '/' + JD + '/' +
                            '3.Compute_GPSTIDE_' + JD + '_' + Year + '.txt' + '\n')

            p = S.check_call("Import_Tides.bat", stdin=None, stdout=None, stderr=None, shell=False)

        elif self.T_T.get()==2:
            Tide_File = self.T_F.get()
            W_Ave = self.W_Ave.get()
            COMP_Errors = self.COMP_Errors.get()

            with open("Import_Tides.bat", "w") as Import:
                Import.write('@ECHO OFF' + '\n')
                Import.write('@ECHO Importing Observed/Predicted Tides' + '\n')
                Import.write('cd '+ Caris + '\n')
                Import.write('carisbatch --run GeoreferenceHIPSBathymetry --vertical-datum-reference TIDE'+
                             ' --tide-file ' + Tide_File)
                if W_Ave == 1:
                    Import.write(' --weighted-average ')
                if COMP_Errors == 1:
                    Import.write(' --compute-errors ')
                Import.write(' --heave-source DELAYED_HEAVE')
                Import.write(r' file:///' + HDCS_Folder + '/' + HIPSFILE + '/' + HIPSFILE + '.hips?Vessel=' + Vessel +
                            ';Day=' + str(Year) + '-' + str(JD) + ' > ' + Out + '/' + JD + '/' +
                            '3.Import_OBSERVEDTIDE_' + JD + '_' + Year + '.txt' + '\n')

            p = S.check_call("Import_Tides.bat", stdin=None, stdout=None, stderr=None, shell=False)

        if self.COMP_TPU.get()==1:
            Meas_Tide = self.TIDE_M.get()
            Meas_SV = self.SV_M.get()
            Surf_So = self.SS_V.get()
            Nav_Source = self.S_N.get()
            Gyro_Source = self.S_G.get()
            Sonar_Source = self.S_S.get()
            Pitch_Source = self.S_P.get()
            Roll_Source = self.S_R.get()
            Heave_Source = self.S_H.get()
            Tide_Source = self.S_Tide.get()
            Heave_M = self.H_MERGED.get()
            Vert_Ref = self.VERT_REF.get()

            with open("Compute_TPU.bat", "w") as Import:
                Import.write('@ECHO OFF' + '\n')
                Import.write('@ECHO Computing TPU' + '\n')
                Import.write('cd '+ Caris + '\n')
                Import.write('carisbatch --run GeoreferenceHIPSBathymetry --vertical-datum-reference ' + str(Vert_Ref) +
                             ' --heave-source ' + str(Heave_M) + ' --compute-tpu ' +
                             '--tide-measured ' + str(Meas_Tide) + ' --sv-measured ' + str(Meas_SV) +
                             ' --sv-surface ' + str(Surf_So) + ' --source-sonar ' + Sonar_Source +
                             ' --source-navigation ' + Nav_Source +
                             ' --source-gyro ' + Gyro_Source +
                             ' --source-pitch ' + Pitch_Source +
                             ' --source-roll ' + Roll_Source + ' --source-heave ' + Heave_Source +
                             ' --source-tide ' + Tide_Source)
                Import.write(r' file:///' + HDCS_Folder + '/' + HIPSFILE + '/' + HIPSFILE + '.hips?Vessel=' + Vessel +
                            ';Day=' + str(Year) + '-' + str(JD) + ' > ' + Out + '/' + str(JD) + '/' +
                            '4.Compute_TPU_' + JD + '_' + Year + '.txt' + '\n')

            p = S.check_call("Compute_TPU.bat", stdin=None, stdout=None, stderr=None, shell=False)
            

    def Load_GRID_Par(self):

        chdir(owd)

        if self.GRID.get()==1:
            self.CREATEGRID_op = LabelFrame(frame7, text="Create HIPS Grid", foreground="blue")
            self.CREATEGRID_op.grid(row=0, column=0, sticky=W)

            self.RES = StringVar()
            self.res = Entry(self.CREATEGRID_op, width=5, textvariable=self.RES)
            self.res_text = Label(self.CREATEGRID_op, text="Surface Resolution")
            self.res_text.grid(row=0, column=0, sticky=W)
            self.res.grid(row=0, column=1, sticky=W)

            self.GRID_DIR = StringVar()
            self.GRID_dir = Entry(self.CREATEGRID_op, width=32, textvariable=self.GRID_DIR)
            self.GRID_dir_text = Label(self.CREATEGRID_op, text="Surface Dir")
            self.GRID_dir_text.grid(row=1, column=0, sticky=W)
            self.GRID_dir.grid(row=1, column=1, sticky=W)
            self.ButtonG_dir = Button(self.CREATEGRID_op, text="...", height=0,
                                   command=self.Search_Grid_Dir)
            self.ButtonG_dir.grid(row=1, column=2, sticky=W, padx=2)

            self.IHO_ORDER = StringVar()
            iho_op = ['S44_SPECIAL',
                      'S44_1A',
                      'S44_1B',
                      'S44_2']
            self.IHO_op = ttk.Combobox(self.CREATEGRID_op, values=iho_op, width=10, textvariable=self.IHO_ORDER)
            self.IHO_text = Label(self.CREATEGRID_op, text="Choose IHO Order")
            self.IHO_text.grid(row=2, column=0, sticky=W)
            self.IHO_op.grid(row=2, column=1, sticky=W+E, padx=0)

            Parameters = pd.read_csv('Parameters.txt', delimiter=',', header=None)
            RES = Parameters.iloc[10,0]
            IHOORDER = Parameters.iloc[10,1]
            GRIDDIR = Parameters.iloc[10,2]

            self.RES.set(RES)
            self.IHO_ORDER.set(IHOORDER)
            self.GRID_DIR.set(GRIDDIR)

            try:
                ## Forget Create Grid 2
                self.CREATEGRID2_op.grid_forget()
            except AttributeError:
                pass

        if self.GRID.get()==2:

            self.CREATEGRID2_op = LabelFrame(frame7, text="Create/Add to HIPS Grid", foreground="blue")
            self.CREATEGRID2_op.grid(row=1, column=0, padx=1, sticky=W)

            self.RES = StringVar()
            self.res = Entry(self.CREATEGRID2_op, width=5, textvariable=self.RES)
            self.res_text = Label(self.CREATEGRID2_op, text="Surface Resolution")
            self.res_text.grid(row=0, column=0, sticky=W)
            self.res.grid(row=0, column=1, sticky=W)

            self.GRID_DIR = StringVar()
            self.GRID_dir = Entry(self.CREATEGRID2_op, width=32, textvariable=self.GRID_DIR)
            self.GRID_dir_text = Label(self.CREATEGRID2_op, text="Surface Dir")
            self.GRID_dir_text.grid(row=1, column=0, sticky=W)
            self.GRID_dir.grid(row=1, column=1, sticky=W)
            self.ButtonG_dir = Button(self.CREATEGRID2_op, text="...", height=0,
                                   command=self.Search_Grid_Dir)
            self.ButtonG_dir.grid(row=1, column=2, sticky=W, padx=2)

            self.IHO_ORDER = StringVar()
            iho_op = ['S44_SPECIAL',
                      'S44_1A',
                      'S44_1B',
                      'S44_2']
            self.IHO_op = ttk.Combobox(self.CREATEGRID2_op, values=iho_op, width=10, textvariable=self.IHO_ORDER)
            self.IHO_text = Label(self.CREATEGRID2_op, text="Choose IHO Order")
            self.IHO_text.grid(row=3, column=0, sticky=W)
            self.IHO_op.grid(row=3, column=1, sticky=W+E, padx=0)


            Parameters = pd.read_csv('Parameters.txt', delimiter=',', header=None)
            RES = Parameters.iloc[10,0]
            IHOORDER = Parameters.iloc[10,1]
            GRIDDIR = Parameters.iloc[10,2]
            COVERAGE = Parameters.iloc[10,3]

            self.RES.set(RES)
            self.IHO_ORDER.set(IHOORDER)
            self.GRID_DIR.set(GRIDDIR)

            try:
                ##Forget Create Grid
                self.CREATEGRID_op.grid_forget()
            except AttributeError:
                pass


    def Create_Addto_Hips_Grid(self):

        PH = self.split_Project_Name()

        if PH[0] is None:
            return
        
        Project_N = PH[0]
        HIPSFILE = PH[1]

        Res = self.RES.get()
        Res = str(Res).strip()
        
        try:
            if not Res.endswith('m'):
                Res = Res + 'm'
            
            Res_no = float(Res.replace('m', ''))
        
        except ValueError:
            messagebox.showerror("Error", f"Invalid resolution value: '{Res}'\nExpected format: e.g. 10m")
            return
        
        Res_List = ['2m', '5m', '10m', '20m', '30m', '50m', '100m', '200m', '300m', Res]
        thresholds = [1, 5, 10, 20, 30, 50, 100, 200, 300]

        Res_P = None

        for i, limit in enumerate(thresholds):
            if Res_no <= limit:
                Res_P = Res_List[i]
                break
        
        if Res_P is None:
            Res_P = Res_List[-1]

        IHO = self.IHO_ORDER.get()
        Dir_Grid = self.GRID_DIR.get()
        HDCS_Folder = self.HDCS_D.get()
        Vessel_F = self.VESSEL_N.get()
        Vessel = path.basename(Vessel_F)
        Vessel = path.splitext(Vessel)[0]
        Year = (self.Year.get())
        JD = self.JULIAN_D.get()
        Out = self.OUT_F.get()
        os.makedirs(os.path.join(Out, str(JD)), exist_ok=True)
        crs = self.CRS_O.get()
        CRS = crs.partition(": ")[-1] if ": " in crs else crs
        if CRS=='EPSG:7912@2010':
            CRS2 = 'EPSG:5937'
        else:
            CRS2 = CRS
        VCRS = 'CUSTOM:69036444' ## CHS PACD Vertical Reference
        G_M = ('CUBE')
        E_R = ('GEOTIFF')

        if self.GRID.get()==1:

            with open("Create_Grid.bat", "w") as Import:
                Import.write('@ECHO OFF' + '\n')
                Import.write('cd '+ Caris + '\n')
                Import.write('@ECHO Creating Grids' + '\n')

                ##Create Surface to Add Future Days to
                Import.write('carisbatch --run CreateHIPSGrid --gridding-method ' + G_M +
                             ' --resolution ' + str(Res_P) + ' --Output-crs ' + CRS2 +
                             ' --output-vertical-crs ' + VCRS +
                             ' --compute-band SHOAL --compute-band DEEP --compute-band DENSITY' +
                             ' --compute-band MEAN --compute-band STD_DEV ' +
                             ' --include-flag ACCEPTED --include-flag EXAMINED --include-flag OUTSTANDING ' +
                             ' --keep-up-to-date ' + ' --iho-order ' + IHO +
                             ' --disambiguation-method DENSITY_LOCALE')
                Import.write(r' file:///' + HDCS_Folder + '/'  + HIPSFILE + '/' + HIPSFILE + '.hips?Vessel=' + Vessel +
                            ';Day=' + str(Year) + '-' + str(JD) + ' ' +
                             Dir_Grid + '/' + Project_N + '.csar' +
                             ' > ' + Out + '/' + JD + '/' + '6.Create_JD_Grid_' + JD + '_' + Year + '.txt' + '\n')
                Import.write('carisbatch --run ExportRaster --output-format ' + E_R +
                             ' --include-band Depth ' +
                             Dir_Grid + '/' + Project_N + '.csar ' +
                             Dir_Grid + '/' + Project_N + '.geotiff' + '\n')

                ##Create Surface Containing only Daily Julian Day Data
                Import.write('carisbatch --run CreateHIPSGrid --gridding-method ' + G_M +
                             ' --resolution ' + str(Res) + ' --Output-crs ' + CRS2 +
                             ' --output-vertical-crs ' + VCRS +
                             ' --compute-band SHOAL --compute-band DEEP --compute-band DENSITY' +
                             ' --compute-band MEAN --compute-band STD_DEV ' +
                             ' --include-flag ACCEPTED --include-flag EXAMINED --include-flag OUTSTANDING ' +
                             ' --keep-up-to-date ' + ' --iho-order ' + IHO +
                             ' --disambiguation-method DENSITY_LOCALE')
                Import.write(r' file:///' + HDCS_Folder + '/'  + HIPSFILE + '/' + HIPSFILE + '.hips?Vessel=' + Vessel +
                            ';Day=' + str(Year) + '-' + str(JD) + ' ' +
                             Dir_Grid + '/' + str(JD) + '_' + str(Year) + '.csar' +
                             ' > ' + Out + '/' + JD + '/' + '6.Create_Project_Grid_' + JD + '_' + Year + '.txt' + '\n')
                Import.write('carisbatch --run ExportRaster --output-format ' + E_R +
                             ' --include-band Depth ' +
                             Dir_Grid + '/' + str(JD) + '_' + str(Year) + '.csar ' +
                             Dir_Grid + '/' + str(JD) + '_' + str(Year) + '.geotiff')

        elif self.GRID.get()==2:

            with open("Create_Grid.bat", "w") as Import:
                Import.write('@ECHO OFF' + '\n')
                Import.write('cd '+ Caris + '\n')
                Import.write('@ECHO Creating and Adding to Grid' + '\n')

                ## Add Hips to Project Surface
                Import.write('carisbatch --run AddToHIPSGrid ')
                Import.write(r' file:///' + HDCS_Folder + '/'+ HIPSFILE + '/' + HIPSFILE + '.hips?Vessel=' + Vessel +
                            ';Day=' + str(Year) + '-' + str(JD) + ' ' +
                            Dir_Grid + '/' + Project_N + '.csar' +
                            ' > ' + Out + '/' + JD + '/' + '6.Add_to_Grid_' + JD + '_' + Year + '.txt' + '\n')

                ##Create Surface Containing only Daily Julian Day Data
                Import.write('carisbatch --run CreateHIPSGrid --gridding-method ' + G_M +
                             ' --resolution ' + str(Res) + ' --Output-crs ' + CRS2 +
                             ' --output-vertical-crs ' + VCRS +
                             ' --compute-band SHOAL --compute-band DEEP --compute-band DENSITY' +
                             ' --compute-band MEAN --compute-band STD_DEV ' +
                             ' --include-flag ACCEPTED --include-flag EXAMINED --include-flag OUTSTANDING ' +
                             ' --keep-up-to-date ' + ' --iho-order ' + IHO +
                             ' --disambiguation-method DENSITY_LOCALE')
                Import.write(r' file:///' + HDCS_Folder + '/'  + HIPSFILE + '/' + HIPSFILE + '.hips?Vessel=' + Vessel +
                            ';Day=' + str(Year) + '-' + str(JD) + ' ' +
                             Dir_Grid + '/' + str(JD) + '_' + str(Year) + '.csar' +
                             ' > ' + Out + '/' + JD + '/' + '6.Create_JD_Grid_' + JD + '_' + Year + '.txt' + '\n')
                Import.write('carisbatch --run ExportRaster --output-format ' + E_R +
                         ' --include-band Depth ' +
                         Dir_Grid + '/' + Project_N + '.csar ' +
                         Dir_Grid + '/' + Project_N + '.geotiff' + '\n')
                Import.write('carisbatch --run ExportRaster --output-format ' + E_R +
                         ' --include-band Depth ' +
                         Dir_Grid + '/' + str(JD) + '_' + str(Year) + '.csar ' +
                         Dir_Grid + '/' + str(JD) + '_' + str(Year) + '.geotiff')

        p = S.check_call("Create_Grid.bat", stdin=None, stdout=None, stderr=None, shell=False)


    def Combine_Caris_Output(self):

        Year = (self.Year.get())
        JD = self.JULIAN_D.get()
        Out = self.OUT_F.get()
        chdir(Out + '/' + JD)
        OutFiles = [f for f in listdir(Out + '/' + JD) if re.match(r'[0-9]+.*\.txt', f)]
        with open('Caris_Output_' + str(JD) + '_' + str(Year) + '.txt', 'w') as fout, fileinput.input(OutFiles) as fin:
            for line in fin:
                fout.write(line)
        startfile('Caris_Output_' + str(JD) + '_' + str(Year) + '.txt')


    def Sub_Rep(self):

        chdir(owd)

        self.sub_op = LabelFrame(frame9, text="Reports, QC and Submissions", foreground="blue")
        self.sub_op.grid(row=0, column=0, sticky=W)

        self.D_R = IntVar()
        self.D_r = Checkbutton(self.sub_op, onvalue=1, offvalue=0, variable=self.D_R, text= "Reports and QC",
                               command=self.Load_Daily_Reports)
        self.D_r.grid(row=0, column=0, sticky=W)

        self.RUN_FF = IntVar()
        self.RUN_ff = Checkbutton(self.sub_op, onvalue=1, offvalue=0, variable=self.RUN_FF, text= "Flier Finder",
                                    command=self.Load_FlierFinder)
        self.RUN_ff.grid(row=0, column=1, sticky=W)

    
    def Sub_Final(self):

        chdir(owd)

        self.sub_final = LabelFrame(frame10, text="Finalization", foreground="blue")
        self.sub_final.grid(row=0, column=0, sticky=W)

        self.Finalize = IntVar()
        self.Finalize_t = Checkbutton(self.sub_final, onvalue=1, offvalue=0, variable=self.Finalize, text="Finalize Surfaces",
                                      command=self.Load_Finalization_Submission)
        self.Finalize_t.grid(row=0, column=0, sticky=W)

        self.HDC_F = IntVar()
        self.HDC_f = Checkbutton(self.sub_final, onvalue=1, offvalue=0, variable=self.HDC_F, text= "HDC ISO Submission Form",
                                    command=self.Load_ATL_SUB_ISO)
        self.HDC_f.grid(row=0, column=1, sticky=W)

        self.SOUACC_F = IntVar()
        self.SOUACC_cb = Checkbutton(self.sub_final, onvalue=1, offvalue=0, variable=self.SOUACC_F, text="SOUACC", command=self.Load_SOUACC)
        self.SOUACC_cb.grid(row=0, column=2, sticky=W)

        self.BP = IntVar()
        self.Bp = Checkbutton(self.sub_final, onvalue=1, offvalue=0, variable=self.BP, text= "Bounding Polygon",
                                    command=self.Load_BoundingPoly)
        self.Bp.grid(row=0, column=3, sticky=W)


    def Load_CATOOLS_Par(self):

        if self.CATOOLS.get() == 1:

            self.CATOOLS_op = LabelFrame(frame8, text="Find NAVWARNS", foreground="blue")
            self.CATOOLS_op.grid(row=0, column=0, sticky=W)

            self.CA_algo = StringVar()
            self.CA_algo.set("POINT_ADDITIVE_v2")
            Label(self.CATOOLS_op, text="Sounding Selection Algorithm").grid(row=0, column=0, sticky=W)
            ttk.Combobox(self.CATOOLS_op, textvariable=self.CA_algo, values=["POINT_ADDITIVE_v2", "MOVING_WINDOW_v2"], state="readonly").grid(row=0, column=1, sticky=W)

            self.CA_mode = StringVar()
            self.CA_mode.set("single")
            Label(self.CATOOLS_op, text="DTM Mode").grid(row=1, column=0, sticky=W)
            Radiobutton(self.CATOOLS_op, text="Single Surface", variable=self.CA_mode, value="single").grid(row=1, column=1, sticky=W)
            Radiobutton(self.CATOOLS_op, text="Multiple Surfaces", variable=self.CA_mode, value="multi").grid(row=2, column=1, sticky=W)

            self.CA_input_mode = StringVar()
            self.CA_input_mode.set("auto")
            Label(self.CATOOLS_op, text="Surface Source").grid(row=3, column=0, sticky=W)
            Radiobutton(self.CATOOLS_op, text="Use Generated Surfaces", variable=self.CA_input_mode, value="auto", command=self.Toggle_CA_Input_Mode).grid(row=3, column=1, sticky=W)
            Radiobutton(self.CATOOLS_op, text="Use Custom Surfaces", variable=self.CA_input_mode, value="manual", command=self.Toggle_CA_Input_Mode).grid(row=3, column=2, sticky=W)

            self.CA_DTM_var = StringVar()
            Label(self.CATOOLS_op, text="CSAR Folder").grid(row=4, column=0, sticky=W)
            self.CA_DTM_entry = Entry(self.CATOOLS_op, width=35, textvariable=self.CA_DTM_var)
            self.CA_DTM_entry.grid(row=4, column=1, sticky=W)
            self.CA_DTM_button = Button(self.CATOOLS_op, text="...", command=self.CA_DTM_Selection)
            self.CA_DTM_button.grid(row=4, column=2, sticky=W, padx=10)

            self.CA_ENC_var = StringVar()
            Label(self.CATOOLS_op, text="ENC Folder").grid(row=5, column=0, sticky=W)
            Entry(self.CATOOLS_op, width=35, textvariable=self.CA_ENC_var).grid(row=5, column=1, sticky=W)
            Button(self.CATOOLS_op, text="...", command=self.CA_ENC_Selection).grid(row=5, column=2, sticky=W, padx=10)

            self.CA_OUT_var = StringVar()
            Label(self.CATOOLS_op, text="Output Folder").grid(row=6, column=0, sticky=W)
            Entry(self.CATOOLS_op, width=35, textvariable=self.CA_OUT_var).grid(row=6, column=1, sticky=W)
            Button(self.CATOOLS_op, text="...", command=self.CA_OUT_Selection).grid(row=6, column=2, sticky=W, padx=10)

            self.CA_progress = ttk.Progressbar(self.CATOOLS_op, orient=HORIZONTAL, length=300, mode='determinate')
            self.CA_progress.grid(row=7, column=0, columnspan=3, padx=5, pady=5, sticky=EW)
            self.progress_label = Label(self.CATOOLS_op, text="Idle")
            self.progress_label.grid(row=8, column=0, columnspan=3, pady=(0,5))

            Button(self.CATOOLS_op, text="Run CA Tools", command=self.Run_CATools_UI).grid(row=9, column=0, columnspan=3, pady=5)

            self.Toggle_CA_Input_Mode()

        else:
            try:
                self.CATOOLS_op.grid_forget()
            except AttributeError:
                pass
        
    def CA_ENC_Selection(self):

        enc_folder = filedialog.askdirectory(title="Select ENC Folder")

        if not enc_folder:
            print("No ENC folder selected.")
            return
        
        self.CA_ENC_var.set(enc_folder)
        
        self.ENC_paths = []

        for root, dirs, files in os.walk(enc_folder):
            for f in files:
                if f.lower().endswith(".000"):
                    full_path = os.path.join(root, f)
                    self.ENC_paths.append(full_path)


    def CA_DTM_Selection(self):

        mode = self.CA_mode.get()

        if mode == "single":
            folder = filedialog.askdirectory(title="Select Folder of CSAR Files")
            if folder:
                self.dtms = [folder]
                self.CA_DTM_var.set(folder)
        else:
            folder = filedialog.askdirectory(title="Select Folder of CSAR Files")
            if folder:
                self.dtms = [folder]
                self.CA_DTM_var.set(folder)

        #filetypes = [("DTM", "*.bag *.tif *.tiff"),
                     #("all files", "*.*")]
        
        #mode = self.CA_mode.get()

        #if mode == "single":
            #dtm = filedialog.askopenfilename(title="Select DTM", filetypes=filetypes)
            #if dtm:
                #self.dtms = [dtm]
                #self.CA_DTM_var.set(dtm)
        #else:
            #dtms = filedialog.askopenfilenames(title="Select Multiple DTMs", filetypes=filetypes)
            #if dtms:
                #self.dtms = list(dtms)
                #display_text = "; ".join(dtms)
                #self.CA_DTM_var.set(display_text)

    
    def CA_OUT_Selection(self):

        out_folder = filedialog.askdirectory(title="Select Output Folder")

        if not out_folder:
            print("No output folder selected.")
            return
        
        self.CA_OUT_var.set(out_folder)

    
    def Run_CATools(self):

        if not hasattr(self, "ENC_paths") or not self.ENC_paths:
            print("No ENC files selected.")
            return

        if not hasattr(self, "dtms") or not self.dtms:
            print("No DTM selected.")
            return

        algo_flag = self.CA_algo.get()
        
        #dtms = self.dtms
        if self.CA_input_mode.get() == "manual":
            csar_folder = self.dtms[0]

            geotiff_list = []

            with open("CSAR_to_TIFF.bat", "w") as conv:
                conv.write('@ECHO OFF\n')
                conv.write('cd /d "' + Caris + '"\n')

                for root, dirs, files in os.walk(csar_folder):
                    for f in files:
                        if f.lower().endswith(".csar"):
                            csar_path = os.path.join(root, f)
                            tiff_path = os.path.splitext(csar_path)[0] + ".tiff"
                            conv.write(
                                f'carisbatch --run ExportRaster --output-format GEOTIFF '
                                f'--include-band Depth "{csar_path}" "{tiff_path}"\n')
                            geotiff_list.append(tiff_path)
            if not geotiff_list:
                print("No CSAR files found.")
                return
            
            S.call("CSAR_to_TIFF.bat", shell=True)

            dtms = geotiff_list
        
        else:
            dtms = self.dtms
        
        total_jobs = (len(dtms) + (len(dtms) * len(self.ENC_paths)))
        completed_jobs = 0
        self.CA_progress["maximum"] = total_jobs

        if self.CA_OUT_var.get():
            base_output = self.CA_OUT_var.get()
        else:
            base_output = path.join(path.dirname(dtms[0]), 'Output')
            #base_output = r"C:\CATools_Out"

        if not path.exists(base_output):
            mkdir(base_output)

        with open('ChartCompare.bat', "w") as CC:
            CC.write('@ECHO OFF' + '\n')
            CC.write('cd /d "' + CATools + '"\n')

            first_enc = self.ENC_paths[0]

            for dtm in dtms:
                dtm_name = os.path.splitext(os.path.basename(dtm))[0]

                output_dir = os.path.join(base_output, dtm_name)
                os.makedirs(output_dir, exist_ok=True)

                selection_dir = os.path.join(output_dir, "SoundingSelection")
                os.makedirs(selection_dir, exist_ok=True)

                print(f"Generating sounding selection for {dtm_name}")

                completed_jobs += 1
                self.CA_progress["value"] = completed_jobs
                self.progress_label.config(text=f"Sounding Selection: {completed_jobs}/{total_jobs}")
                self.update_idletasks()

                CC.write('CATools SurveyDTMVsChart '
                     '--ss_algo ' + algo_flag + ' '
                     '--th_depth 15.0 --dton_value_less 0.3 --dton_pct_more 10 '
                     '-l -5.0 '
                      f'"{dtm}" '
                      f'"{first_enc}" '
                      f'"{selection_dir}"\n')

        """Running the batch"""
        process = S.Popen("ChartCompare.bat", shell=True, stdout=S.PIPE, stderr=S.STDOUT, text=True)

        output_lines = []

        for line in process.stdout:
            print(line.strip())
            output_lines.append(line)
        
        process.wait()

        sounding_files = {}

        for dtm in dtms:
            dtm_name = os.path.splitext(os.path.basename(dtm))[0]

            selection_dir = os.path.join(base_output, dtm_name, "SoundingSelection")

            for item in os.listdir(selection_dir):
                item_path = os.path.join(selection_dir, item)

                if os.path.isdir(item_path):
                    for root, dirs, files in os.walk(item_path):
                        for f in files:
                            src = os.path.join(root, f)
                            dst = os.path.join(selection_dir, f)

                            print("\nSRC =", src)
                            print("DST =", dst)
                            print("SRC EXISTS =", os.path.exists(src))
                            print("DST EXISTS =", os.path.exists(dst))

                            if not os.path.exists(dst):
                                try:
                                    shutil.move(src, dst)
                                except Exception as e:
                                    print("\nMOVE FAILED")
                                    print("SRC =", src)
                                    print("DST =", dst)
                                    print("SRC EXISTS =", os.path.exists(src))
                                    print("DST EXISTS =", os.path.exists(dst))
                                    print("ERROR =", repr(e))

                                    raise
                    shutil.rmtree(item_path, ignore_errors=True)

            sounding_file = None

            for root, dirs, files in os.walk(selection_dir):
                for f in files:
                    full_file = os.path.join(root, f)
                    if f.lower().endswith("_sb.000"):
                        sounding_file = full_file
                    else:
                        try:
                            os.remove(full_file)
                        except:
                            pass
                    
                
            if sounding_file:
                sounding_files[dtm] = sounding_file
                print("Found sounding file:", sounding_file)
            
        with open("SoundingsVsChart.bat", "w") as SC:
            SC.write("@ECHO OFF\n")
            SC.write('cd /d "' + CATools + '"\n')

            for dtm in dtms:
                sounding_file = sounding_files.get(dtm)

                if not sounding_file:
                    continue

                dtm_name = os.path.splitext(os.path.basename(dtm))[0]

                for enc in self.ENC_paths:
                    enc_name = os.path.splitext(os.path.basename(enc))[0]

                    enc_output_dir = os.path.join(base_output, dtm_name, enc_name)

                    os.makedirs(enc_output_dir, exist_ok=True)

                    completed_jobs += 1
                    self.CA_progress["value"] = completed_jobs
                    self.progress_label.config(text=f"ENC Comparison: {completed_jobs}/{total_jobs}")
                    self.update_idletasks()

                    SC.write('CATools SurveySoundingsVsChart '
                     '--th_depth 15.0 --dton_value_less 0.3 --dton_pct_more 10 '
                     '-l -5.0 '
                      f'"{sounding_file}" '
                      f'"{enc}" '
                      f'"{enc_output_dir}"\n')
        S.call("SoundingsVsChart.bat", shell=True)

        overlap_encs = []
        no_overlap_encs = []

        for dtm in dtms:
            dtm_name = os.path.splitext(os.path.basename(dtm))[0]

            review_dir = os.path.join(base_output, "NAVWARN_REVIEW", dtm_name)

            os.makedirs(review_dir, exist_ok=True)

            dtm_folder = os.path.join(base_output, dtm_name)

            for enc in self.ENC_paths:
                enc_name = os.path.splitext(os.path.basename(enc))[0]

                enc_folder = os.path.join(dtm_folder, enc_name)

                if not os.path.exists(enc_folder):
                    no_overlap_encs.append(enc_name)
                    print(f"[NO OVERLAP] {enc_name}")
                    continue

                for item in os.listdir(enc_folder):
                    item_path = os.path.join(enc_folder, item)

                    if os.path.isdir(item_path):
                            for root, dirs, files in os.walk(item_path):
                                for f in files:
                                    src = os.path.join(root, f)
                                    dst = os.path.join(enc_folder, f)
                                    
                                    if not os.path.exists(dst):
                                        shutil.move(src, dst)
                            shutil.rmtree(item_path, ignore_errors=True)

                files_found = False

                for root, dirs, files in os.walk(enc_folder):
                    if files:
                        files_found = True
                        break
                
                if files_found:
                    overlap_encs.append(enc_name)
                    print(f"[OVERLAP] {enc_name}")
                
                else:
                    no_overlap_encs.append(enc_name)
                    print(f"[NO OVERLAP] {enc_name}")

            for root, dirs, files in os.walk(dtm_folder):
                if "NAVWARN_REVIEW" in root:
                    continue

                for f in files:
                    lower = f.lower()

                    if ("discr_soundings.000" in lower or "dtons_soundings.000" in lower):
                        shutil.copy2(os.path.join(root, f),
                                     os.path.join(review_dir, f))
                        
        output_text = "".join(output_lines)

        lines = output_text.splitlines()
        filtered = [line.strip() for line in lines if "- possible" in line.lower() or "untested features" in line.lower()]

        if filtered:
            summary = "\n".join(filtered)
        else:
            summary = "Processing complete (no summary values found)"

        msg = f"Processing complete\n\n{summary}\n\n"

        if overlap_encs:
            msg += "ENCs with overlap:\n"
            msg += "\n".join(sorted(overlap_encs))
            msg += "\n\n"
        
        if no_overlap_encs:
            msg += "ENCs with NO overlap:\n"
            msg += "\n".join(sorted(no_overlap_encs))

        messagebox.showinfo("DTM vs ENC Results", msg)

        #found = False

        #for _ in range(10):
            #for root, dirs, files in os.walk(path.join(path.dirname(dtms[0]), 'Output')):
                #if any(f.lower().endswith(".png") for f in files):
                    #found = True
                  #  break
            
           # if found:
               # break
           # time.sleep(0.5)

        #for dtm in dtms:
            #dtm_name = path.splitext(path.basename(dtm))[0]
            #output_dir = path.join(path.dirname(dtm), 'Output', dtm_name)

            #opened = set()

            #for root, dirs, files in os.walk(output_dir):
                #for f in files:
                    #if f.lower().endswith(".png"):
                        #full_path = os.path.join(root, f)
                        #if full_path not in opened:
                            #img = mpimg.imread(full_path)
                            #fig = plt.figure(figsize=(10, 10), dpi=150)
                            #plt.imshow(img, aspect='equal')
                            #plt.axis('off')
                           #plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
                            #plt.show()
                            #opened.add(full_path)
        
        self.CA_progress["value"] = self.CA_progress["maximum"]
        self.progress_label.config(text="Complete")

    
    def Run_CATools_UI(self):
        if not self.CA_ENC_var.get():
            print("NO ENC folder selected.")
            return
        
        if self.CA_input_mode.get() == "manual":
            if not hasattr(self, "dtms") or not self.dtms:
                print("No surface selected.")
                return
        
        else:
            self.dtms = []

            try:
                self.dtms = self.get_generated_surfaces()
            except Exception as e:
                print("Actual error:", repr(e))
                return
        self.Run_CATools()
    

    def get_generated_surfaces(self):

        #base = os.path.normpath(self.HDCS_D.get())
        #print("HDCS_D =", repr(base))
        #surface_dir = os.path.join(base, "Surfaces")

        base = self.HDCS_D.get()

        if base.endswith("Processed_Data"):
            surface_dir = os.path.join(base, "Surfaces")
        else:
            surface_dir = os.path.join(base, "Processed_Data", "Surfaces")

        print("Scanning from:", surface_dir)

        if not os.path.exists(surface_dir):
            raise Exception("Surface directory not found.")

        jd = self.JULIAN_D.get()
        year = self.Year.get()

        target_files = [f"{jd}_{year}.tif",
                        f"{jd}_{year}.tiff",
                        f"{jd}_{year}.bag"]
        
        surfaces = []

        for root, dirs, files in os.walk(surface_dir):
            for f in files:
                print("Checking file:", repr(f))

                if f in target_files:
                    full_path = os.path.join(root, f)
                    surfaces.append(full_path)
        
        if not surfaces:
            raise Exception("No surfaces found.")
        
        print("Found surfaces:")
        for s in surfaces:
            print(s)
        
        return surfaces
    

    def Toggle_CA_Input_Mode(self):
        if not hasattr(self, "CA_DTM_entry"):
            return
        
        mode = self.CA_input_mode.get()

        if mode == "auto":
            self.CA_DTM_entry.config(state="disabled")
            self.CA_DTM_button.config(state="disabled")

        else:
            self.CA_DTM_entry.config(state="normal")
            self.CA_DTM_button.config(state="normal")
    

    def Load_SOUACC(self):

        if self.SOUACC_F.get() == 1:

            self.SOUACC_frame = LabelFrame(frame10, text="SOUACC Calculation", foreground="blue")
            self.SOUACC_frame.grid(row=6, column=0, sticky=W)
        
            self.SOUACC_DIR = StringVar()
            self.SOUACC_text = Label(self.SOUACC_frame, text="Surface Folder")
            self.SOUACC_text.grid(row=0, column=0, sticky=W)
            self.SOUACC_entry = Entry(self.SOUACC_frame, width=38, textvariable=self.SOUACC_DIR)
            self.SOUACC_entry.grid(row=0, column=1, sticky=W)
            self.SOUACC_btn = Button(self.SOUACC_frame, text="...", height=0, command=self.select_souacc_dir)
            self.SOUACC_btn.grid(row=0, column=2, sticky=W, padx=2)
            
            self.SOUACC_convert = Button(self.SOUACC_frame, text="Convert Final Surfaces to Text Files", height=0, command=self.convert_csar_to_txt)
            self.SOUACC_convert.grid(row=1, column=0, sticky=W, padx=2)

            self.SOUACC_calc = Button(self.SOUACC_frame, text="Calculate SOUACC", height=0, command=self.calculate_souacc)
            self.SOUACC_calc.grid(row=2, column=0, sticky=W, padx=2)

            self.SOUACC_output = Text(self.SOUACC_frame, width=60, height=10)
            self.SOUACC_output.grid(row=3, column=0, columnspan=3)
        
        else:
            try:
                self.SOUACC_frame.grid_forget()
            except AttributeError:
                pass

    
    def select_souacc_dir(self):
        folder=filedialog.askdirectory(title="Select Surface Folder")
        self.SOUACC_DIR.set(folder)
    

    def convert_csar_to_txt(self):
        user_dir = self.SOUACC_DIR.get()
        file_list = listdir(user_dir)

        script_dir = os.path.dirname(__file__)
        bat_path = os.path.join(script_dir, "Coverage_to_ASCII.bat")

        with open(bat_path, "w") as ECTA:
            ECTA.write('@ECHO OFF\n')
            ECTA.write(f'call "C:/Program Files/CARIS/HIPS and SIPS/12.1/system/caris_env.bat"\n')
            ECTA.write('@ECHO Exporting Coverage to ASCII\n')

            for sf in file_list:
                if sf.lower().endswith('.csar'):
                    sf_path = os.path.join(user_dir, sf)
                    sf_name = os.path.splitext(sf)[0]
                    out_path = os.path.join(user_dir, sf_name + ".txt")
                    ECTA.write(
                        f'carisbatch --run ExportCoverageToASCII '
                        f'--include POSITION Lat 6 DD '
                        f'--include POSITION Lon 6 DD '
                        f'--include BAND Depth 2 m '
                        f'--include BAND Uncertainty 2 m '
                        f'"{sf_path}" "{out_path}"\n')
        S.check_call(bat_path, shell=True)


    def calculate_souacc(self):
        user_dir = self.SOUACC_DIR.get()
        files = listdir(user_dir)
        self.SOUACC_output.delete(1.0, END)

        for f in files:
            if f.endswith(".txt"):
                self.SOUACC_output.insert(END, f"{f.strip('.txt')}\n")
                ASCII_Out = pd.read_csv(f"{user_dir}/{f}", sep=' ', header=0, low_memory=False)
                ASCII_Out.columns = ["Lat", "Long", "Depth", "Depth TPU"]
                ASCII_Out["Weight"] = 1/ASCII_Out["Depth"]
                ASCII_Out["WTVU"] = ASCII_Out["Weight"] * ASCII_Out["Depth TPU"]
                SOUACC = str(round((ASCII_Out["WTVU"].sum())/(ASCII_Out["Weight"].sum()), 2)) + " m"
                self.SOUACC_output.insert(END, f"Calculated Sounding Accuracy is {SOUACC} metres.\n")
                self.SOUACC_output.insert(END, "---------------------------------\n")


    def Load_Daily_Reports(self):

        chdir(owd)

        if self.D_R.get() == 1:

            self.Daily = LabelFrame(frame9, text="Create Daily Excel Reports", foreground ="blue")
            self.Daily.grid(row=1, column=0, sticky=W)

            self.SVPDir = StringVar()
            self.SVP_Dir = Entry(self.Daily, width=38, textvariable=self.SVPDir)
            self.SVP_Dirtext = Label(self.Daily, text="Julian Day SVP Directory")
            self.SVP_Dirtext.grid(row=1, column=0, sticky=W)
            self.SVP_Dir.grid(row=1, column=1, sticky=W)
            self.ButtonSVP_Dir = Button(self.Daily, text="...", height=0,
                                        command=self.Search_SVP)
            self.ButtonSVP_Dir.grid(row=1, column=2, sticky=W, padx=2)
    
            self.REP_F = StringVar()
            self.REP_f = Entry(self.Daily, width=38, textvariable=self.REP_F)
            self.REP_ftext = Label(self.Daily, text="Daily Report Spreadsheet")
            self.REP_ftext.grid(row=2, column=0, sticky=W)
            self.REP_f.grid(row=2, column=1, sticky=W)
            self.ButtonREP_f = Button(self.Daily, text="...", height=0,
                                  command=self.Search_SpreadSheet_File)
            self.ButtonREP_f.grid(row=2, column=2, sticky=W, padx=2)

            self.WREP_F = StringVar()
            self.WREP_f = Entry(self.Daily, width=38, textvariable=self.WREP_F)
            self.WREP_ftext = Label(self.Daily, text="Weekly Report Spreadsheet")
            self.WREP_ftext.grid(row=3, column=0, sticky=W)
            self.WREP_f.grid(row=3, column=1, sticky=W)
            self.ButtonWREP_f = Button(self.Daily, text="...", height=0,
                                  command=self.Search_SpreadSheet_File2)
            self.ButtonWREP_f.grid(row=3, column=2, sticky=W, padx=2)

            self.IHO_ORDER2 = StringVar()
            iho_op2 = ['EXCLUSIVE',
                       'SPECIAL',
                       '1A',
                       '1B',
                       '2',
                       '3']
            self.IHO2_op = ttk.Combobox(self.Daily, values=iho_op2, width=10, textvariable=self.IHO_ORDER2)
            self.IHO2_text = Label(self.Daily, text="Choose IHO Order")
            self.IHO2_text.grid(row=4, column=0, sticky=W)
            self.IHO2_op.grid(row=4, column=1, sticky=W+E, padx=0)

            self.WeekNO = StringVar()
            self.Weekno = Entry(self.Daily, width=20, textvariable=self.WeekNO)
            self.Weeknotext = Label(self.Daily, text="Week #, JD#-JD#")
            self.Weeknotext.grid(row=5, column=0, sticky=W)
            self.Weekno.grid(row=5, column=1, sticky=W)

            self.TPUQC=IntVar()
            Radiobutton(self.Daily, text= "HIPS Points QC", variable=self.TPUQC, value=2).grid(row=6, column=0, sticky= W, padx=1)
            Radiobutton(self.Daily, text= "Surface QC", variable=self.TPUQC, value=1).grid(row=6, column=1, sticky= W, padx=1)

            self.Button_Rep = Button(self.Daily, text="Create Daily, Weekly Reports", height=0,
                               command=self.Run_Daily_Report)
            self.Button_Rep.grid(row=7, column=0, sticky=W, padx=2)

            Parameters = pd.read_csv('Parameters.txt', delimiter=',', header=None)
            #Line = (Parameters.iloc[14,0])
            Daily = Parameters.iloc[14,1]
            Weekly = Parameters.iloc[14,2]
            Weekno = Parameters.iloc[14,4]
            IHOOrder = Parameters.iloc[14,3]
            QC = Parameters.iloc[14,5]

            ##Setting defaults from Parameter file for SBET
            #self.LINE_F.set(Line)
            self.REP_F.set(Daily)
            self.WREP_F.set(Weekly)
            self.WeekNO.set(Weekno)
            self.IHO_ORDER2.set(IHOOrder)
            self.TPUQC.set(QC)

        else:
            try:
                ##Forget Options
                self.Daily.grid_forget()
            except AttributeError:
                pass

        #tip_LINE_F = ToolTip(self.LINE_f, str(self.LINE_F.get()))
        # tip_REP_F = ToolTip(self.REP_f, (self.REP_F.get()))


    def Load_BoundingPoly(self):

        if self.BP.get() == 1:
            self.BoundingP = LabelFrame(frame10, text="Create Bounding Polygon", foreground="blue")
            self.BoundingP.grid(row=5, column=0, sticky=W)

            if not hasattr(self, "VALSRC_F"):
                self.VALSRC_F = StringVar()
            self.VALSRC_f = Entry(self.BoundingP, width=38, textvariable=self.VALSRC_F)
            self.VALSRC_text = Label(self.BoundingP, text="Surface Folder")
            self.VALSRC_text.grid(row=1, column=0, sticky=W)
            self.VALSRC_f.grid(row=1, column=1, sticky=W)
            self.ButtonSF = Button(self.BoundingP, text="...", height=0,
                                      command=self.Search_VALSRC_Folder)
            self.ButtonSF.grid(row=1, column=2, sticky=W, padx=2)

            self.Button_Final = Button(self.BoundingP, text="Create Bounding Polygons", height=0,
                               command=self.Create_BoundingPoly)
            self.Button_Final.grid(row=20, column=0, sticky=W, padx=2)

        else:
            try:
                ##Forget Options for Finalization
                self.BoundingP.grid_forget()
            except AttributeError:
                pass
        

    def Load_Finalization_Submission(self):

        if self.Finalize.get() == 1:
            self.Finalization = LabelFrame(frame10, text="Finalize Surfaces", foreground="blue")
            self.Finalization.grid(row=2, column=0, sticky=W)

            if not hasattr(self, "VALSRC_F"):
                self.VALSRC_F = StringVar()

            self.VALSRC_f = Entry(self.Finalization, width=38, textvariable=self.VALSRC_F)
            self.VALSRC_text = Label(self.Finalization, text="Surface Folder")
            self.VALSRC_text.grid(row=0, column=0, sticky=W)
            self.VALSRC_f.grid(row=0, column=1, sticky=W)
            self.ButtonSF = Button(self.Finalization, text="...", height=0,
                                      command=self.Search_VALSRC_Folder)
            self.ButtonSF.grid(row=0, column=2, sticky=W, padx=2)

            self.Button_Final = Button(self.Finalization, text="Finalize Surfaces", height=0,
                               command=self.FinalizeQC)
            self.Button_Final.grid(row=1, column=0, columnspan=3, pady=5)

        else:
            try:
                ##Forget Options for Finalization
                self.Finalization.grid_forget()
            except AttributeError:
                pass


    def Load_ATL_SUB_ISO(self):

        if self.HDC_F.get() == 1:
            self.Dir_Form = LabelFrame(frame10, text="Create ATL ISO 1001 07 AF01", foreground="blue")
            self.Dir_Form.grid(row=3, column=0, sticky=W)

            self.SIG = StringVar()

            self.Sig = Entry(self.Dir_Form, width=25, textvariable=self.SIG)
            self.Sig_text = Label(self.Dir_Form, text="Full Name")
            self.Sig_text.grid(row=1, column=0, sticky=W)
            self.Sig.grid(row=1, column=1, sticky=W)

            self.SUB_D = StringVar()
            self.SUB_d = Entry(self.Dir_Form, width=38, textvariable=self.SUB_D)
            self.SUB_dtext = Label(self.Dir_Form, text="Submission Directory")
            self.SUB_dtext.grid(row=2, column=0, sticky=W)
            self.SUB_d.grid(row=2, column=1, sticky=W)

            self.Buttonsub = Button(self.Dir_Form, text="...", height=0,
                                  command=self.Search_Sub_dir_file)
            self.Buttonsub.grid(row=2, column=2, sticky=W, padx=2)

            self.ButtonC = Button(self.Dir_Form, text="Fill HDC ISO Sub Form", height=0,
                                  command=self.ISO_1001_07_A_F01)
            self.ButtonC.grid(row=3, column=0, sticky=W, padx=2)

        else:
            try:
                ##Forget Options for ISO 1001 07 A F01 Form
                self.Dir_Form.grid_forget()
            except AttributeError:
                pass


    def Load_FlierFinder(self):

        if self.RUN_FF.get() == 1:

            self.FlierFinder = LabelFrame(frame9, text="QCTools Flier Finder", foreground="blue")
            self.FlierFinder.grid(row=4, column=0, sticky=W)

            self.DTM_DIR = StringVar()
            self.DTM_dir = Entry(self.FlierFinder, width=38, textvariable=self.DTM_DIR)
            self.DTM_dir_text = Label(self.FlierFinder, text="Surface Folder")
            self.DTM_dir_text.grid(row=2, column=0, sticky=W)
            self.DTM_dir.grid(row=2, column=1, sticky=W)
            self.ButtonSF = Button(self.FlierFinder, text="...", height=0,
                                      command=self.Search_DTMFolder)
            self.ButtonSF.grid(row=2, column=2, sticky=W, padx=2)

            self.FHEIGHT = StringVar()
            heights = ['AUTO',
                        '1','2','3','4','5','6','7','8','9','10']
            self.FHEIGHT_op = ttk.Combobox(self.FlierFinder, values=heights, textvariable=self.FHEIGHT)
            self.FHEIGHT_text = Label(self.FlierFinder, text="Flier Height (m)")
            self.FHEIGHT_text.grid(row=1, column=0, sticky=W)
            self.FHEIGHT_op.grid(row=1, column=1, sticky=W+E, padx=0)

            self.ButtonFF = Button(self.FlierFinder, text="Run Flier Finder", height=0,
                                  command=self.Find_Fliers)
            self.ButtonFF.grid(row=3, column=0, sticky=W, padx=2)

        else:
            try:
                ##Forget Options for QCTools Flier Finder
                self.FlierFinder.grid_forget()
            except AttributeError:
                pass

        
    def FinalizeQC(self):

        V_F = self.VALSRC_F.get()

        if not V_F or not path.exists(V_F):
            print("Invalid VALSRC folder.")
            return

        self.Finalized_Folder = ('Finalized_Surfaces')

        chdir(V_F)

        if not path.exists(self.Finalized_Folder):
            mkdir(self.Finalized_Folder)

        chdir(owd)

        self.Finalize_Surfaces()
 

    def Create_BoundingPoly(self):

        V_F = self.VALSRC_F.get()

        if not V_F or not path.exists(V_F):
            print("Invalid surface folder.")
            return
        
        print("\n=== START BOUNDING POLYGON CREATION ===\n")
        
        for f in listdir(V_F):
            if f.endswith(".csar"):
                full_path = path.join(V_F, f)
                print("Processing", full_path)

                try:
                    params = BP.compute_parameters(full_path)
                    print("Params:", params)

                    poly = BP.create_bp(full_path, params[0], params[1])
                    print("Poly:", poly)
                    
                    print(f"Success: {f}")
                
                except Exception as e:
                    print(f"Failed: {f} | Error: {e}")
        
        print("\n=== BOUNDING POLYGON COMPLETE ===\n")

  
    def Vectorize_Raster2(self, surface, Out):

        Surface = surface.split('.')
        
        hob = (Out + '/' + Surface[0] + '.hob')
        FilePrefix = Surface[0]
        shp = (Out + '/' + Surface[0] + '_cvrage(A).shp')

        with open("Vectorize_Raster.bat", "w") as Area_C:
            Area_C.write('@ECHO OFF' + '\n')
            Area_C.write('@ECHO Vectorizing Surface' + '\n')
            Area_C.write('cd '+ Caris + '\n')
            Area_C.write('carisbatch --run  VectorizeRaster --input-band Depth --feature-catalogue "Bathy DataBASE"' +
                         ' --polygon-feature cvrage --mode COVERAGE ' + Out + '/' + surface + ' ' + hob + '\n')
            Area_C.write('carisbatch --run ExportFeaturesToShapefile --feature-catalogue "Bathy DataBASE"' +
                         ' --file-prefix ' + FilePrefix + ' ' + hob + ' ' + Out)

        p = S.check_call("Vectorize_Raster.bat", stdin=None, stdout=None, stderr=None, shell=False)


    def Finalize_Surfaces(self):

        V_F = self.VALSRC_F.get()
        list_VF = listdir(V_F)


        with open("Finalized.bat", 'w') as Final:
            Final.write('@ECHO OFF' + '\n')
            Final.write('@ECHO Finalizing Surfaces' + '\n')
            Final.write('cd '+ Caris + '\n')

            for VALSRCno in list_VF:
                if VALSRCno.lower().endswith(".csar"):
                    name = os.path.splitext(VALSRCno)[0]
                    Final.write('carisbatch --run FinalizeRaster --include-band  Depth --include-band Uncertainty '  +
                                '--apply-designated --uncertainty-source UNCERT ' +
                                V_F +  '/' + name + '.csar ' +
                                V_F + '/' + self.Finalized_Folder + '/' + name + '.csar' +'\n')

        p = S.check_call("Finalized.bat", stdin=None, stdout=None, stderr=None, shell=False)


    def ExporttoACSII(self):

        PH = self.split_Project_Name()
        Project_N = PH[0]
        HIPSFILE = PH[1]

        HDCS_Folder = self.HDCS_D.get()
        crs = self.CRS_O.get() ## Coordinate Ref System
        CRS = crs.partition(": ")[2]
        Vessel_F = self.VESSEL_N.get()
        Vessel = path.basename(Vessel_F)
        Vessel = path.splitext(Vessel)[0]
        Dir_Grid = self.GRID_DIR.get()
        Year = (self.Year.get())
        JD = self.JULIAN_D.get()
        Out = self.OUT_F.get()
        TPUQCFolder = str('TPUQC')
        HTA_Out = (Out + '/' + str(JD) + '/' + TPUQCFolder)
        chdir(Out + '/' + str(JD))
        if path.exists(TPUQCFolder):
            pass
        else:
            mkdir(TPUQCFolder)

        if self.TPUQC.get()==1:
            chdir(HTA_Out)
            if path.exists('Coverage'):
                pass
            else:
                mkdir('Coverage')
            chdir(owd)
            with open("Coverage_to_ASCII.bat", "w") as ECTA:
                ECTA.write('@ECHO OFF' + '\n')
                ECTA.write('cd '+ Caris + '\n')
                ECTA.write('@ECHO Exporting Coverage to ACSII' + '\n')
                ECTA.write('carisbatch --run ExportCoverageToASCII' +
                           ' --include POSITION Lat 6 DD' +
                           ' --include POSITION Lon 6 DD' +
                           ' --include BAND Depth 2 m' +
                           ' --include BAND Uncertainty 2 m ' +
                           Dir_Grid + '/' + JD + '_' + Year + '.csar ' +
                           ' ' + HTA_Out + '/Coverage/' + 'Coverage_' + JD + '_' + Year + '.txt')
            p = S.check_call("Coverage_to_ASCII.bat", stdin=None, stdout=None, stderr=None, shell=False)

        elif self.TPUQC.get()==2:
            chdir(HTA_Out)
            if path.exists('HIPS'):
                pass
            else:
                mkdir('HIPS')
            chdir(owd)

            with open("Hip_to_ASCII.bat", "w") as HTA:
                HTA.write('@ECHO OFF' + '\n')
                HTA.write('cd '+ Caris + '\n')
                HTA.write('@ECHO Exporting HIPS to ACSII' + '\n')
                HTA.write('carisbatch --run ExportHIPS --output-format ASCII --sample 0.5m MIN ALLDATA' +
                            ' --delimiter "," --overwrite --include-flag ACCEPTED --output-crs ' + CRS +
                            ' --include-flag EXAMINED --include-flag OUTSTANDING --include-header --coordinate-format LLDG_DD' +
                            ' --include-attribute DEPTH_PRO --include-attribute POSITION_TPU' +
                            ' --include-attribute Depth_TPU --coordinate-precision 7 --single-file Sampled_HIPS_Data_' + str(JD) + '.txt' +
                            r' file:///' + HDCS_Folder + '/'  + HIPSFILE + '/' + HIPSFILE + '.hips?Vessel=' + Vessel +
                            ';Day=' + str(Year) + '-' + str(JD) + ' ' + HTA_Out + '/HIPS' + '\n')

            p = S.check_call("Hip_to_ASCII.bat", stdin=None, stdout=None, stderr=None, shell=False)


    def Vectorize_Raster(self):

        Dir_Grid = self.GRID_DIR.get()
        Output = self.OUT_F.get()
        Year = (self.Year.get())
        JD = self.JULIAN_D.get()
        chdir(Output + '/' + JD +'/TPUQC')
        if path.exists('Polygon_' + str(JD)):
            pass
        else:
            mkdir('Polygon_' + str(JD))
        chdir(owd)

        raster = (Dir_Grid + '/' + JD + '_' + Year + '.csar')
        hob = (Output + '/' + JD +'/TPUQC/' + 'Polygon_' + str(JD) + '/' + JD + '_' + Year + '.hob')
        shp = (Output + '/' + JD +'/TPUQC/' + 'Polygon_' + str(JD) + '/' + JD + '_' + Year + '.shp')

        with open("Vectorize_Raster.bat", "w") as Area_C:
            Area_C.write('@ECHO OFF' + '\n')
            Area_C.write('@ECHO Vectorizing Surface' + '\n')
            Area_C.write('cd '+ Caris + '\n')
            Area_C.write('carisbatch --run  VectorizeRaster --input-band Depth --feature-catalogue "Bathy DataBASE"' +
                         ' --polygon-feature cvrage --mode COVERAGE ' + raster + ' ' + hob + '\n')
            Area_C.write('@ECHO Adding Area Geometry' + '\n')
            Area_C.write('carisbatch --run AddGeometryAttributes --feature-catalogue "Bathy DataBASE"' +
                         ' --area ' + hob + ' ' + shp + '\n')

        p = S.check_call("Vectorize_Raster.bat", stdin=None, stdout=None, stderr=None, shell=False)


    def Run_Daily_Report(self):

        JD = self.JULIAN_D.get()
        Year = self.YEAR.get()

        JDS = str(self.GRID_DIR.get() + '/' + str(JD) + '_' + str(Year) +'.csar')

        chdir(str(self.OUT_F.get()))
        if path.exists(str(JD)):
            pass
        else:
            mkdir(str(JD)) ## Create a Julian Day dump folder for all Processing logs and CHSython Output

        chdir(owd)
        if path.isfile(JDS):
            pass
        else:
            self.Create_Addto_Hips_Grid()
            
        self.ExporttoACSII()
        self.Vectorize_Raster()
        self.Plotting()


    def Plotting(self):

        Dir_Grid = self.GRID_DIR.get()
        Year = (self.Year.get())
        JD = self.JULIAN_D.get()
        Out = self.OUT_F.get()
        Report_F = self.REP_F.get()
        Weekly_Report = self.WREP_F.get()
        Name = self.WeekNO.get()
        order = self.IHO_ORDER2.get()
        TPUQCFolder = str('TPUQC')

        t_95_1d = 1.96
        t_95_2d = 2.45

        IHO_orders = [order]

        if self.TPUQC.get()==1:
            ASCII_Out = pd.read_csv(Out + '/' + JD + '/' + TPUQCFolder + '/Coverage/' + 'Coverage_' + JD + '_' + Year + '.txt', sep=' ', header=0, low_memory=False)
            ASCII_Out.columns = ["Lat", "Long", "Depth", "Depth TPU"]

            List_TVU = []
            for orders in IHO_orders:
                TVU_D = []
                for Depth in ASCII_Out['Depth']:
                    TPU2 = TPU(orders, Depth)
                    TVU_D.append(TPU2[0])
                ASCII_Out['Allowable TVU'] = TVU_D
                ASCII_Out['Within Allowable TVU'] = np.where(ASCII_Out['Depth TPU'] <= ASCII_Out['Allowable TVU'],
                                                   'yes', 'no')
                P_W_A_TVU = round(((len(ASCII_Out[ASCII_Out['Within Allowable TVU'] == 'yes'])/len(ASCII_Out)))*100,2)

                Depth_mean = round(ASCII_Out['Depth'].mean(),3)

                Depth_TPU_max = round(ASCII_Out['Depth TPU'].max(),3)
                Depth_TPU_min = round(ASCII_Out['Depth TPU'].min(),3)
                Depth_TPU_mean = round(ASCII_Out['Depth TPU'].mean(),3)
                Depth_TPU_std = round(ASCII_Out['Depth TPU'].std(),3)
                Depth_95_p = round((Depth_TPU_mean + t_95_1d*Depth_TPU_std),3)
                Depth_95_n = round((Depth_TPU_mean - t_95_1d*Depth_TPU_std),3)

                TPU_v = TPU(orders, Depth_mean)
                fig, ax = plt.subplots(nrows=2)
                D_TPU = list(ASCII_Out.loc[:,'Depth TPU'])
                ax[0].hist(D_TPU, weights=np.ones(len(D_TPU)) / len(D_TPU), alpha=0.5)
                ax[0].axvline(Depth_TPU_max, 0, c='r', label = "MAX = " + str(Depth_TPU_max) + 'm')
                ax[0].axvline(Depth_TPU_mean, 0, c='g', label = "MEAN = " + str(Depth_TPU_mean) + 'm')
                ax[0].axvline(Depth_TPU_min, 0, c='c', label = "MIN = " + str(Depth_TPU_min) + 'm')
                ax[0].axvline(Depth_95_p, 0, c='m', label = "95% Level = " + str(Depth_95_p) + 'm')
                ax[0].axvline(TPU_v[0], 0, c='k', label = "CHS/IHO = " + str(TPU_v[0]) + 'm')
                ax[0].legend(loc='upper right')
                ax[0].set_title('Vertical Accuracy (Ave Depth ' + str(Depth_mean) + ' m)' + '(Order = ' + str(orders) + ')\n')
                ax[0].set_xlabel('Depth Accuracy (m)')
                ax[0].set_ylabel('Percentage (%)')

                maxd = round(ASCII_Out['Depth'].max(),0)+5
                Depths = np.arange(0,maxd,1)
                Contours = [0,2,5,10,15,20,30,50,100]
                ATPU=[]
                for D in Depths:
                    ATPU.append(TPU(orders,D)[0])


                colors = {'yes': 'green', 'no':'red'}
                ax[1].scatter(ASCII_Out['Depth'],ASCII_Out['Depth TPU'],c=ASCII_Out['Within Allowable TVU'].map(colors))
                ax[1].plot(Depths, ATPU)
                ax[1].set_title('Vertical Accuracy Scatterplot) ' + '(Order = ' + str(orders) + ')\n Red - Outside Allowable Green - Within Allowable(' + str(P_W_A_TVU) + '%)')
                ax[1].set_xlabel('Depth (m)')
                ax[1].set_ylabel('Depth Accuracy (m)')
                plt.tight_layout()
                plt.savefig(str(Out) + '/' + str(JD) + '/' + TPUQCFolder  + '/Coverage/' + orders + '_Accuracy.png', dpi=200)


        elif self.TPUQC.get()==2:
            ASCII_Files = (Out + '/' + JD + '/' + TPUQCFolder + '/HIPS')
            HIPS_Files = listdir(ASCII_Files)
            Import = [pd.read_table(ASCII_Files + '/' + file, delimiter=',') for file in HIPS_Files]
            ASCII_Out = pd.concat(Import)
            ASCII_Out.columns = ['Lat', 'Long', 'Depth', 'Depth TPU', 'Position TPU']

            THU_D = []
            TVU_D = []
            for Depth in ASCII_Out['Depth']:
                TPU2 = TPU(order, Depth)
                TVU_D.append(TPU2[0])
                THU_D.append(TPU2[1])
            ASCII_Out['Allowable TVU'] = TVU_D
            ASCII_Out['Allowable THU'] = THU_D
            ASCII_Out['Within Allowable THU'] = np.where(ASCII_Out['Position TPU'] <= ASCII_Out['Allowable THU'],
                                               'yes', 'no')
            P_W_A_THU = round(((len(ASCII_Out[ASCII_Out['Within Allowable THU'] == 'yes'])/len(ASCII_Out)))*100,2)

            ASCII_Out['Within Allowable TVU'] = np.where(ASCII_Out['Depth TPU'] <= ASCII_Out['Allowable TVU'],
                                               'yes', 'no')

            P_W_A_TVU = round(((len(ASCII_Out[ASCII_Out['Within Allowable TVU'] == 'yes'])/len(ASCII_Out)))*100,2)

            Depth_mean = round(ASCII_Out['Depth'].mean(),3)

            POS_TPU_max = round(ASCII_Out['Position TPU'].max(),3)
            POS_TPU_min = round(ASCII_Out['Position TPU'].min(),3)
            POS_TPU_mean = round(ASCII_Out['Position TPU'].mean(),3)
            POS_TPU_std = round(ASCII_Out['Position TPU'].std(),3)
            POS_95_p = round((POS_TPU_mean + t_95_2d*POS_TPU_std),3)
            POS_95_n = round((POS_TPU_mean - t_95_2d*POS_TPU_std),3)

            Depth_TPU_max = round(ASCII_Out['Depth TPU'].max(),3)
            Depth_TPU_min = round(ASCII_Out['Depth TPU'].min(),3)
            Depth_TPU_mean = round(ASCII_Out['Depth TPU'].mean(),3)
            Depth_TPU_std = round(ASCII_Out['Depth TPU'].std(),3)
            Depth_95_p = round((Depth_TPU_mean + t_95_1d*Depth_TPU_std),3)
            Depth_95_n = round((Depth_TPU_mean - t_95_1d*Depth_TPU_std),3)

            TPU_v = TPU(order, Depth_mean)

            fig, ax = plt.subplots(nrows=2)
            D_TPU = list(ASCII_Out.loc[:,'Depth TPU'])
            ax[0].hist(D_TPU, weights=np.ones(len(D_TPU)) / len(D_TPU), alpha=0.5)
            ax[0].axvline(Depth_TPU_max, 0, c='r', label = "MAX = " + str(Depth_TPU_max) + 'm')
            ax[0].axvline(Depth_TPU_mean, 0, c='g', label = "MEAN = " + str(Depth_TPU_mean) + 'm')
            ax[0].axvline(Depth_TPU_min, 0, c='c', label = "MIN = " + str(Depth_TPU_min) + 'm')
            ax[0].axvline(Depth_95_p, 0, c='m', label = "95% Level = " + str(Depth_95_p) + 'm')
            ax[0].axvline(TPU_v[0], 0, c='k', label = "CHS/IHO = " + str(TPU_v[0]) + 'm')
            ax[0].legend(loc='upper right')
            ax[0].set_title('Vertical Accuracy (Ave Depth ' + str(Depth_mean) + ' m)' + '(Order = ' + str(order) + ')\n')
            ax[0].set_xlabel('Depth Accuracy (m)')
            ax[0].set_ylabel('Percentage (%)')

            POS_TPU = list(ASCII_Out.loc[:,'Position TPU'])
            ax[1].hist(POS_TPU, weights=np.ones(len(POS_TPU)) / len(POS_TPU), alpha=0.5)
            ax[1].axvline(POS_TPU_max, 0, c='r', label = "MAX = " + str(POS_TPU_max) + 'm')
            ax[1].axvline(POS_TPU_mean, 0, c='g', label = "MEAN = " + str(POS_TPU_mean) + 'm')
            ax[1].axvline(POS_TPU_min, 0, c='c', label = "MIN = " + str(POS_TPU_min) + 'm')
            ax[1].axvline(POS_95_p, 0, c='m', label = "95% Level = " + str(POS_95_p) + 'm')
            ax[1].axvline(TPU_v[1], 0, c='k', label = "CHS/IHO = " + str(TPU_v[1]) + 'm')
            ax[1].legend(loc='upper right')
            ax[1].set_title('Horizontal Accuracy' + '(Order = ' + str(order) + ')')
            ax[1].set_xlabel('Positional Accuracy (m)')
            ax[1].set_ylabel('Percentage (%)')
            plt.tight_layout()
            plt.savefig(str(Out) + '/' + JD + '/' + TPUQCFolder + '/HIPS/' + order + '_Accuracy.png', dpi=200)

        SVPCount = self.SVP_Count()
        self.Line_Report()
        Line_Report = pd.read_csv(Out + '/' + JD + '/LineReport_' + JD + '.csv', delimiter=',')
        line_count = len(Line_Report)
        Total_Survey_Time = self.Total_Survey_Time
        Total_Survey_Length = self.Total_Survey_Length

        shp_file = (Out + '/' + JD +'/TPUQC/' + 'Polygon_' + str(JD) + '/' + JD + '_' + Year + 'cvrage(A).shp')
        Area_shp = shapefile.Reader(shp_file)
        shp_records = Area_shp.records()
        l_Areas = len(shp_records)
        Areas = []
        c = 0
        while c < l_Areas:
            rec = Area_shp.record(c)
            Areas.append(rec['AREA'])
            c = c + 1
        Total_Survey_Area = round(sum(Areas)/(1000*1000),3)

        myworkbook2 = openpyxl.load_workbook(Report_F)

        if "Sheet1" in myworkbook2.sheetnames and len(myworkbook2.sheetnames) == 1:
            std = myworkbook2["Sheet1"]
            myworkbook2.remove(std)

        if str(JD) in myworkbook2.sheetnames:
            worksheet = myworkbook2[str(JD)]
            worksheet.delete_rows(1, worksheet.max_row)
        else:
            worksheet = myworkbook2.create_sheet(title=str(JD))
        #cws = myworkbook2.create_sheet(JD)
        #worksheet = myworkbook2.get_sheet_by_name(JD)

        from openpyxl.utils.dataframe import dataframe_to_rows
        rows = dataframe_to_rows(Line_Report)
        for r_idx, row in enumerate(rows, 1):
            for c_idx, value in enumerate(row, 1):
                 worksheet.cell(row=r_idx, column=c_idx, value=value)

        IHO_orders = ['EXCLUSIVE', 'SPECIAL', '1A', '1B', '2', '3']
        worksheet['A'+ str(line_count + 5)] = ('Summary')
        worksheet.merge_cells('A'+ str(line_count + 5) + ':B' + str(line_count + 5))
        worksheet['A'+ str(line_count + 6)] = ('Total Survey Time (hh:mm:ss.sss)')
        worksheet['A'+ str(line_count + 7)] = ('Total Length (km)')
        worksheet['A'+ str(line_count + 8)] = ('Total Area sqkm')
        worksheet['A'+ str(line_count + 9)] = ('Total Sound Velocity Casts')
        worksheet['A'+ str(line_count + 10)] = ('% TVU Values within ' + str(order))
        worksheet['A'+ str(line_count + 11)] = ('% THU Values within ' + str(order))
        worksheet['B'+ str(line_count + 6)] = (Total_Survey_Time)
        worksheet['B'+ str(line_count + 7)] = (Total_Survey_Length)
        worksheet['B'+ str(line_count + 8)] = (Total_Survey_Area)
        worksheet['B'+ str(line_count + 9)] = (SVPCount)
        worksheet['B'+ str(line_count + 10)] = str(P_W_A_TVU)

        if self.TPUQC.get()==2:
            worksheet['B'+ str(line_count + 11)] = str(P_W_A_THU)
        myworkbook2.save(Report_F)

        wb = openpyxl.load_workbook(Report_F)
        #ws = wb.get_sheet_by_name(JD)
        ws = wb[str(JD)]
        if self.TPUQC.get()==1:
            img = openpyxl.drawing.image.Image(str(Out) + '/' + str(JD) + '/' + 'TPUQC' +  '/Coverage/' + order + '_Accuracy.png')
        elif self.TPUQC.get()==2:
            img = openpyxl.drawing.image.Image(str(Out) + '/' + str(JD) + '/' + 'TPUQC' + '/HIPS/' + order + '_Accuracy.png')
        ws.add_image(img, 'A' + str(line_count + 14))
        wb.save(Report_F)
        startfile(Report_F)

        Weekly = openpyxl.load_workbook(Weekly_Report)
        if Name in Weekly.sheetnames:
            worksheet = Weekly[Name]
        else:
            worksheet = Weekly.create_sheet(Name)
        #worksheet = Weekly.get_sheet_by_name(Name)
        Space = worksheet.max_row #len(worksheet['A']) + 1
        
        worksheet['A'+ str(1 + Space)] = ('Summary JD' + str(JD))
        worksheet.merge_cells('A'+ str(1 + Space) + ':B' + str(1 + Space))
        worksheet['A'+ str(2 + Space)] = ('Total Survey Time (hh:mm:ss.sss)')
        worksheet['A'+ str(3 + Space)] = ('Total Length (km)')
        worksheet['A'+ str(4 + Space)] = ('Total Area sqkm')
        worksheet['A'+ str(5 + Space)] = ('Total Sound Velocity Casts')
        worksheet['A'+ str(6 + Space)] = ('% TVU Values within ' + str(order))
        worksheet['A'+ str(7 + Space)] = ('% THU Values within ' + str(order))
        worksheet['B'+ str(2 + Space)] = (Total_Survey_Time)
        worksheet['B'+ str(3 + Space)] = (Total_Survey_Length)
        worksheet['B'+ str(4 + Space)] = (Total_Survey_Area)
        worksheet['B'+ str(5 + Space)] = (SVPCount)
        worksheet['B'+ str(6 + Space)] = str(P_W_A_TVU)
        if self.TPUQC.get()==2:
            worksheet['B'+ str(7 + Space)] = str(P_W_A_THU)
        Weekly.save(Weekly_Report)
        startfile(Weekly_Report)


    def SVP_Count(self):
        """"Count the total number of SVP cast coducted each Julian Day"""

        SVP_dir = self.SVPDir.get()
        SVPfiles = listdir(SVP_dir)

        svpcounter = 0
        for file in SVPfiles:
            if file.endswith((".asvp",".svp")):
                svpcounter = svpcounter + 1
        return(svpcounter)


    def Line_Report(self):

        HDCS_Folder = self.HDCS_D.get()
        Vessel_F = self.VESSEL_N.get()
        Vessel = path.basename(Vessel_F)
        Vessel = path.splitext(Vessel)[0]
        Year = (self.Year.get())
        JD = self.JULIAN_D.get()
        Out = self.OUT_F.get()
        PH = self.split_Project_Name()
        Project_N = PH[0]
        HIPSFILE = PH[1]

        hips = HIPSProject(HDCS_Folder + '/' + HIPSFILE + '/' + HIPSFILE + '.hips')
        lines = hips.get_lines()
        tot = 0

        try:
            Vessels = list(hips.get_vessels())
        except Exception:
            Vessels = []
    
        vessel_n = []

        for v in Vessels:
            if isinstance(v, (list, tuple)) and len(v) > 1:
                vessel_n.append(os.path.basename(v[1]))

        LR = pd.DataFrame()
        for line in lines:
            dict_new = line.attributes
            new_row = pd.DataFrame([dict_new])
            LR = pd.concat([LR, new_row], ignore_index=True)

        LR['Vessel Id'] = pd.to_numeric(LR['Vessel Id'], errors='coerce')
        LR['Vessel Name'] = None

        i2 = 1
        while i2 <= len(vessel_n):
            LR.loc[LR['Vessel Id'] == float(i2), 'Vessel Name'] = vessel_n[i2-1]
            i2 += 1
        LR['Vessel'] = Vessel
        LR['Day'] = (Year + '-' + JD)

        filtered = LR[LR['Raw Data Path'].astype(str).str.contains('JD' + JD, na=False)]

        if not filtered.empty:
            print(f"JD filter matched {len(filtered)} rows")
            LR = filtered
        else:
            print("JD filter returned no rows. Using all lines.")

        #LR = LR[LR['Raw Data Path'].str.contains(('.+' +'JD' +  JD + '.+'), regex=True)]

        LR['Georeferenced'].mask(LR['Georeferenced'] == 1, 'Yes', inplace=True)
        LR['Georeferenced'].mask(LR['Raw Range'] == 'None', 'No', inplace=True)
        LR['Georeferenced'].mask(LR['Georeferenced'] == 0, 'No', inplace=True)
        
        LR['Tpu Computed'].mask(LR['Tpu Computed'] == 1, 'Yes', inplace=True)
        LR['Tpu Computed'].mask(LR['Tpu Computed'] == 'None', 'No', inplace=True)
        LR['Tpu Computed'].mask(LR['Tpu Computed'] == 0, 'No', inplace=True)

        LR['Gps Vertical Reference Available'].mask(LR['Gps Vertical Reference Available'] == 1, 'Yes', inplace=True)
        LR['Gps Vertical Reference Available'].mask(LR['Gps Vertical Reference Available'] == 'None', 'No', inplace=True)
        LR['Gps Vertical Reference Available'].mask(LR['Gps Vertical Reference Available'] == 0, 'No', inplace=True)

        LR['Tide Available'].mask((LR['Tide Available']) == 0, 'No', inplace=True)
        LR['Tide Available'].mask(LR['Tide Available'] == 'None', 'No', inplace=True)
        LR['Tide Available'].mask(LR['Tide Available'] == 1, 'Yes', inplace=True)

        LR['Svp Corrected'].mask((LR['Svp Corrected']) == 0, 'No', inplace=True)
        LR['Svp Corrected'].mask(LR['Svp Corrected'] == 'None', 'No', inplace=True)
        LR['Svp Corrected'].mask(LR['Svp Corrected'] == 1, 'Yes', inplace=True)

        LR['Outdated'].mask((LR['Outdated']) == 0, 'No', inplace=True)
        LR['Outdated'].mask(LR['Outdated'] == 'None', 'No', inplace=True)
        LR['Outdated'].mask(LR['Outdated'] == 1, 'Yes', inplace=True)

        LR['Raw Range'].mask((LR['Raw Range']) == 0, 'No', inplace=True)
        LR['Raw Range'].mask(LR['Raw Range'] == 'None', 'No', inplace=True)
        LR['Raw Range'].mask(LR['Raw Range'] == 1, 'Yes', inplace=True)

        LR['Data Confidence Computed'].mask((LR['Data Confidence Computed']) == 0, 'No', inplace=True)
        LR['Data Confidence Computed'].mask(LR['Data Confidence Computed'] == 'None', 'No', inplace=True)
        LR['Data Confidence Computed'].mask(LR['Data Confidence Computed'] == 1, 'Yes', inplace=True)

        LR['Del Dft Loaded'].mask((LR['Del Dft Loaded']) == 0, 'No', inplace=True)
        LR['Del Dft Loaded'].mask(LR['Del Dft Loaded'] == 'None', 'No', inplace=True)
        LR['Del Dft Loaded'].mask(LR['Del Dft Loaded'] == 1, 'Yes', inplace=True)
       
        #LR['Vertical Reference'].mask(LR['Vertical Reference'] == 0, 'NONE', inplace=True)
        #LR['Vertical Reference'].mask(LR['Vertical Reference'] == 1, 'TIDE', inplace=True)
        #LR['Vertical Reference'].mask(LR['Vertical Reference'] == 2, 'GPS', inplace=True)

        LR['Vertical Reference'] = LR['Vertical Reference'].replace({0: 'NONE', 1: 'TIDE', 2: 'GPS', '0': 'NONE', '1': 'TIDE', '2': 'GPS'})

        
        LR['Total Time'] = (LR['Max Time'] - LR['Min Time'])/1000
        self.Total_Survey_Time = time.strftime("%H:%M:%S", time.gmtime(LR['Total Time'].sum()))


        LR['Max Time'] = LR['Max Time'].apply(lambda x: hips.convert_utc_time(x))
        LR['Min Time'] = LR['Min Time'].apply(lambda x: hips.convert_utc_time(x))
       
        LR['Total Time'] = LR['Total Time'].apply(lambda x: time.strftime("%H:%M:%S", time.gmtime(x)))


        LR = LR.drop( columns=['Concrete Object Id', 'Max Nav Time', 'Min Nav Time',
                               'Mod Time', 'Nav Examined', 'Nav Status', 'Nav Timestamps',
                               'Observed Depths Status', 'Procssed Depths Status',
                               'Resolution', 'Sources', 'Line Path', 'Towfish Nav Status',
                               'Tool Type'])

        LR = LR.sort_values(['Line Name'])
        print(LR)

        LR_out = LR.copy()

        yes_no_cols = ['Georeferenced',
                        'Outdated',
                        'Tide Available',
                        'Del Dft Loaded',
                        'Svp Corrected',
                        'Tpu Computed',
                        'Gps Vertical Reference Available',
                        'Raw Range',
                        'Data Confidence Computed',
                        'Multiple Frequency']
        
        for col in yes_no_cols:
            if col in LR_out.columns:
                LR_out[col] = LR_out[col].replace({1: 'Yes', 0: 'No', '1': 'Yes', '0': 'No'})
    
        LR_out.to_csv(Out + '/' + JD + '/LineReport_' + JD + '.csv')

        self.Total_Survey_Length = (LR['Length'].sum())/1000


    def Create_Project_Dir(self):

        self.Search_dir()
        PH = self.split_Project_Name()
        CP = PH[0]
        HIPSFILE = PH[1]
        PL = self.PF
        chdir(PL)
        Projectname = CP
        mkdir(Projectname)

        P_F = path.join(PL,CP)
        chdir(path.join(PL,CP))
        PF_2021 = ['Processed_Data', 'BaseStation', 'MetaData', 'Inertial', 'Raw', 'SVP', 'Tide', 'VALSRC']
        for folder in PF_2021:
            full_path = P_F
            if path.exists(folder):
                return
            else:
                mkdir(folder)

        Pro_F = path.join(path.join(PL,CP), 'Processed_Data')
        PRF_2021 = [HIPSFILE, 'Surfaces', 'Vessel_Config']
        chdir(Pro_F)
        for folder in PRF_2021:
            full_path = Pro_F
            if path.exists(folder):
                return
            else:
                mkdir(folder)

        Meta_F = path.join(path.join(PL,CP), 'MetaData')
        MF_2021 = ['LogForms', 'Output', 'ISO_Documentation', 'Field_Notes']
        chdir(Meta_F)
        for folder in MF_2021:
            full_path = Meta_F
            if path.exists(folder):
                return
            else:
                mkdir(folder)

        startfile(P_F)
    

    def set_cell_text(self, cell, text):
        if cell.paragraphs:
            p = cell.paragraphs[0]

            for run in p.runs:
                run.text = ""
            
            run = p.add_run(text)
            run.font.name = "Arial"

            for i in range(len(cell.paragraphs) - 1, 0, -1):
                cell._element.remove(cell.paragraphs[i]._element)


    def ISO_1001_07_A_F01(self):

        PH = self.split_Project_Name()
        Project_N = PH[0]

        Sub_Filedir = self.SUB_D.get()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        D = os.path.join(script_dir, '1001_07_A_F01_Template.docx')

        print("CURRENT WORKING DIR:", os.getcwd())
        print("TEMPLATE EXISTS HERE?:", os.path.exists(D))

        document = Document(D)
        Sig = self.SIG.get()

        dir_lst = []
        for filename in listdir(Sub_Filedir):
            if path.isdir(path.join(Sub_Filedir, filename)):
                dir_lst.append(filename)

        Folders = []
        Files = []
        folder_size = []
        for f in dir_lst:
            dir_path = os.path.join(Sub_Filedir, f)

            total_size = 0
            files = 0
            folders = 0

            for root, dirnames, filenames in os.walk(dir_path):
                folders += len(dirnames)
                files += len(filenames)

                for fname in filenames:
                    fpath = os.path.join(root, fname)
                    try:
                        total_size += os.path.getsize(fpath)
                    except:
                        pass
            folder_size.append(total_size)
            Folders.append(folders)
            Files.append(files)

        style = document.styles['Normal']
        font = style.font
        for para in document.paragraphs:
            for run in para.runs:
                run.font.name = 'Arial'
        table = document.tables[0] #a list of all tables in document
        start_row = None

        for i, row in enumerate(table.rows):
            text = " ".join(cell.text for cell in row.cells)

            if "Folder size" in text and "NTMASC" in text:
                start_row = i + 1
                break

        if start_row is None:
            print("ERROR: Could not find table start row")
            return
        #required_rows = len(dir_lst) + 2

        end_row = None

        for i, row in enumerate(table.rows):
            text = " ".join(cell.text for cell in row.cells)

            if "Additional Submission Notes" in text:
                end_row = i
                break

        if end_row is None:
            print("ERROR: Could not find end of data section")
            return

        needed_rows = len(dir_lst) - (end_row - start_row)

        template_row = table.rows[start_row]

        for _ in range(needed_rows):
            new_row = deepcopy(template_row._element)
            table._tbl.insert(end_row, new_row)
            end_row += 1

        for i, row in enumerate(table.rows):
            text = " ".join(cell.text for cell in row.cells)

            if "Additional Submission Notes" in text:
                end_row = i
                break
        
        for row in table.rows:
            full_text = " ".join(cell.text for cell in row.cells)

            if "Project Number & Location:" in full_text:
                self.set_cell_text(row.cells[0], f"Project Number & Location: {Project_N}")
                break
    
        #c = 3
        i = 0
            
        #t_d = DATES.datetime.today()
        t_d = datetime.today().strftime("%d-%m-%Y")
        for i, f in enumerate(dir_lst):
            row_index = start_row + i

            if row_index >= end_row:
                break

            row = table.rows[row_index]

            if len(row.cells) < 4:
                continue

            self.set_cell_text(row.cells[0], f)
            self.set_cell_text(row.cells[1],
                                    f"Size: {format(folder_size[i], ',')} bytes\n"
                                    f"Contains: {Files[i]} Files, {Folders[i]} Folders")
            self.set_cell_text(row.cells[2], Sig)
            self.set_cell_text(row.cells[3], f"{Sig}\n{t_d}")
    

            #c += 1
            
        table = document.tables[0]

        for row in table.rows:
            full_text = " ".join(cell.text for cell in row.cells)

            if "Submission verified by Hydrographer in Charge (insert full name):" in full_text:
                for cell in row.cells:
                    if "Submission verified" in cell.text:
                        self.set_cell_text(cell, f"Submission verified by Hydrographer in Charge: {Sig}")
                
                for cell in row.cells:
                    if "Date:" in cell.text:
                        self.set_cell_text(cell, f"Date: {t_d}")
            
            elif "Processed by HDC staff (insert full name):" in full_text:
                for cell in row.cells:
                    if "Processed by HDC staff (insert full name)" in cell.text:
                        self.set_cell_text(cell, "Processed by HDC staff:")
                
                for cell in row.cells:
                    if "Date:" in cell.text:
                        self.set_cell_text(cell, "Date:")

        
        doc = (Sub_Filedir + '/1001_07_A_F01_' + str(Project_N) + '.docx')
        document.save(doc)

        startfile(doc)


    def Find_Fliers(self):

        height = self.FHEIGHT.get()
        DTM_dir = self.DTM_DIR.get()
        DTMs = listdir(DTM_dir)

        if path.exists(DTM_dir + '/' + 'FlierFinder'):
            return
        else:
            mkdir(DTM_dir + '/' + 'FlierFinder')

        chdir(owd)

        with open("FindFliers.bat", "w") as Import:
            Import.write('@ECHO OFF' + '\n')
            Import.write('@ECHO Checking for Fliers' + '\n')
            Import.write('cd '+ QCTools + '\n')

            for dtm in DTMs:
                if dtm.ensdwith('*.csar'):
                    if height != 'AUTO':
                        Import.write('QCTools FindFliers -enforce_height' + height + '\n')
                    else:
                        Import.write('QCTools FindFliers ' + '\n')

                    Import.write('-check_laplacian ' + '-check_curv ' +  '-check_isolated ' + '-check_slivers ' +
                                 DTM_dir + '/' + dtm + ' ' + DTM_dir + '/' + 'FlierFinder')


        p = S.check_call("FindFliers.bat", stdin=None, stdout=None, stderr=None, shell=False)


    def Help(self):
        return


    def close(self):
        self.Exit = 'True'
        self.popup_SavePar()
        root.destroy()


def on_closing():
    if messagebox.askokcancel("Quit", "Did you save Parameters?"):
        root.destroy()

root = Tk()
root.title("CHS Pycessing Tool")
root.geometry("700x750")
menu = Menu(root)
root.config(menu=menu)
submenu = Menu(menu)
submenu2 = Menu(menu)
notebook = ttk.Notebook(root)
frame1 = ttk.Frame(notebook)
notebook.add(frame1, text="Caris Hips\nProcessing")
frame2 = ttk.Frame(notebook)
notebook.add(frame2, text="Import Sensor\nData")
frame3 = ttk.Frame(notebook)
notebook.add(frame3, text="Import Auxiliary\nData")
frame4 = ttk.Frame(notebook)
notebook.add(frame4, text="Apply\nTides")
frame5 = ttk.Frame(notebook)
notebook.add(frame5, text="Compute\nTPU")
frame7 = ttk.Frame(notebook)
notebook.add(frame7, text="HIPS\nGRID")
notebook.grid(row=0, column=0)
frame8 = ttk.Frame(notebook)
notebook.add(frame8, text="CA\nTools")
frame9 = ttk.Frame(notebook)
notebook.add(frame9, text="Reporting and \nData Submission")
notebook.grid(row=0, column=0)
frame10 = ttk.Frame(notebook)
notebook.add(frame10, text="Finalization")
app = Application(root)
root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
