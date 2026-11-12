#ORISE 2026 - CARI-7/7A file running automation script - Hannah R Swanson 

import os
import shutil
import math
import csv
import datetime
import pyautogui
import time
import psutil
import matplotlib.pyplot as plt
import pandas as pd
import re
import sys
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch

def open_application(DVD_path, file_name): #opens CARI-7/7A
    if not os.path.exists(DVD_path):
        print(f"Folder '{DVD_path}' does not exist.")
        return
    file_path = os.path.join(DVD_path, file_name)
    if not os.path.isfile(file_path):
        print(f"File '{file_name}' does not exist in '{DVD_path}'.") #says the file doesn't exist in the folder 
    try:
        print("Opening application...") #opens CARI-7/7A
        time.sleep(1)
        os.startfile(DVD_path)
        #print("Waiting for application to load...") 
        time.sleep(5)
        pyautogui.write(file_name)
        pyautogui.press("enter")
    except Exception as e:
        print(f"Error clicking the file: {e}") #says application won't open 

def batch_run(source_folder, DVD_folder): #reformats .csv files and puts them into .deg files
    csv_files = [file for file in os.listdir(source_folder) if file.endswith('.csv')] #searches for any .csv file in folder 
    for source_name in csv_files:
        d = -1
        source_path = os.path.join(source_folder, source_name)
        print("File being processed: ", source_name) #states the name of the file being processed
        if os.path.exists(source_path):
            with open(source_path, 'r', encoding='utf-8', errors='replace') as source_file:
                csv_reader = csv.reader(source_file)#reads the .csv file
                headers = [h.strip() for h in next(csv_reader)]
                #print(headers)
                lat_index = None
                long_index = None
                alt_index = None
                time_index = None
                for i, header in enumerate(headers):
                    if "Time" in header:
                        time_index = i
                    elif "Latitude" in header:
                        lat_index = i
                    elif "Longitude" in header:
                        long_index = i
                    elif "feet" in header or "Elevation" in header or "Altitude (ft)" in header:
                        alt_index = i
                #print(time_index, lat_index, long_index, alt_index)
                #if None in (lat_index, long_index, alt_index):
                    #print(f"Required columns not found in {source_name}")
                    #continue
                new_file = [] #creates a new file
                duration_present = False
                last_minute = None
                for row in csv_reader:
                    if len(row) <= max(lat_index, long_index, alt_index):
                        continue
                    time_string = row[time_index].strip()
                    if not time_string:
                        continue
                    parts = time_string.split()
                    if len(parts) == 1:
                        time_part = parts[0]
                    else:  
                        time_part = parts[1]
                    current_minute = time_part[:5]
                    if current_minute == last_minute:
                        continue
                    last_minute = current_minute
                    latitude = float(row[lat_index]) #first row
                    longitude = float(row[long_index]) #second row
                    altitude = int(row[alt_index].replace(",", "")) #third row
                    d += 1 #incrememnt duration (mostly for if there is no time in .csv
                    duration = str(d) #fourth row
                    new_lat = str(abs(latitude)).split(".")
                    degrees_lat = int(new_lat[0])
                    decimal_lat = float("0." + new_lat[1]) if len(new_lat) > 1 else 0.0
                    minutes_lat = round(decimal_lat * 60, 2)
                    direction_lat = "N" if latitude >= 0 else "S"
                    new_long = str(abs(longitude)).split(".")
                    degrees_long = int(new_long[0])
                    decimal_long = float("0." + new_long[1]) if len(new_long) > 1 else 0.0
                    minutes_long = round(decimal_long * 60, 2)
                    direction_long = "E" if longitude >= 0 else "W"
                    new_row = [degrees_lat, minutes_lat, direction_lat, degrees_long, minutes_long, direction_long, altitude, duration]
                    new_file.append(new_row) #creates new file
            #creates flight name and file name
            flight_name = os.path.splitext(source_name)[0]
            while True:
                new_name = input(f"File named {flight_name} \n"
                                 "Press ENTER to use this filename or enter a different filename (no special characters!): ").strip()
                if new_name == "":
                    flight = flight_name
                    break
                else:
                    flight = new_name
                    break
            DVD_file = flight + extensions[0]
            DVD_path = os.path.join(DVD_folder, DVD_file) #puts the new file in the DVD folder

            #defines and creates dates 
            modification_time = os.path.getmtime(source_path) 
            modification_datetime = datetime.datetime.fromtimestamp(modification_time)
            default_date = modification_datetime.strftime("%m/%Y")
            while True:
                user_date = input(f"File last modified: {default_date}\n"
                                  "Press ENTER to use this date or enter a different date as MM/YYYY: ").strip()
                if user_date == "":
                    formatted_date = default_date
                    break
                try:
                    datetime.datetime.strptime(user_date, "%m/%Y")
                    formatted_date = user_date
                    break
                except ValueError:
                    print("Invalid format. Enter the date as MM/YYYY")

            #rewrites new header 
            with open(source_path, 'w', newline='') as updated_file:
                csv_writer = csv.writer(updated_file)
                updated_file.write("{}, {}\n".format(formatted_date, flight))
                updated_file.write("DEG MIN N/S DEG MIN E/W FEET TIME(MIN)\n")
                csv_writer.writerows(new_file)

                #moves the file to the DVD folder
            shutil.move(source_path, DVD_path)
            time.sleep(5)
            print(f"File edited and saved to CARI_7_DVD successfully as {DVD_file} \n")
        else:
            #says the file isn't found in the original folder 
            print("File not found in source folder") 
            print("Source Folder: ", source_folder)
            print("File Name: ", source_name)

def update_default(DVD_folder, default_file, measurement, dose, print_dose=True):
    default_path = os.path.join(DVD_folder, default_file)
    if not os.path.isfile(default_path):
        print(f"File {default_file} does not exist in {DVD_folder}")
        return
    try:
        with open(default_path, "r") as file:
            lines = file.readlines()
        lines[2] = lines[2].replace(lines[2].strip(), str(measurement))
        lines[3] = lines[3].replace(lines[3].strip(), str(dose))
        with open(default_path, "w") as file:
            file.writelines(lines)
        if print_dose:
            if dose == "1":
                if measurement == 0:
                    print("Updated dose to Total Ion Fluence (excluding neutrons and photons")
                else:
                    print("Updated dose to Secondary Particle Fluence")
            elif dose == "2":
                print("Updated dose to ICRP Pub. 103 Effective Dose")
            elif dose == "3":
                print("Updated dose to ICRP Pub. 60 Effective Dose")
            elif dose == "4":
                print("Updated dose to ICRU Ambient Dose Equivalent H*(10)")
            elif dose == "5":
                print("Updated dose to Average Whole-Body Absorbed Dose")
            elif dose == "6":
                print("Updated dose to Dose in 0.5mm Si")
            elif dose == "7":
                print("Updated dose to Dose in 0.3mm Si")
            elif dose == "8":
                print("Updated dose to NM64 Neutron Monitor Response Rate")
        if measurement == 0:
            print("Updated to Total")
        elif measurement == 1:
            print("Updated to Neutrons")
        elif measurement == 2:
            print("Updated to Photons (Gamma)")
    except Exception as e:
              print(f"Error updating file: {e}")
    return

def update_name(DVD_folder, measurement):
    ignore_files = {"DEBUGGER.DAT"}
    if measurement not in ("N", "P", "I"):
        return
    for file in os.listdir(DVD_folder):
        if file.upper() in ignore_files:
            continue
        name, ext = os.path.splitext(file)
        if ext.upper() not in (".DAT", ".SUM"):
            continue
        if name.endswith(("_N", "_P", "_I")):
            continue
        old_path = os.path.join(DVD_folder, file)
        new_path = os.path.join(DVD_folder, f"{name}_{measurement}{ext}")
        if os.path.exists(new_path):
            os.remove(new_path)
        os.rename(old_path, new_path)

def total_table(results_folder, measurement, dose, pdf_base):
    tables = {}
    for file in os.listdir(results_folder):
        if not file.upper().endswith(".SUM"):
            continue
        #print(f"Reading {file}")
        results_path = os.path.join(results_folder, file)
        with open(results_path, "r") as f:
            lines = f.readlines()
        flight = lines[0].strip()
        if ".DEG" not in flight:
            continue
        flight_name = flight.replace("FLIGHT FROM", "")
        flight_name = flight_name.replace(".DEG", "").strip()
        filename = os.path.splitext(file)[0]
        if filename.endswith("_I"):
            radiation = "Ion"
            base_flight = filename[:-2]
        elif filename.endswith("_N"):
            radiation = "Neutron"
            base_flight = filename[:-2]
        elif filename.endswith("_P"):
            radiation = "Gamma"
            base_flight = filename[:-2]
        else:
            continue
        dose_line = lines[-1].strip()
        parts = dose_line.split()
        doseValue = float(parts[0])
        units = parts[2].replace(",", "")
        dose_type = dose_line.split(",", 1)[1]
        dose_type = dose_type.replace("DOSE", "").strip().title()
        if dose_type not in tables:
            tables[dose_type] = {"units": units,
                                 "flights": {} }
        flights = tables[dose_type]["flights"]
        if base_flight not in flights:
            flights[base_flight] = {"Ion": "",
                                    "Neutron": "",
                                    "Gamma": ""}
        flights[base_flight][radiation] = f"{doseValue:.5f}"
        #print(tables.keys())
    styles = getSampleStyleSheet()
    title_style = styles["Heading1"]
    title_style.alignment = TA_CENTER
    for dose_type, info in tables.items():
        units = info["units"]
        flights = info["flights"]
        pdf_name = f"{pdf_base}.pdf"
        pdf_path = os.path.join(results_folder, pdf_name)
        if dose == "1" and measurement in ("I", "A"):
            first_column = f"Total Ion Dose \n ({units})"
        else:
            first_column = f"Total Dose \n ({units})"
        table_data = [["Flight Name",
                        first_column,
                        f"Total Neutron Dose \n ({units})",
                        f"Total Gamma Dose \n({units})" ]]
        for flight in sorted(flights):
            table_data.append([flight,
                                flights[flight]["Ion"],
                                flights[flight]["Neutron"],
                                flights[flight]["Gamma"]])
        table = Table(table_data, colWidths=[2.2*inch, 1.6*inch, 1.6*inch, 1.6*inch])
        table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                                       ("GRID", (0, 0), (-1, -1), 1, colors.black),
                                       ("BOX", (0, 0), (-1, -1), 1.5, colors.black),
                                       ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                                       ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                                       ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                                       ("TOPPADDING", (0, 1), (-1, -1), 5),
                                       ("BOTTOMPADDING", (0, 1), (-1, -1), 5), ]))
        doc = SimpleDocTemplate(pdf_path)
        elements = [Paragraph(f"{pdf_base}", title_style),
                    table, Spacer(1, 0.25 * inch),
                    Paragraph(f"<b>Dose Tally:</b> {dose_type} dose ({units})", styles["Normal"])]
        doc.build(elements)
        print(f"Total doses displayed in {pdf_name}")
    

def check_open(file_name, check_interval = 1):
    printed = False
    while True:
        running = False
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] and proc.info['name'].lower() == file_name.lower():
                    running = True
                    if not printed:
                        print("Running files... ")
                        printed = True
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        if not running:
            print("Closed \n")
            return True

def altitude_data(results_folder):
    deg = [file for file in os.listdir(results_folder) if file.endswith('.DEG')]
    altitude_dictionary = {}
    for file in deg:
        deg_name = os.path.splitext(file)[0]
        deg_path = os.path.join(results_folder, file)
        duration = []
        altitude = []
        with open(deg_path, 'r', newline='', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            next(csv_reader, None)
            next(csv_reader, None)
            for row in csv_reader:
                if len(row) >= 8:
                    try:
                        duration.append(float(row[7]))
                        altitude.append(float(row[6]))
                    except ValueError:
                        continue
        altitude_dictionary[deg_name] = (duration, altitude)
    return altitude_dictionary

def dose_data(results_folder):
    dat = [file for file in os.listdir(results_folder) if file.endswith('.DAT')]
    dose_dictionary = {}
    for file in dat:
        dat_name = os.path.splitext(file)[0]
        if dat_name.endswith(("_I", "_N", "_P")):
            basename = dat_name[:-2]
        else:
            basename = dat_name
        dat_path = os.path.join(results_folder, file)
        rate = []
        total = []
        last = ""
        with open(dat_path, 'r', encoding='utf-8') as file:
            for line in file:
                last = line.strip()
                row = line.split()
                if len(row) < 6:
                     continue
                try:
                    rate.append(float(row[4]))
                    total.append(float(row[5]))
                except ValueError:
                    continue
        try:
            doseUnits = last.split()
            total_dose = float(doseUnits[0])
            units = doseUnits[2]
        except(ValueError, IndexError):
            total_dose = None
            units = ""
        if basename not in dose_dictionary:
            dose_dictionary[basename] = {}
        if dat_name.endswith("_I"):
            ending = "_I"
        elif dat_name.endswith("_N"):
            ending = "_N"
        elif dat_name.endswith("_P"):
            ending = "_P"
        else:
            ending = ""
        dose_dictionary[basename][ending] = (rate, total, total_dose, units)
    return dose_dictionary

def plot_flight(duration, altitude, measurements, filename, results_folder, plot_type):
    fig, ax1 = plt.subplots(figsize=(10, 6))
    line1 = ax1.plot(duration, altitude, color="red", label="Altitude")
    ax1.set_xlabel("Time (min)")
    ax1.set_ylabel("Altitude (ft)")
    ax1.grid(True)
    ax2 = ax1.twinx()
    dose_lines = []
    for ending, data in measurements.items():
        rate, total, total_dose, units = data
        n = min(len(duration), len(rate))
        if n == 0:
            continue
        dose_line = ax2.plot(duration[:n], rate[:n], label=f"Dose Rate {ending}")
        dose_lines.extend(dose_line)
    ax2.set_ylabel(f"Dose Rate ({units})")
    lines = line1 + dose_lines
    labels = [line.get_label() for line in lines]
    ax1.legend(lines, labels, loc="upper left")
    plt.title(f"Dose Rate and Altitude vs Flight Duration for {filename}")
    total_box = "TOTAL DOSE\n"
    for ending, data in measurements.items():
        rate, total, total_dose, units = data
        if total_dose is not None:
            total_box += (f"{ending}: {total_dose:.4e} {units}\n")
    total_box = total_box.rstrip()
    ax1.text(0.72, 0.98, total_box, transform=ax1.transAxes, fontsize=10,
            verticalalignment="top", bbox=dict(boxstyle="round", facecolor="white",
            alpha=0.7))
    fig.tight_layout(rect=[0, 0, 0.82, 1])
    if plot_type =="F":
        save_path = os.path.join(results_folder, f"{filename}_F.png")
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
    elif plot_type == "R":
        save_path = os.path.join(results_folder, f"{filename}_R.png")
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
    else:
        print()
    plt.close()
    print(f"{filename} plotted")
    
def plot_run(dose_points, results_folder, filename):
    ending_labels = {
        "_I": "Total",
        "_N": "Neutron",
        "_P": "Gamma"}
    for ending, label in ending_labels.items():
        basenames = []
        total_doses = []
        for basename, measurements in dose_points.items():
            if ending in measurements:
                rate, total, total_dose, units = measurements[ending]
                if total_dose is not None:
                    basenames.append(basename)
                    total_doses.append(total_dose)
        if not total_doses:
            print(f"No {ending} data found. Skipping plot.")
            continue
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.bar(basenames, total_doses, color="blue")
        ax.set_xlabel("Flight")
        ax.set_ylabel(f"Total Dose ({units})")
        ax.set_title(f"{label} Dose")
        plt.xticks(rotation=45, ha="right")
        ax.grid(axis="y", linestyle="--", alpha=0.5)
        fig.tight_layout()
        output_filename = f"{filename}{ending}.png"
        output_path = os.path.join(results_folder, output_filename)
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"{output_filename} saved")

def base_name(filename):
    name = os.path.splitext(filename)[0]
    if name.endswith("_N") or name.endswith("_P") or name.endswith("_I"):
        return name[:-2]
    return name

def transfer(DVD_folder, results_folder):
    flights = {}
    for root, _, files in os.walk(DVD_folder):
        for file in files:
            ext = os.path.splitext(file)[1].upper()
            if ext not in (".DEG", ".DAT", ".SUM"):
                continue
            flight = base_name(file)
            if flight not in flights:
                flights[flight] = {"DEG": None,
                                   "DAT": [],
                                   "SUM": []}
            path = os.path.join(root, file)
            if ext == ".DEG":
                flights[flight]["DEG"] = path
            elif ext == ".DAT":
                flights[flight]["DAT"].append(path)
            elif ext == ".SUM":
                flights[flight]["SUM"].append(path)
    transferred = 0
    for flight, files in flights.items():
        if files["DEG"] is None:
            continue
        if len(files["DAT"]) == 0 or len(files["SUM"]) == 0:
            continue
        print(f"Transferring {flight} files")
        shutil.move(files["DEG"], os.path.join(results_folder, os.path.basename(files["DEG"])))
        for dat in files["DAT"]:
            shutil.move(dat, os.path.join(results_folder, os.path.basename(dat)))
        for SUM in files["SUM"]:
            shutil.move(SUM, os.path.join(results_folder, os.path.basename(SUM)))
        transferred += 1
    if transferred == 0:
        print("No flight files to transfer")
        

if __name__ == "__main__":
    extensions = (".DEG", ".DAT", ".SUM") #list of file extensions
    default_file = "DEFAULT.INP"
    program = input("Type 7 for CARI-7 or 7A for CARI-7A (Case Sensitive): ") #input prompt for 7 or 7A

    while program != "7" and program != "7A":
        print("Not an option, please try again. Case Sensitive")
        program = input("Type 7 for CARI-7 or 7A for CARI-7A (Case Sensitive): ")
    if program == "7": #cari-7
        file_name = 'cari-7.exe' #looks for cari7 application, I removed the linux version from the DVD folder for 7
        source_folder = input("Paste the folder path where files are coming from: ") #for .csv files
        DVD_folder = input("Paste the folder path the CARI-7 application is located: ") #the DVD folder
        DVD_path = DVD_folder
        batch_run(source_folder, DVD_folder)
        
        measurement = input("Type N for Neutrons, P for Photons, I for Ions, A for all three (Case Sensitive): ")
        while measurement not in ("N", "P", "I", "A"):
            print("Any other radiation measurement must be change manually in DEFAULT.INP")
            print("Manually change measurement and re-run script")
            sys.exit() 
        print("\n Dose Type Options: ")
        if measurement == "I" and measurement != "N" and measurement != "P":
            print("1 = Total ion fluence excluding neutrons and photons)")
        else:
            print("1 = Secondary particle fluence")
        print("2 = ICRP Pub. 103 Effective Dose (microSv)")
        print("3 = ICRP Pub. 60 Effective Dose (microSv)")
        print("4 = ICRU Ambient Dose Equivalent H*(10) (microSv)")
        print("5 = Average Whole-Body Absorbed Dose (microGy)")
        print("6 = Dose in 0.5 mm Si (microGy)")
        print("7 = Dose in 0.3 mm Si (microGy)")
        print("8 = NM64 Neutron Monitor Response Rate (Counts)")
        dose = input("Type the number for the dose type: ")
        while dose not in ("1", "2", "3", "4", "5", "6", "7", "8"):
            dose = input("Not an option. \n Type the number for the dose type: ")
            
        if measurement == "I":
            update_default(DVD_folder, default_file, 0, dose, True)
            open_application(DVD_path, file_name)
            time.sleep(20)
            check_open(file_name)
            update_name(DVD_folder, measurement)
            
        elif measurement == "N":
            update_default(DVD_folder, default_file, 1, dose, True)
            open_application(DVD_path, file_name)
            time.sleep(20)
            check_open(file_name)
            update_name(DVD_folder, measurement)
            
        elif measurement == "P":
            update_default(DVD_folder, default_file, 2, dose, True)
            open_application(DVD_path, file_name)
            time.sleep(20)
            check_open(file_name)
            update_name(DVD_folder, measurement)
            
        elif measurement == "A":
            update_default(DVD_folder, default_file, 0, dose, True) #ions
            open_application(DVD_path, file_name)
            time.sleep(20)
            check_open(file_name)
            update_name(DVD_folder, "I")

            if dose == "1":
                print("Updated to Secondary Particle Fluence")
            
            update_default(DVD_folder, default_file, 1, dose, False) #neutrons
            open_application(DVD_path, file_name)
            time.sleep(20)
            check_open(file_name)
            update_name(DVD_folder, "N")
            
            update_default(DVD_folder, default_file, 2, dose, False) #photons
            open_application(DVD_path, file_name)
            time.sleep(20)
            check_open(file_name)
            update_name(DVD_folder, "P")
        else:
            print("Any other radiation measurement must be change manually in DEFAULT.INP")
            print("Manually change measurement and re-run script")
            sys.exit()
        time.sleep(5)
        print("Files run in CARI-7")
        time.sleep(1)
        
        results_folder = input("Paste the file path where processed data files should go: ")
        transfer(DVD_folder, results_folder)
        rename_dict = update_name(results_folder, measurement)
        toPlot = input("Would you like to plot data as dose and altitude V time? Y/N  ")
        if toPlot == "Y":
            altitude_points = altitude_data(results_folder)
            dose_points = dose_data(results_folder)
            plot_type = input("Plot by flight(F) or by run (R)? ")
            if plot_type == "F":
                plots = 0
                print("Plotting... ")
                for basename, measurements in dose_points.items():
                    if basename not in altitude_points:
                        print(f"No altitude data found for {basename}")
                        continue
                    duration, altitude = altitude_points[basename]
                    plot_flight(duration, altitude, measurements, basename, results_folder, plot_type)
            elif plot_type == "R":
                filename = input("Enter a filename for the plots: ")
                plot_run(dose_points, results_folder, filename)
            else:
                print()
            print(f"All files plotted and saved to {os.path.basename(os.path.normpath(results_folder))} folder")
        else:
            print()
        time.sleep(1)
        makeTable = input("Would you like total doses from flights made into a table? Y/N  ")
        if makeTable == "Y":
            pdf_base = input("Enter a name for the table file (no special characters): ").strip()
            total_table(results_folder, measurement, dose, pdf_base)
        else:
            print()
        time.sleep(5)

    else: #cari-7a
        file_name = 'cari-7a.exe' #the linux version and other application versions are still in the DVD folder for now 
        source_folder = input("Paste the folder path where files are coming from: ") #for .csv files 
        DVD_folder = input("Paste the folder path the CARI-7 application is located: ") #7A DVD folder
        DVD_path = DVD_folder
        batch_run(source_folder, DVD_folder)
        
        measurement = input("Type N for Neutrons, P for Photons, I for Ions, A for all three (Case Sensitive): ")
        while measurement not in ("N", "P", "I", "A"):
            print("Any other radiation measurement must be change manually in DEFAULT.INP")
            print("Manually change measurement and re-run script")
            sys.exit() 
        print("\n Dose Type Options: ")
        if measurement == "I":
            print("1 = Total ion fluence excluding neutrons and photons")
        else:
            print("1 = Secondary particle fluence")
        print("2 = ICRP Pub. 103 Effective Dose (microSv)")
        print("3 = ICRP Pub. 60 Effective Dose (microSv)")
        print("4 = ICRU Ambient Dose Equivalent H*(10) (microSv)")
        print("5 = Average Whole-Body Absorbed Dose (microGy)")
        print("6 = Dose in 0.5 mm Si (microGy)")
        print("7 = Dose in 0.3 mm Si (microGy)")
        print("8 = NM64 Neutron Monitor Response Rate (Counts)")
        dose = input("Type the number for the dose type: ")
        while dose not in ("1", "2", "3", "4", "5", "6", "7", "8"):
            dose = input("Not an option. \n Type the number for the dose type: ")

        if measurement == "I":
            update_default(DVD_folder, default_file, 0, True)
            open_application(DVD_path, file_name)
            time.sleep(20)
            check_open(file_name)
            update_name(DVD_folder, measurement)
            
        elif measurement == "N":
            update_default(DVD_folder, default_file, 1, True)
            open_application(DVD_path, file_name)
            time.sleep(20)
            check_open(file_name)
            update_name(DVD_folder, measurement)
            
        elif measurement == "P":
            update_default(DVD_folder, default_file, 2, True)
            open_application(DVD_path, file_name)
            time.sleep(20)
            check_open(file_name)
            update_name(DVD_folder, measurement)
            
        elif measurement == "A":
            update_default(DVD_folder, default_file, 0, True) #ions
            open_application(DVD_path, file_name)
            time.sleep(20)
            check_open(file_name)
            update_name(DVD_folder, "I")
            
            update_default(DVD_folder, default_file, 1, False) #neutrons
            open_application(DVD_path, file_name)
            time.sleep(20)
            check_open(file_name)
            update_name(DVD_folder, "N")
            
            update_default(DVD_folder, default_file, 2, False) #photons
            open_application(DVD_path, file_name)
            time.sleep(20)
            check_open(file_name)
            update_name(DVD_folder, "P")
        else:
            print("Any other radiation measurement must be change manually in DEFAULT.INP")
            print("Manually change measurement and re-run script")
            sys.exit()
        time.sleep(5)
        print("Files are run in CARI-7A")
        time.sleep(1)
        
        results_folder = input("Paste the file path where processed data files should go: ")
        transfer(DVD_folder, results_folder)
        rename_dict = update_name(results_folder, measurement)
        toPlot = input("Would you like to plot data as dose and altitude V time? Y/N  ")
        if toPlot == "Y":
            altitude_points = altitude_data(results_folder)
            dose_points = dose_data(results_folder)
            plot_type = input("Plot by flight(F) or by run (R)? ")
            if plot_type == "F":
                plots = 0
                print("Plotting... ")
                for basename, measurements in dose_points.items():
                    if basename not in altitude_points:
                        print(f"No altitude data found for {basename}")
                        continue
                    duration, altitude = altitude_points[basename]
                    plot_flight(duration, altitude, measurements, basename, results_folder, plot_type)
            elif plot_type == "R":
                filename = input("Enter a filename for the plots: ")
                plot_run(dose_points, results_folder, filename)
            else:
                print()
            print(f"All files plotted and saved to {os.path.basename(os.path.normpath(results_folder))} folder")
        else:
            print()
        time.sleep(1)
        makeTable = input("Would you like total doses from flights made into a table? Y/N  ")
        if makeTable == "Y":
            total_table(results_folder)
        else:
            print()
        time.sleep(5)


    


        
    


