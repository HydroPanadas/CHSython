## This application allows users in survey unit to accept one or more survey block extent as an input,
## query the CHS Products ESRI Web Map Service/Map Server, identify affected CHS products within extents,
## and produce a consolidated list matching ENC, Paper Charts, and BSB products.
## The product list will be used to retrieve most current available chart products, and extract downloaded files
## into a structured output directory

from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
from bs4 import BeautifulSoup
import urllib3
import os
from os import path
import time
import logging
import zipfile
import requests
import geopandas as gpd
import pandas as pd
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CHS_PRODUCTS = {"ENC" : 2,
                "ENC_NO_CHART" : 3,
                "BSB" : 4,
                "PAPER" : 5}

BASE_URL = "https://egisp.dfo-mpo.gc.ca/arcgis/rest/services/chs/CHS_Products/MapServer"

class Application(Frame):
    """Initialize Query Application"""

    def __init__(self, master):
        """Initialize the Frames for Queries"""
        Frame.__init__(self, master)
        self.grid()
        self.app_widgets()
        self.product_set = set()


    def app_widgets(self):
        """Creates Widgets for user GUI"""
        PRODUCTS = LabelFrame(self, text="CHS Product Retrieval", foreground="blue")
        PRODUCTS.grid(row=0, column=0, padx=1, sticky=W)

        self.EXTENT_FILE = StringVar()
        Label(PRODUCTS, text="Extent Shapefile").grid(row=0, column=0, sticky=W)
        self.EXTENT = Entry(PRODUCTS, width=60, textvariable=self.EXTENT_FILE)
        self.EXTENT.grid(row=0, column=1, sticky=W)
        Button(PRODUCTS, text="...", command=self.Search_Extent_File).grid(row=0, column=2, padx=5, sticky=W)

        self.OUT_DIR = StringVar()
        Label(PRODUCTS, text="Output Folder").grid(row=1, column=0, sticky=W)
        self.OUT = Entry(PRODUCTS, width=60, textvariable=self.OUT_DIR)
        self.OUT.grid(row=1, column=1, sticky=W)
        Button(PRODUCTS, text="...", command=self.Search_Output).grid(row=1, column=2, padx=5, sticky=W)

        self.progress = ttk.Progressbar(PRODUCTS, orient=HORIZONTAL, length=450, mode="determinate")
        self.progress.grid(row=2, column=0, columnspan=3, pady=5)
        self.progress_label = Label(PRODUCTS, text="Idle")
        self.progress_label.grid(row=3, column=0, columnspan=3)

        self.RUN_BUTTON = Button(PRODUCTS, text="Run", command=self.Run_Queries)
        self.RUN_BUTTON.grid(row=4, column=0, sticky=W)

    
    def Search_Extent_File(self):
        """Function to search for shapefile"""
        shp = filedialog.askopenfilename(title="Select Survey Extent", filetypes=[("Shapefile", "*.shp"),
                                                                                  ("GeoPackage", "*.gpkg"),
                                                                                  ("GeoJSON", "*.geojson"),
                                                                                  ("All Files", "*.*")])
        self.EXTENT_FILE.set(shp)


    def Search_Output(self):
        """Function to choose an output directory"""
        folder = filedialog.askdirectory(title="Select Output Folder")
        self.OUT_DIR.set(folder)

    
    def logger_setup(self):
        """Function to initiate logging"""
        current_time = time.strftime("%Y%m%d_%H%M%S")
        
        logfile = path.join(self.OUT_DIR.get(), "Logs", f"CHS_ProductRetrieval_{current_time}.log")
        logging.basicConfig(level=logging.INFO, format="%(asctime)s:%(levelname)s:%(message)s", handlers=[logging.FileHandler(logfile), logging.StreamHandler()])


    def Create_Output_Folders(self):
        """Function to create required output directory structure"""
        folders = ["Reports",
                   "ENC",
                   "BSB",
                   "PAPER",
                   path.join("PAPER", "PDF"),
                   "Logs"]
        
        for folder in folders:
            out = path.join(self.OUT_DIR.get(), folder)
            os.makedirs(out, exist_ok=True)

        
    def Load_Extent(self):
        """Function to load and verify extent file"""
        extent = self.EXTENT_FILE.get()

        if not path.exists(extent):
            raise Exception("Extent file does not exist")
        
        logging.info(f"Loading: {extent}")

        extent_gdf = gpd.read_file(extent)

        if extent_gdf.crs is not None:
            if extent_gdf.crs.to_epsg() != 4326:
                extent_gdf = extent_gdf.to_crs(epsg=4326)

        if len(extent_gdf) == 0:
            raise Exception("No features found in extent.")
        
        logging.info(f"{len(extent_gdf)} features loaded.")
        return extent_gdf


    ## Product Query Functions


    def Load_CHS_Layer(self, layer):
        """Function to retrieve CHS product layer from Map Service"""
        url = (f"{BASE_URL}/{layer}/query?where=1=1&outFields=*&f=geojson")

        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()

            logging.info(f"Layer {layer} reachable")

            gdf = gpd.read_file(url)

            logging.info(f"Layer {layer}: "
                         f"{len(gdf)} features loaded")
            return gdf

        except Exception as e:
            logging.error(f"Failed to load layer {layer}")
            logging.error(str(e))
            return gpd.GeoDataFrame()
    

    def Query_CHS_Products(self, extents):
        """Function to query chart products intersecting extents"""
        all_products = []
        
        for product_type, layer in CHS_PRODUCTS.items():
            logging.info(f"Loading {product_type}")

            layer_gdf = self.Load_CHS_Layer(layer)

            matches = gpd.sjoin(layer_gdf, extents, predicate="intersects", how="inner")

            logging.info(f"{product_type}: {len(matches)} matches")

            if len(matches) > 0:
                matches["PRODUCT_TYPE"] = product_type

                ## Create a common product identifier used for deduplication
                ## ENC/BSB use PRODUCT_ID, Paper charts use REG_PRODUCT_ID
                if "PRODUCT_ID_left" in matches.columns:
                    product_id_field = "PRODUCT_ID_left"
                else:
                    product_id_field = "PRODUCT_ID"

                if product_type == "ENC":
                    matches["UNIQUE_ID"] = (matches[product_id_field])

                elif product_type == "BSB":
                    matches["UNIQUE_ID"] = (matches[product_id_field])

                else:
                    matches["UNIQUE_ID"] = (matches["REG_PRODUCT_ID"])

                all_products.append(matches)

        if len(all_products) == 0:
            return gpd.GeoDataFrame()

        products = gpd.GeoDataFrame(pd.concat(all_products, ignore_index=True))

        logging.info(f"Raw matches before deduplication: {len(products)}")

        report_dir = path.join(self.OUT_DIR.get(), "Reports")

        products.to_csv(path.join(report_dir, "Raw_Products.csv"), index=False)

        if "UNIQUE_ID" in products.columns:
            duplicates = products[products.duplicated(subset=["UNIQUE_ID"], keep=False)]

            duplicates.to_csv(path.join(report_dir, "Duplicates.csv"), index=False)
            
            self.product_set = set(products["UNIQUE_ID"].dropna())

            logging.info(f"{len(self.product_set)} unique products")

            products = products.drop_duplicates(subset=["UNIQUE_ID"])

            logging.info(f"{len(products)} products after deduplication")
        return products


    ## Reporting Functions

    
    def Build_Product_Report(self, products):
        """Function to generate Excel and CSV product reports"""
        report_dir = path.join(self.OUT_DIR.get(), "Reports")

        report_fields = ["PRODUCT_TYPE",
                         "UNIQUE_ID",
                         "TITLE",
                         "NAME",
                         "VERSION_ID",
                         "PC_LAST_EDITION_DATE"]

        report_fields = [field for field in report_fields if field in products.columns]

        report = products[report_fields].copy()

        report.to_excel(path.join(report_dir, "Product_Report.xlsx"), index=False)

        report.to_csv(path.join(report_dir, "Product_Report.csv"), index=False)

        logging.info("Reports created.")
        return report
    

    def Download_File(self, url, save_path):
        """Function to download chart file"""
        try:
            with requests.get(url, stream=True, timeout=60, verify=False) as response:
                response.raise_for_status()

                with open(save_path, "wb") as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            file.write(chunk)

            logging.info(f"Downloaded: {save_path}")
            return True
        
        except Exception as e:
            logging.error(f"Download failed: {url}")
            logging.error(str(e))
            return False
        

    def Extract_Zip(self, zip_file, out_folder):
        """Function to extract zip archive"""
        try:
            with zipfile.ZipFile(zip_file, "r") as z:
                z.extractall(out_folder)

            if os.path.basename(out_folder) == "PAPER":
                pdf_dir = path.join(out_folder, "PDF")

                os.makedirs(pdf_dir, exist_ok=True)

                for file in os.listdir(out_folder):
                    if file.lower().endswith(".pdf"):
                        source = path.join(out_folder, file)

                        destination = path.join(pdf_dir, file)

                        os.replace(source, destination)
            
            logging.info(f"Extracted: {zip_file}")
            return True
        
        except Exception as e:
            logging.error(str(e))
            return False


    def Save_Product_Set(self):
        """Function to generate a text file for the product set"""
        report_dir = path.join(self.OUT_DIR.get(), "Reports")

        outfile = path.join(report_dir, "Product_Set.txt")

        with open(outfile, "w") as f:
            for product in sorted(self.product_set):
                f.write(f"{product}\n")

        logging.info(f"Saved {len(self.product_set)} products")


    ## Download Functions


    def Get_ENC_Download_URL(self, enc_id):
        """Function to build ENC download URL"""
        return (f"https://wwwintra.chs-shc.gc.ca/ChartRegistry/ENC/CHSENCS57/CA/{enc_id}.zip")

    
    def Get_PAPER_Download_URL(self, chart_number):
        """Function to retrieve POD chart download url"""
        url = (f"https://wwwintra.chs-shc.gc.ca/dealers-depositaires/pod/current-eng.asp?page=current&region=ALL&chart=&chart2={chart_number}")

        response = requests.get(url, verify=False, timeout=60)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        for link in soup.find_all("a"):
            href = link.get("href", "")

            if href.lower().endswith(".zip"):
                return href
        return None


    def Get_BSB_Download_URL(self, chart_number):
        """Function to retrieve BSB chart download url"""
        url = (f"https://wwwintra.chs-shc.gc.ca/dealers-depositaires/pod/bsb_cur-eng.asp?page=bsb_cur&region=ALL&chart=&chart2={chart_number}")

        response = requests.get(url, verify=False, timeout=60)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        for link in soup.find_all("a"):
            href = link.get("href", "")

            if href.lower().endswith(".zip"):
                return href
        return None


    def Build_Download_URLs(self, report):
        """Function to resolve download URLs for chart products"""
        report["DOWNLOAD_URL"] = None

        for index, row in report.iterrows():
            product_type = str(row["PRODUCT_TYPE"])

            unique_id = str(row["UNIQUE_ID"])

            if product_type == "ENC":
                report.loc[index, "DOWNLOAD_URL"] = (self.Get_ENC_Download_URL(unique_id))

            elif product_type == "PAPER":
                chart_number = str(row["NAME"])

                report.loc[index, "DOWNLOAD_URL"] = (self.Get_PAPER_Download_URL(chart_number))

            elif product_type == "BSB":
                chart_number = unique_id.replace("RM-", "")

                report.loc[index, "DOWNLOAD_URL"] = (self.Get_BSB_Download_URL(chart_number))
        return report


    def Download_Products(self, report):
        """Function to download and extract chart products"""
        if "DOWNLOAD_URL" not in report.columns:
            logging.info("DOWNLOAD_URL field not found.")
            return
        
        total = len(report)

        self.progress["maximum"] = total

        count = 0

        for index, row in report.iterrows():
            count += 1

            self.progress["value"] = count
            self.progress_label.config(text=f"Downloading {count}/{total}")
            self.update_idletasks()

            download_url = str(row["DOWNLOAD_URL"])

            product_type = str(row["PRODUCT_TYPE"])

            if product_type.startswith("ENC"):
                out_dir = path.join(self.OUT_DIR.get(), "ENC")
            
            elif product_type == "BSB":
                out_dir = path.join(self.OUT_DIR.get(), "BSB")

            else:
                out_dir = path.join(self.OUT_DIR.get(), "PAPER")
            
            zip_file = path.join(out_dir, os.path.basename(download_url))

            logging.info(f"Downloading {download_url}")

            success = self.Download_File(download_url, zip_file)

            if success:
                self.Extract_Zip(zip_file, out_dir)


    ## Main Application Workflow
    

    def Run_Queries(self):
        """Function to execute CHS product retrieval workflow"""
        self.RUN_BUTTON.config(state=DISABLED)

        if not self.EXTENT_FILE.get():
            messagebox.showerror("Missing Input", "Please select an extent file.")
            return
        
        if not self.OUT_DIR.get():
            messagebox.showerror("Missing Input", "Please select an output folder.")
            return

        try:
            self.Create_Output_Folders()
            
            self.logger_setup()

            logging.info("CHS Product Retrieval Started")

            extents = self.Load_Extent()
            products = self.Query_CHS_Products(extents)

            if len(products) == 0:
                messagebox.showwarning("No Products", "No products found.")
                return

            logging.info(f"{len(products)} products returned.")

            ## Generate reports and resolve download URLs
            report = self.Build_Product_Report(products)
            report = self.Build_Download_URLs(report)

            self.Save_Product_Set()

            self.Download_Products(report)

            self.progress_label.config(text="Complete")

            ## Create completion summary
            enc_count = len(report[report["PRODUCT_TYPE"] == "ENC"])
            bsb_count = len(report[report["PRODUCT_TYPE"] == "BSB"])
            paper_count = len(report[report["PRODUCT_TYPE"] == "PAPER"])

            summary_file = path.join(self.OUT_DIR.get(), "Reports", "Summary.txt")

            with open(summary_file, "w") as f:
                f.write(f"ENC: {enc_count}\n"
                        f"BSB: {bsb_count}\n"
                        f"PAPER: {paper_count}\n"
                        f"TOTAL: {len(report)}\n")

            summary = (f"ENC Products: {enc_count}\n"
                       f"BSB Products: {bsb_count}\n"
                       f"PAPER Products: {paper_count}\n\n"
                       f"Total Products: {len(report)}")

            messagebox.showinfo("Complete", summary)

        except Exception as e:
            logging.error(str(e))

            messagebox.showerror("Error", str(e))

        finally:
            self.RUN_BUTTON.config(state=NORMAL)

    
root = Tk()
root.title("CHS Product Retrieval Tool")
root.geometry("525x160")
menu = Menu(root)
root.config(menu=menu)
app = Application(root)
root.mainloop()