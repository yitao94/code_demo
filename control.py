# -*- coding: utf-8 -*-
"""
Created on Wed Aug 15 11:20:43 2018

@author:    jin     (orginal)
            dumler  (modified)

about threading:
    https://www.youtube.com/watch?v=kEkS2YOC80E
    https://morvanzhou.github.io/
about GUI:
    Python GUI with Tkinter - 1 - Introduction 
        <https://www.youtube.com/watch?v=RJB1Ek2Ko_Y>
    http://www.runoob.com/python/python-gui-tkinter.html
    How to make the Matplotlib graph live in your application:
        <https://pythonprogramming.net/embedding-live-matplotlib-graph-tkinter-gui/>
"""
import sys
import os
import time
import threading
import numpy as np
import scipy.io

from queue import Queue

from socket import *

import tkinter as tk
from tkinter import ttk
from tkinter import *
from tkinter import messagebox
from tkinter.filedialog import askopenfilename, askdirectory

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from setting import *

#import binascii

LARGE_FONT= ("Verdana", 12)

class App(tk.Tk):

    def __init__(self, *args, **kwargs):        
        tk.Tk.__init__(self, *args, **kwargs)

        #tk.Tk.iconbitmap(self, default="clienticon.ico")
        tk.Tk.wm_title(self, "HyperCam")
        self.title("Control GUI")
        self.geometry("1000x900")
        
        # ----- control frame -----
        controlFrame = tk.Frame(self)
        controlFrame.pack(side=TOP,fill=X)
        button1 = ttk.Button(controlFrame, text="Raw", command=lambda: self.show_frame(P1_Frame))
        button1.pack(side = LEFT)
        button2 = ttk.Button(controlFrame, text="Settings", command=lambda: self.show_frame(P2_Settings))
        button2.pack(side = LEFT)
        button3 = ttk.Button(controlFrame, text="Image", command=lambda: self.show_frame(P3_Image))
        button3.pack(side = LEFT)
        button4 = ttk.Button(controlFrame, text="Spectrum", command=lambda: self.show_frame(P4_Spectrum))
        button4.pack(side = LEFT)

#       # ----- main menu -----
#        menu = Menu(master)
#        master.config(menu=menu)
#
#        fileMenu = Menu(menu)
#        menu.add_cascade(label="File", menu=fileMenu)
#        fileMenu.add_command(label="New", command=self.doNothing)
#        fileMenu.add_command(label="Save", command=self.doNothing)
#        fileMenu.add_separator()
#        fileMenu.add_command(label="Exit", command=lambda:self.exitWindow(master))
#
#        editMenu = Menu(menu)
#        menu.add_cascade(label="Project", menu=editMenu)
#        editMenu.add_command(label="Run", command=self.doNothing)
#        editMenu.add_command(label="Stop", command=self.doNothing)
#        editMenu.add_command(label="Generate", command=self.doNothing)

#        helpMenu = Menu(menu)
#        menu.add_cascade(label="Help", menu=helpMenu)
#        helpMenu.add_command(label="Documentation", command=self.doNothing)
#        helpMenu.add_command(label="Contact", command=self.doNothing)

        # ----- status bar -----
#        statusFrame = tk.Frame(self)
#        self.status_var = StringVar()
#        self.status_var.set("preparing for operation...")
#        statusLabel = Label(statusFrame, textvariable=self.status_var)
#        statusLabel.pack(side=TOP, anchor=W)
#        statusFrame.pack(side=BOTTOM, fill=X)

        # ------- selectable frame ---------
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand = True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)


        self.frames = {}

        for F in (P1_Frame, P2_Settings, P3_Image, P4_Spectrum):

            frame = F(container, self)

            self.frames[F] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(P1_Frame)

    def show_frame(self, cont):

        frame = self.frames[cont]
        frame.tkraise()

        
class P1_Frame(tk.Frame):
    def __init__(self, parent, master):
        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text="Frame", font=LARGE_FONT)
        label.pack(pady=10,padx=10)


        self.socket_flag = 1 # flag of ethernet socket
        self.savePlace_flag = 0
        self.captureFlag = 0
        self.exposure = 100

        mat = scipy.io.loadmat('C:\\python_workspace\\Ethernet_2\\calib.mat')
        self.wl = np.array(mat['wl'])
        self.Mc = np.array(mat['Mc'])

        # -------- Control --------------------------------------------------------------    
        controlFrame = tk.Frame(self)
        controlFrame.pack(side=TOP,fill=X)

        # -------- Exposure -------------------------------------------------------------
        exposureFrame = tk.Frame(controlFrame)
        exposureFrame.pack(side=LEFT,fill=Y)
        exposureSetButton = ttk.Button(exposureFrame, text="Exposure Time", command=self.setExposure)
        exposureSetButton.pack(side=BOTTOM)
        self.exposureEntry = Entry(exposureFrame)
        self.exposureEntry.pack(side=TOP)
        self.exposureEntry.insert(0, "100")

        # -------- Request --------------------------------------------------------------    
        #imageReqButton = ttk.Button(self, text="Request", command=self.requestFrame)
        #imageReqButton.pack()
        reqFrame = tk.Frame(controlFrame)
        reqFrame.pack(side=LEFT,fill=Y)
        imageButton = ttk.Button(reqFrame, text="Request Frame", command=self.captureFrame)
        imageButton.pack(side=LEFT,fill=Y)

        # ------- Save --------
        saveFrame = tk.Frame(controlFrame)
        saveFrame.pack(side=RIGHT)        
        saveButton = ttk.Button(saveFrame, text="Save", command=self.saveFrame)
        saveButton.grid(row=2, column=1, ipadx=10)
        saveplaceButton = ttk.Button(saveFrame, text="Path", command=self.savePlace)
        saveplaceButton.grid(row=2, column=2, ipadx=10)
        self.saveplace_var = tk.StringVar()   
        self.saveplace_var.set("Select save location")
        saveplaceLabel = Label(saveFrame, textvariable=self.saveplace_var)
        saveplaceLabel.grid(row=1, column=1, columnspan=2)
  
        #outputButton = ttk.Button(self, text="Plot", command=self.plotImage)
        #outputButton.pack()

        # -------- Image --------------------------------------------------------------    
        self.outputData = np.zeros((IMAGE["ROW"], IMAGE["COLUMN"])) # initial
        self.outputFigure = Figure(figsize=(5,5), dpi=100)
        self.outputImageGrey = self.outputFigure.add_subplot(111)

        self.outputImageGrey.set_title("raw frame")
        self.outputImageGrey.imshow(self.outputData, cmap='gray', interpolation='nearest', aspect='auto')
        
        self.canvas = FigureCanvasTkAgg(self.outputFigure, self)        
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=BOTTOM, fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2Tk(self.canvas, self)
        toolbar.update()
        self.canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)        
                
        # following paremeter
   
    #----------------------------------------------------------------------------------------------------------------------------------------------------------
    def connectSocket(self):
        self.socket = socket(AF_INET, SOCK_STREAM)
        try:
            self.socket.connect((ETHERNET["IP"], ETHERNET["PORT"]))
            self.socket.settimeout(0.005)
            self.socket_flag = 2
        except:
            messagebox.showwarning("Warning", "there is already an connection.")
            return -1
        #self.status_var.set("Connection has been set.")
    
    #----------------------------------------------------------------------------------------------------------------------------------------------------------
    def disconnectSocket(self):
#       print("start of disconnectSocket...\n")
        try:
            self.socket.send(('q\n').encode('utf-8'))
            time.sleep(0.01) # wait for sending data and receiving ACK on ethernet
            self.socket.shutdown(SHUT_RDWR)
            self.socket.close()
            self.socket_flag = 1
        except:
            messagebox.showwarning("Warning", "please connect the ethernet socket firstly.")
            return -1
#        print("disconnectSocket\n")
        #self.status_var.set("disable the connection.")

    #----------------------------------------------------------------------------------------------------------------------------------------------------------
    def requestFrame(self):
        self.connectSocket()
        self.socket.send(('a\n').encode('utf-8'))
        self.disconnectSocket()        

    #----------------------------------------------------------------------------------------------------------------------------------------------------------
    def setExposure(self):
        self.connectSocket()
        self.socket.send(('c{}\n'.format(self.exposureEntry.get())).encode('utf-8'))
        self.disconnectSocket()        

    #----------------------------------------------------------------------------------------------------------------------------------------------------------
    def captureFrame(self):
        #master.status_var.set("Receiving Frame...")
        self.connectSocket()
        try:
##            recv_start=time.time()
            recv_pre = self.socket.recv(1024) # clear receive buffer before sending image capture control
##            recv_end=time.time()
##            print("captureFrame receive: \n%s\n" % str(recv_pre))
##            print("receiving time: %f" % (recv_end-recv_start)) ## nearly none
#            self.soc.send(('f\n').encode('utf-8'))
##            print("captureFrame send succeed\n")
#            time.sleep(0.005)
#            self.dataReceive()
        except OSError as msg:
            if str(msg) == "timed out":
                pass
            else:
                messagebox.showwarning("Warning", "please connect the ethernet socket firstly.")
                return -1
        
        self.socket.send(('x\n').encode('utf-8'))
        time.sleep(0.005)
        #print("{}".format(str(self.soc.recv(1024))).replace("\x00",""))
        self.dataReceive()
        self.disconnectSocket()
        self.plotImage()
        
#        print("captureFrame\n")

        
    #----------------------------------------------------------------------------------------------------------------------------------------------------------
    def dataReceive(self):
        package_counter = 0
        self.recv_data = bytearray()
        recv_start = time.time()
        while(package_counter<2048):
            try:
                self.recv_data.extend(bytearray(self.socket.recv(1024)))
                #print("{}_{}".format(package_counter, len(self.recv_data)))
            except:
                package_counter -= 1
#            print(recv_counter)
            package_counter += 1
        recv_end = time.time()
        print("Done, data received: {} Byte/{} Packages in {}s".format(len(self.recv_data),package_counter,recv_end-recv_start))
        #messagebox.showwarning("Done, data received: {} Byte/{} Packages in {}s".format(len(self.recv_data),package_counter,recv_end-recv_start))
#       print("dataReceive\n")
        


    #----------------------------------------------------------------------------------------------------------------------------------------------------------
    def plotImage(self):
        row = IMAGE["ROW"]
        column = IMAGE["COLUMN"]
        try:
            image_frame_array = list(self.recv_data)
            self.captureFlag = 1
        except:
            messagebox.showwarning("Warning", "please capture image firstly.")
            return -1
        i = 0
        for image_frame_pixel in image_frame_array:
            image_frame_array[i] = image_frame_pixel
            i += 1
        if len(image_frame_array) < row*column: 
            # if pixel number less than defined size, refill with zero
            for i in range(0, row*column-len(image_frame_array)):
                image_frame_array.append(0)
        
        # correct electrical noise        
        self.image_frame_nparray = np.resize(image_frame_array, (row,column))
        m=np.mean(self.image_frame_nparray[:,0:15],axis=1)
        #print(m)
        c=self.image_frame_nparray-m.reshape(1024,1)

        self.outputData = c

        print("update plot")

        self.outputImageGrey.clear()
        self.outputImageGrey.set_title("raw frame")
        self.outputImageGrey.imshow(self.outputData)
        self.canvas.draw()

#        plt.figure(1)
#        plt.imshow(self.image_frame_nparray, cmap='gray')
#        plt.show()
        
        
    #----------------------------------------------------------------------------------------------------------------------------------------------------------
    def plotAnimate(self, i):
#        # test plot for animation
#        graph_data = open("sampleText.txt", "r").read()
#        lines = graph_data.split("\n")
#        xs = []
#        ys = []
#        for line in lines:
#            if len(line) > 1:
#                x, y = line.split(",")
#                xs.append(float(x))
#                ys.append(float(y))
#        self.a.clear()
#        self.a.plot(xs, ys)
        self.outputImageGrey.clear()
        self.outputImageGrey.set_title("image frame (grey)")
        self.outputImageGrey.imshow(self.outputData, cmap='gray', interpolation='nearest', aspect='auto')
 
    #----------------------------------------------------------------------------------------------------------------------------------------------------------    
    def savePlace(self):
        self.path = askdirectory()
        self.saveplace_var.set(self.path)
#        print("savePlace\n")
        self.savePlace_flag = 1
           
    #----------------------------------------------------------------------------------------------------------------------------------------------------------
    def saveFrame(self):
        if self.savePlace_flag == 0:
            messagebox.showwarning("Warning", "Please select location to save image log data file.")
            return -1
        elif self.savePlace_flag == 1:
            #master.status_var.set("Saving Frame...")
            self.timestamp = time.strftime("%y%m%d_%H%M%S")
            self.filename = "log_{}.txt".format(self.timestamp)
            self.recv_file = open(self.path + '/' + self.filename, 'w')
            recvThread = threading.Thread(target=self.translate2html)
#            testrunThread = threading.Thread(target=self.testRunning)
            recvThread.start()

    #----------------------------------------------------------------------------------------------------------------------------------------------------------            
    def translate2html(self):
        # Log file Header -----------------------------------------------------------------
        text_translate = "<HEAD>\n"
        text_translate += "<TMSTMP>{}</TMSTMP>\n".format(self.timestamp)
        text_translate += "<NROWS>{}</NROWS>\n".format(1024)
        text_translate += "<NCOLS>{}</NCOLS>\n".format(2048)
        text_translate += "<EXP>{}</EXP>\n".format(self.exposureEntry.get())
        text_translate += "</HEAD>\n"

        # Log file Data -------------------------------------------------------------------
        text_translate += "<DATA>\n"
        for row in range(1024):
            text_translate += "<ROW n={}>".format(row)
            for col in range(2048):
                try:
                    text_translate += str(self.recv_data[col+row*2048])+"," #str(ord(self.recv_data[col+row*2048]))+","
                except:
                    print(row)
                    print(col)
            text_translate = text_translate[:-1]
            text_translate += "</ROW>\n"
        text_translate += "</DATA>\n"
        self.recv_file.write(text_translate)
        #master.status_var.set("Frame saved as {}".format(self.filename))
        self.recv_file.close()
        
    #----------------------------------------------------------------------------------------------------------------------------------------------------------    
    def testRunning(self):
        for i in range(30):
            print(i)
            time.sleep(0.5)
    
    #----------------------------------------------------------------------------------------------------------------------------------------------------------
    def testFunction(self):
#        print("that is ok.\n")
        print("testFunction\n")
        
    #----------------------------------------------------------------------------------------------------------------------------------------------------------
    def doNothing(self):
        print("doNothing")

#= Settings ===================================================================================================================================================
class P2_Settings(tk.Frame):

    def __init__(self, parent, master):
        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text="Settings", font=LARGE_FONT)
        label.pack(pady=10,padx=10)
        
#= Spectral Image ===================================================================================================================================================
class P3_Image(tk.Frame):
    def __init__(self, parent, master):
        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text="Spectral Image", font=LARGE_FONT)
        label.pack(pady=10,padx=10)


        self.socket_flag = 1 # flag of ethernet socket
        self.savePlace_flag = 0
        self.captureFlag = 0
        self.exposure = 100

        mat = scipy.io.loadmat('C:\\python_workspace\\Ethernet_2\\calib.mat')
        self.wl = np.array(mat['wl'])
        self.Mc = np.array(mat['Mc'])

        # -------- Control --------------------------------------------------------------    
        controlFrame = tk.Frame(self)
        controlFrame.pack(side=TOP,fill=X)

        # -------- Exposure -------------------------------------------------------------
        exposureFrame = tk.Frame(controlFrame)
        exposureFrame.pack(side=LEFT,fill=Y)
        exposureSetButton = ttk.Button(exposureFrame, text="Exposure Time", command=self.setExposure)
        exposureSetButton.pack(side=BOTTOM)
        self.exposureEntry = Entry(exposureFrame)
        self.exposureEntry.pack(side=TOP)
        self.exposureEntry.insert(0, "100")

        # -------- Request --------------------------------------------------------------    
        #imageReqButton = ttk.Button(self, text="Request", command=self.requestFrame)
        #imageReqButton.pack()
        reqFrame = tk.Frame(controlFrame)
        reqFrame.pack(side=LEFT,fill=Y)
        imageButton = ttk.Button(reqFrame, text="Request Frame", command=self.captureFrame)
        imageButton.pack(side=LEFT,fill=Y)

        # ------- Save --------
        saveFrame = tk.Frame(controlFrame)
        saveFrame.pack(side=RIGHT)        
        saveButton = ttk.Button(saveFrame, text="Save", command=self.saveFrame)
        saveButton.grid(row=2, column=1, ipadx=10)
        saveplaceButton = ttk.Button(saveFrame, text="Path", command=self.savePlace)
        saveplaceButton.grid(row=2, column=2, ipadx=10)
        self.saveplace_var = tk.StringVar()   
        self.saveplace_var.set("Select save location")
        saveplaceLabel = Label(saveFrame, textvariable=self.saveplace_var)
        saveplaceLabel.grid(row=1, column=1, columnspan=2)
  
        #outputButton = ttk.Button(self, text="Plot", command=self.plotImage)
        #outputButton.pack()

        # -------- Image --------------------------------------------------------------    
        self.outputData = np.zeros((IMAGE["ROW"], IMAGE["COLUMN"])) # initial
        self.outputFigure = Figure(figsize=(5,5), dpi=100)
        self.outputImageGrey = self.outputFigure.add_subplot(111)

        self.outputImageGrey.set_title("raw frame")
        self.outputImageGrey.imshow(self.outputData, cmap='gray', interpolation='nearest', aspect='auto')
        
        self.canvas = FigureCanvasTkAgg(self.outputFigure, self)        
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=BOTTOM, fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2Tk(self.canvas, self)
        toolbar.update()
        self.canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)        
                
        # following paremeter
   
    #----------------------------------------------------------------------------------------------------------------------------------------------------------
    def connectSocket(self):
        self.socket = socket(AF_INET, SOCK_STREAM)
        try:
            self.socket.connect((ETHERNET["IP"], ETHERNET["PORT"]))
            self.socket.settimeout(0.005)
            self.socket_flag = 2
        except:
            messagebox.showwarning("Warning", "there is already an connection.")
            return -1
        #self.status_var.set("Connection has been set.")
    
    #----------------------------------------------------------------------------------------------------------------------------------------------------------
    def disconnectSocket(self):
#       print("start of disconnectSocket...\n")
        try:
            self.socket.send(('q\n').encode('utf-8'))
            time.sleep(0.01) # wait for sending data and receiving ACK on ethernet
            self.socket.shutdown(SHUT_RDWR)
            self.socket.close()
            self.socket_flag = 1
        except:
            messagebox.showwarning("Warning", "please connect the ethernet socket firstly.")
            return -1
#        print("disconnectSocket\n")
        #self.status_var.set("disable the connection.")        

    #----------------------------------------------------------------------------------------------------------------------------------------------------------
    def setExposure(self):
        self.connectSocket()
        self.socket.send(('c{}\n'.format(self.exposureEntry.get())).encode('utf-8'))
        self.disconnectSocket()        

    #----------------------------------------------------------------------------------------------------------------------------------------------------------
    def captureFrame(self):
        #master.status_var.set("Receiving Frame...")
        self.connectSocket()
        try:
##            recv_start=time.time()
            recv_pre = self.socket.recv(1024) # clear receive buffer before sending image capture control
##            recv_end=time.time()
##            print("captureFrame receive: \n%s\n" % str(recv_pre))
##            print("receiving time: %f" % (recv_end-recv_start)) ## nearly none
#            self.soc.send(('f\n').encode('utf-8'))
##            print("captureFrame send succeed\n")
#            time.sleep(0.005)
#            self.dataReceive()
        except OSError as msg:
            if str(msg) == "timed out":
                pass
            else:
                messagebox.showwarning("Warning", "please connect the ethernet socket firstly.")
                return -1
        
        self.socket.send(('x\n').encode('utf-8'))
        time.sleep(0.005)
        #print("{}".format(str(self.soc.recv(1024))).replace("\x00",""))
        self.dataReceive()
        self.disconnectSocket()
        self.plotImage()
        
#        print("captureFrame\n")

        
    #----------------------------------------------------------------------------------------------------------------------------------------------------------
    def dataReceive(self):
        package_counter = 0
        self.recv_data = bytearray()
        recv_start = time.time()
        while(package_counter<2048):
            try:
                self.recv_data.extend(bytearray(self.socket.recv(1024)))
                #print("{}_{}".format(package_counter, len(self.recv_data)))
            except:
                package_counter -= 1
#            print(recv_counter)
            package_counter += 1
        recv_end = time.time()
        print("Done, data received: {} Byte/{} Packages in {}s".format(len(self.recv_data),package_counter,recv_end-recv_start))
        #messagebox.showwarning("Done, data received: {} Byte/{} Packages in {}s".format(len(self.recv_data),package_counter,recv_end-recv_start))
#       print("dataReceive\n")
        


    #----------------------------------------------------------------------------------------------------------------------------------------------------------
    def plotImage(self):
        row = IMAGE["ROW"]
        column = IMAGE["COLUMN"]
        try:
            image_frame_array = list(self.recv_data)
            self.captureFlag = 1
        except:
            messagebox.showwarning("Warning", "please capture image firstly.")
            return -1
        i = 0
        for image_frame_pixel in image_frame_array:
            image_frame_array[i] = image_frame_pixel
            i += 1
        if len(image_frame_array) < row*column: 
            # if pixel number less than defined size, refill with zero
            for i in range(0, row*column-len(image_frame_array)):
                image_frame_array.append(0)
        
        # correct electrical noise        
        self.image_frame_nparray = np.resize(image_frame_array, (row,column))
        m=np.mean(self.image_frame_nparray[:,0:15],axis=1)
        #print(m)
        c=self.image_frame_nparray-m.reshape(1024,1)

        # correction matrix
        v = list()
        b = list()
        for col in range(2048):
            for bin in range(128):
                try:
                    p1 = 1+bin*8
                    p2 = 7+bin*8
                    b.append(np.mean(c[p1:p2,col]))
                except:
                    print("start end")
                    print(p1)
                    print(p2)
            k = np.array(b)
            b = list()
            try:
                v.append(list(np.dot(self.Mc,k)))
            except:
                print('Append')
                print(bin)
                print(col)
                print(len(k))
        w = np.array(v)
        w.reshape(100,2048)
        w = np.rot90(w);
        self.outputData = w

        print("update plot")

        self.outputImageGrey.clear()
        self.outputImageGrey.set_title("raw frame")
        self.outputImageGrey.imshow(self.outputData)
        self.canvas.draw()

#        plt.figure(1)
#        plt.imshow(self.image_frame_nparray, cmap='gray')
#        plt.show()
        
        
    #----------------------------------------------------------------------------------------------------------------------------------------------------------
    def plotAnimate(self, i):
#        # test plot for animation
#        graph_data = open("sampleText.txt", "r").read()
#        lines = graph_data.split("\n")
#        xs = []
#        ys = []
#        for line in lines:
#            if len(line) > 1:
#                x, y = line.split(",")
#                xs.append(float(x))
#                ys.append(float(y))
#        self.a.clear()
#        self.a.plot(xs, ys)
        self.outputImageGrey.clear()
        self.outputImageGrey.set_title("image frame (grey)")
        self.outputImageGrey.imshow(self.outputData, cmap='gray', interpolation='nearest', aspect='auto')
 
    #----------------------------------------------------------------------------------------------------------------------------------------------------------    
    def savePlace(self):
        self.path = askdirectory()
        self.saveplace_var.set(self.path)
#        print("savePlace\n")
        self.savePlace_flag = 1
           
    #----------------------------------------------------------------------------------------------------------------------------------------------------------
    def saveFrame(self):
        if self.savePlace_flag == 0:
            messagebox.showwarning("Warning", "Please select location to save image log data file.")
            return -1
        elif self.savePlace_flag == 1:
            #master.status_var.set("Saving Frame...")
            self.timestamp = time.strftime("%y%m%d_%H%M%S")
            self.filename = "log_{}.txt".format(self.timestamp)
            self.recv_file = open(self.path + '/' + self.filename, 'w')
            recvThread = threading.Thread(target=self.translate2html)
#            testrunThread = threading.Thread(target=self.testRunning)
            recvThread.start()

    #----------------------------------------------------------------------------------------------------------------------------------------------------------            
    def translate2html(self):
        # Log file Header -----------------------------------------------------------------
        text_translate = "<HEAD>\n"
        text_translate += "<TMSTMP>{}</TMSTMP>\n".format(self.timestamp)
        text_translate += "<NROWS>{}</NROWS>\n".format(1024)
        text_translate += "<NCOLS>{}</NCOLS>\n".format(2048)
        text_translate += "<EXP>{}</EXP>\n".format(self.exposureEntry.get())
        text_translate += "</HEAD>\n"

        # Log file Data -------------------------------------------------------------------
        text_translate += "<DATA>\n"
        for row in range(1024):
            text_translate += "<ROW n={}>".format(row)
            for col in range(2048):
                try:
                    text_translate += str(self.recv_data[col+row*2048])+"," #str(ord(self.recv_data[col+row*2048]))+","
                except:
                    print(row)
                    print(col)
            text_translate = text_translate[:-1]
            text_translate += "</ROW>\n"
        text_translate += "</DATA>\n"
        self.recv_file.write(text_translate)
        #master.status_var.set("Frame saved as {}".format(self.filename))
        self.recv_file.close()

#= Spectrum ===================================================================================================================================================
class P4_Spectrum(tk.Frame):
    def __init__(self, parent, master):
        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text="Spectral Characteristics", font=LARGE_FONT)
        label.pack(pady=10,padx=10)


        self.socket_flag = 1 # flag of ethernet socket
        self.savePlace_flag = 0
        self.captureFlag = 0
        self.exposure = 100

        mat = scipy.io.loadmat('C:\\python_workspace\\Ethernet_2\\calib.mat')
        self.wl = np.array(mat['wl'])
        self.Mc = np.array(mat['Mc'])

        # -------- Control --------------------------------------------------------------    
        controlFrame = tk.Frame(self)
        controlFrame.pack(side=TOP,fill=X)

        # -------- Exposure -------------------------------------------------------------
        exposureFrame = tk.Frame(controlFrame)
        exposureFrame.pack(side=LEFT,fill=Y)
        exposureSetButton = ttk.Button(exposureFrame, text="Exposure Time", command=self.setExposure)
        exposureSetButton.pack(side=BOTTOM)
        self.exposureEntry = Entry(exposureFrame)
        self.exposureEntry.pack(side=TOP)
        self.exposureEntry.insert(0, "100")

        # -------- Request --------------------------------------------------------------    
        #imageReqButton = ttk.Button(self, text="Request", command=self.requestFrame)
        #imageReqButton.pack()
        reqFrame = tk.Frame(controlFrame)
        reqFrame.pack(side=LEFT,fill=Y)
        imageButton = ttk.Button(reqFrame, text="Request Frame", command=self.captureFrame)
        imageButton.pack(side=LEFT,fill=Y)
        outputButton = ttk.Button(reqFrame, text="Plot", command=self.plotImage)
        outputButton.pack(side=LEFT,fill=Y)


        # ------- Save --------
        saveFrame = tk.Frame(controlFrame)
        saveFrame.pack(side=RIGHT)        
        saveButton = ttk.Button(saveFrame, text="Save", command=self.saveFrame)
        saveButton.grid(row=2, column=1, ipadx=10)
        saveplaceButton = ttk.Button(saveFrame, text="Path", command=self.savePlace)
        saveplaceButton.grid(row=2, column=2, ipadx=10)
        self.saveplace_var = tk.StringVar()   
        self.saveplace_var.set("Select save location")
        saveplaceLabel = Label(saveFrame, textvariable=self.saveplace_var)
        saveplaceLabel.grid(row=1, column=1, columnspan=2)
  

        # -------- Image --------------------------------------------------------------    
        self.outputData = np.zeros((IMAGE["ROW"], IMAGE["COLUMN"])) # initial
        self.outputFigure = Figure(figsize=(5,5), dpi=100)
        self.outputImageGrey = self.outputFigure.add_subplot(111)

        self.outputImageGrey.set_title("raw frame")
        self.outputImageGrey.imshow(self.outputData, cmap='gray', interpolation='nearest', aspect='auto')
        
        self.canvas = FigureCanvasTkAgg(self.outputFigure, self)        
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=BOTTOM, fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2Tk(self.canvas, self)
        toolbar.update()
        self.canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)        
                
        # following paremeter
   
    #----------------------------------------------------------------------------------------------------------------------------------------------------------
    def connectSocket(self):
        self.socket = socket(AF_INET, SOCK_STREAM)
        try:
            self.socket.connect((ETHERNET["IP"], ETHERNET["PORT"]))
            self.socket.settimeout(0.005)
            self.socket_flag = 2
        except:
            messagebox.showwarning("Warning", "there is already an connection.")
            return -1
        #self.status_var.set("Connection has been set.")
    
    #----------------------------------------------------------------------------------------------------------------------------------------------------------
    def disconnectSocket(self):
#       print("start of disconnectSocket...\n")
        try:
            self.socket.send(('q\n').encode('utf-8'))
            time.sleep(0.01) # wait for sending data and receiving ACK on ethernet
            self.socket.shutdown(SHUT_RDWR)
            self.socket.close()
            self.socket_flag = 1
        except:
            messagebox.showwarning("Warning", "please connect the ethernet socket firstly.")
            return -1
#        print("disconnectSocket\n")
        #self.status_var.set("disable the connection.")        

    #----------------------------------------------------------------------------------------------------------------------------------------------------------
    def setExposure(self):
        self.connectSocket()
        self.socket.send(('c{}\n'.format(self.exposureEntry.get())).encode('utf-8'))
        self.disconnectSocket()        

    #----------------------------------------------------------------------------------------------------------------------------------------------------------
    def captureFrame(self):
        #master.status_var.set("Receiving Frame...")
        self.connectSocket()
        try:
##            recv_start=time.time()
            recv_pre = self.socket.recv(1024) # clear receive buffer before sending image capture control
##            recv_end=time.time()
##            print("captureFrame receive: \n%s\n" % str(recv_pre))
##            print("receiving time: %f" % (recv_end-recv_start)) ## nearly none
#            self.soc.send(('f\n').encode('utf-8'))
##            print("captureFrame send succeed\n")
#            time.sleep(0.005)
#            self.dataReceive()
        except OSError as msg:
            if str(msg) == "timed out":
                pass
            else:
                messagebox.showwarning("Warning", "please connect the ethernet socket firstly.")
                return -1
        
        self.socket.send(('x\n').encode('utf-8'))
        time.sleep(0.005)
        #print("{}".format(str(self.soc.recv(1024))).replace("\x00",""))
        self.dataReceive()
        self.disconnectSocket()
        
#        print("captureFrame\n")

        
    #----------------------------------------------------------------------------------------------------------------------------------------------------------
    def dataReceive(self):
        package_counter = 0
        self.recv_data = bytearray()
        recv_start = time.time()
        while(package_counter<2048):
            try:
                self.recv_data.extend(bytearray(self.socket.recv(1024)))
                #print("{}_{}".format(package_counter, len(self.recv_data)))
            except:
                package_counter -= 1
#            print(recv_counter)
            package_counter += 1
        recv_end = time.time()
        print("Done, data received: {} Byte/{} Packages in {}s".format(len(self.recv_data),package_counter,recv_end-recv_start))
        #messagebox.showwarning("Done, data received: {} Byte/{} Packages in {}s".format(len(self.recv_data),package_counter,recv_end-recv_start))
#       print("dataReceive\n")
        


    #----------------------------------------------------------------------------------------------------------------------------------------------------------
    def plotImage(self):
        row = IMAGE["ROW"]
        column = IMAGE["COLUMN"]
        try:
            image_frame_array = list(self.recv_data)
            self.captureFlag = 1
        except:
            messagebox.showwarning("Warning", "please capture image firstly.")
            return -1
        i = 0
        for image_frame_pixel in image_frame_array:
            image_frame_array[i] = image_frame_pixel
            i += 1
        if len(image_frame_array) < row*column: 
            # if pixel number less than defined size, refill with zero
            for i in range(0, row*column-len(image_frame_array)):
                image_frame_array.append(0)
        
        # correct electrical noise        
        self.image_frame_nparray = np.resize(image_frame_array, (row,column))
        m=np.mean(self.image_frame_nparray[:,0:15],axis=1)
        #print(m)
        c=self.image_frame_nparray-m.reshape(1024,1)

        # correction matrix
        v = list()
        b = list()
        for col in range(2048):
            for bin in range(128):
                try:
                    p1 = 1+bin*8
                    p2 = 7+bin*8
                    b.append(np.mean(c[p1:p2,col]))
                except:
                    print("start end")
                    print(p1)
                    print(p2)
            k = np.array(b)
            b = list()
            try:
                v.append(list(np.dot(self.Mc,k)))
            except:
                print('Append')
                print(bin)
                print(col)
                print(len(k))
        w = np.array(v)
        w.reshape(100,2048)
        self.outputData = w[500,:]
        w2 = list(self.outputData)
        u = list(self.wl[0])
        print("update plot")

        self.outputImageGrey.clear()
        self.outputImageGrey.set_title("raw frame")
        self.outputImageGrey.plot(u,w2)
        self.canvas.draw()

#        plt.figure(1)
#        plt.imshow(self.image_frame_nparray, cmap='gray')
#        plt.show()
        
        
    #----------------------------------------------------------------------------------------------------------------------------------------------------------
    def plotAnimate(self, i):
#        # test plot for animation
#        graph_data = open("sampleText.txt", "r").read()
#        lines = graph_data.split("\n")
#        xs = []
#        ys = []
#        for line in lines:
#            if len(line) > 1:
#                x, y = line.split(",")
#                xs.append(float(x))
#                ys.append(float(y))
#        self.a.clear()
#        self.a.plot(xs, ys)
        self.outputImageGrey.clear()
        self.outputImageGrey.set_title("image frame (grey)")
        self.outputImageGrey.imshow(self.outputData, cmap='gray', interpolation='nearest', aspect='auto')
 
    #----------------------------------------------------------------------------------------------------------------------------------------------------------    
    def savePlace(self):
        self.path = askdirectory()
        self.saveplace_var.set(self.path)
#        print("savePlace\n")
        self.savePlace_flag = 1
           
    #----------------------------------------------------------------------------------------------------------------------------------------------------------
    def saveFrame(self):
        if self.savePlace_flag == 0:
            messagebox.showwarning("Warning", "Please select location to save image log data file.")
            return -1
        elif self.savePlace_flag == 1:
            #master.status_var.set("Saving Frame...")
            self.timestamp = time.strftime("%y%m%d_%H%M%S")
            self.filename = "log_{}.txt".format(self.timestamp)
            self.recv_file = open(self.path + '/' + self.filename, 'w')
            recvThread = threading.Thread(target=self.translate2html)
#            testrunThread = threading.Thread(target=self.testRunning)
            recvThread.start()

    #----------------------------------------------------------------------------------------------------------------------------------------------------------            
    def translate2html(self):
        # Log file Header -----------------------------------------------------------------
        text_translate = "<HEAD>\n"
        text_translate += "<TMSTMP>{}</TMSTMP>\n".format(self.timestamp)
        text_translate += "<NROWS>{}</NROWS>\n".format(1024)
        text_translate += "<NCOLS>{}</NCOLS>\n".format(2048)
        text_translate += "<EXP>{}</EXP>\n".format(self.exposure)
        text_translate += "</HEAD>\n"

        # Log file Data -------------------------------------------------------------------
        text_translate += "<DATA>\n"
        for row in range(1024):
            text_translate += "<ROW n={}>".format(row)
            for col in range(2048):
                try:
                    text_translate += str(self.recv_data[col+row*2048])+"," #str(ord(self.recv_data[col+row*2048]))+","
                except:
                    print(row)
                    print(col)
            text_translate = text_translate[:-1]
            text_translate += "</ROW>\n"
        text_translate += "</DATA>\n"
        self.recv_file.write(text_translate)
        #master.status_var.set("Frame saved as {}".format(self.filename))
        self.recv_file.close()



#= Main =======================================================================================================================================================
if __name__ == '__main__':
    # ---- Window ----
    app = App()
    app.mainloop()
