# -*- coding: utf-8 -*-
"""
Created on Fri Dec  7 15:19:02 2018

@author: jin

note:
    %matplotlib auto # type in sypder IPython console to have an independent plot gui
"""

import copy
import numpy as np
import scipy
import time
import math


from skimage import data,filters,color
from matplotlib import style
import matplotlib.pyplot as plt
style.use("ggplot")
from sklearn import svm, metrics #Import scikit-learn metrics module for accuracy calculation
from sklearn.preprocessing import MinMaxScaler
# Import train_test_split function
from sklearn.model_selection import train_test_split
from sklearn.externals import joblib

"""
Seven grayscale conversion algorithms (with pseudocode and VB6 source code)
http://www.tannerhelland.com/3643/grayscale-image-algorithm-vb6/ method one

https://blog.csdn.net/shaw820/article/details/72716976
"""
def greyscale(data1, data2):
    data_grey = (data1+data2)/2
    return data_grey.astype(int)

def entropy(data1, data2):
    data = greyscale(data1, data2)
    tmp = []
    for i in range(256):
        tmp.append(0)
    val = 0
    k = 0
    ent = 0 # entropy
    asm = 0 # energy
    for i in range(len(data)):
        for j in range(len(data[i])):
            val = data[i][j]
            tmp[val] = float(tmp[val] + 1)
            k =  float(k + 1)
    for i in range(len(tmp)):
        tmp[i] = float(tmp[i] / k)
    for i in range(len(tmp)):
        if(tmp[i] == 0):
            ent = ent
        else:
            ent = float(ent - tmp[i] * (math.log(tmp[i]) / math.log(2.0)))
        asm += tmp[i]**2
    return ent, asm

def eigen_extraction(data1, data2, label=0, d_x=100, d_y=50):
    if data1.shape == data2.shape:
        n_x = int(np.ceil(data1.shape[1]/d_x)) # number of interval in horizontal axis
        n_y = int(np.ceil(data1.shape[0]/d_y)) # number of interval in vertical axis
        data1_eigen = np.zeros((n_x*n_y,11))
        for i in range(n_y): # i: vertical, j: horizontal
            for j in range(n_x):
                data1_eigen[i*n_x+j,0] = i
                data1_eigen[i*n_x+j,1] = j
                data1_eigen[i*n_x+j,2] = label
                
                data1_eigen[i*n_x+j,3] = np.average(data1[i*d_y:(i+1)*d_y,j*d_x:(j+1)*d_x]) # 1st order, average of block
                data1_eigen[i*n_x+j,4] = np.std(data1[i*d_y:(i+1)*d_y,j*d_x:(j+1)*d_x]) # 2nd order, standard deviation
                data1_eigen[i*n_x+j,5] = scipy.stats.skew(data1[i*d_y:(i+1)*d_y,j*d_x:(j+1)*d_x].ravel()) # 3rd order, skewness
                
                data1_eigen[i*n_x+j,6] = np.average(data2[i*d_y:(i+1)*d_y,j*d_x:(j+1)*d_x]) # 1st order, average of block
                data1_eigen[i*n_x+j,7] = np.std(data2[i*d_y:(i+1)*d_y,j*d_x:(j+1)*d_x]) # 2nd order, standard deviation
                data1_eigen[i*n_x+j,8] = scipy.stats.skew(data2[i*d_y:(i+1)*d_y,j*d_x:(j+1)*d_x].ravel()) # 3rd order, skewness
                
                data1_eigen[i*n_x+j,9] = entropy(data1[i*d_y:(i+1)*d_y,j*d_x:(j+1)*d_x], data2[i*d_y:(i+1)*d_y,j*d_x:(j+1)*d_x])[0] # entropy
                data1_eigen[i*n_x+j,10] = entropy(data1[i*d_y:(i+1)*d_y,j*d_x:(j+1)*d_x], data2[i*d_y:(i+1)*d_y,j*d_x:(j+1)*d_x])[1] # entropy
                
        return data1_eigen
                
    else:
        print("error[eigen_extraction]: the sizes of data1 and data2 do not match!")
        return False

"""
if label2 is formed by same element, input label2 as one variable and set flag to 1
"""    
def accuracy(label1,label2, flag=0):
    if flag==0:
        if len(label1) == len(label2):
            counter = 0
            for i in range(len(label1)):
                if label1[i]!=label2[i]:
                    counter += 1
            return 1-counter/len(label1)
        else: 
            print("error[accuracy] 1: the sizes of label1 and label2 do not match!")
    else:
        if isinstance(int(label2), int):
            counter = 0
            for i in range(len(label1)):
                if label1[i]!=label2:
                    counter += 1
            return 1-counter/len(label1)
        else:
            print("error[accuracy] 2: the sizes of label1 and label2 do not match!")
    
        
def cross_validation(file_no, clf, mix_flag=0):
    global file_900_set, file_970_set
    d_x=100
    d_y=50
    data_900_name = file_900_set[file_no]
    data_970_name = file_970_set[file_no]
    data_900 = np.load(data_900_name, mmap_mode='r')
    data_970 = np.load(data_970_name, mmap_mode='r')
    if mix_flag == 0:
        data_label = int(data_900_name.split("_")[0])
    else:
        data_label = -1
    data_eigen_temp = eigen_extraction(data_900, data_970, label=data_label)
    data_eigen_temp[:,3:] = scaler.fit_transform(data_eigen_temp[:,3:])
    y_pred = clf.predict(data_eigen_temp[:,3:])
    
    n_x = int(np.ceil(data_900.shape[1]/d_x))
    n_y = int(np.ceil(data_900.shape[0]/d_y))
    
    a=y_pred.reshape((n_x,n_y))
    a_a = copy.copy(a)
    if mix_flag == 0:
        accuray_wo = accuracy(a.flatten(),data_label,1)
    plt.figure()
    plt.imshow(a, plt.cm.gray)
    plt.title("IMG block predict - without correction function ")
    plt.show()
    
    b=correction(y_pred, n_x, n_y).reshape(n_x,n_y)
    if mix_flag == 0:
        accuray_w = accuracy(b.flatten(),data_label,1)
    plt.figure()
    plt.imshow(b, plt.cm.gray)
    plt.title("IMG block predict - correction function ")
    plt.show()
    
    if mix_flag == 0:
        print("cross_validation without correction: %0.2f%%" %(accuray_wo*100))
        print("cross_validation with correction: %0.2f%%" %(accuray_w*100))
    
        return accuray_wo, accuray_w, a_a, b
    else:
        return "mix material validation", a_a, b
    
    

"""
correcting predict label in whole pic
algorithm:
    default 1st and last column and row are correct
    e.g. 
        1  1  1           1  1  1
        1  x  1   --->    1  1  1
        1  2  1           1  2  1
        (if >=6 out of 8 surrounding label marker is same (1), change the center x to 1)
    
"""
def correction(label_pred, n_x, n_y):
    if len(label_pred) == n_x*n_y:
        label_mat = label_pred.reshape((n_y, n_x))
        label_most = np.argmax([np.count_nonzero(label_pred==0), np.count_nonzero(label_pred==1), np.count_nonzero(label_pred==2)]) # most likely label
        for i in range(1, n_y-1): # row
            for j in range(1, n_x-1): # column
                temp_mat = [label_mat[i-1,j-1],label_mat[i-1,j],label_mat[i-1,j+1], label_mat[i,j-1], -1, label_mat[i,j+1], label_mat[i+1,j-1],label_mat[i+1,j],label_mat[i+1,j+1]] 
                temp_mat_most = np.argmax([temp_mat.count(0), temp_mat.count(1), temp_mat.count(2)]) # find most label 0, 1, 2 in the surrounding area
                temp_mat_most_num = temp_mat.count(temp_mat_most) # number of most label
                if label_mat[i,j]!=temp_mat_most and temp_mat_most_num>=6:
                    label_mat[i,j] = temp_mat_most # correction
        return label_mat.flatten()
        
    else:
        print("error[correction]: the sizes of label1 and label2 do not match!")
            
## Main ===========
if __name__ == '__main__':    
    
    d_x=100 #default d_x=100, d_y=50 are better
    d_y=50
    file_900_set = ["0_sand_dry_900.npy", "0_sand_wet_900.npy", "1_concrete_dry_900.npy","1_concrete_wet_900.npy","2_bitumen_dry_900.npy","2_bitumen_wet_900.npy","2_bitumen_wet_900_1.npy", "sandconcrete_dry_900.npy"]
    file_970_set = ["0_sand_dry_970.npy", "0_sand_wet_970.npy", "1_concrete_dry_970.npy","1_concrete_wet_970.npy","2_bitumen_dry_970.npy","2_bitumen_wet_970.npy","2_bitumen_wet_970_1.npy", "sandconcrete_dry_970.npy"]
    material = ["sand", "concrete", "bitumen"]
    counter_file = 0
    data_eigen = np.array([])
    scaler = MinMaxScaler()  # Default behavior is to scale to [0,1]
    t1_eigen = time.time()
    for i in file_900_set[:-2]:
        data_900_name = file_900_set[counter_file]
        data_970_name = file_970_set[counter_file]
        data_900 = np.load(data_900_name, mmap_mode='r')
        data_970 = np.load(data_970_name, mmap_mode='r')
        data_label = int(data_900_name.split("_")[0])
        data_eigen_temp = eigen_extraction(data_900, data_970, label=data_label, d_x=d_x, d_y=d_y)
        data_eigen_temp[:,3:] = scaler.fit_transform(data_eigen_temp[:,3:])
        data_eigen = np.vstack((data_eigen, data_eigen_temp)) if data_eigen.size else data_eigen_temp
        counter_file += 1
    t2_eigen = time.time()
    print("time of eigenvalue extraction: %0.2fs" % (t2_eigen-t1_eigen))
    
    X_train, X_test, y_train, y_test = train_test_split(data_eigen[:], data_eigen[:], test_size=0.2)
     
    #C_2d_range = [1e-2, 1, 1e2]
    C_2d_range = np.logspace(-2, 2, 10)
    #gamma_2d_range = [1e-1, 1, 1e1]
    gamma_2d_range = np.logspace(-2, 2, 10)
    classifiers = []
    prediction_rate = 0
    
    print("processing...")
    for C in C_2d_range:
        for gamma in gamma_2d_range:
            #clf = svm.SVC(kernel='poly', C=C, gamma=gamma, degree=3)
            clf = svm.SVC(kernel='rbf', C=C, gamma=gamma, degree=3)
            t1_train = time.time()
            clf.fit(X_train[:,3:], y_train[:,2])
            t2_train = time.time()
            t1_pred = time.time()
            y_pred = clf.predict(X_test[:,3:])
            t2_pred = time.time()
            classifiers.append((C, gamma, clf))
            prediction_rate_temp = accuracy(y_test[:,2], y_pred)*100
            print("Accuracy: %0.2f%% (C=%s, gamma=%s) (training time:%0.2fs, prediction time:%0.2fs)" % (prediction_rate_temp, str(C), str(gamma), t2_train-t1_train, t2_pred-t1_pred))
            if prediction_rate_temp > prediction_rate:
                prediction_rate = prediction_rate_temp
                clf_max = clf
    
    joblib.dump(clf_max, 'clf_material.pkl') # save clf model
    
    clf3 = joblib.load('clf_material.pkl') # read clf model
    
    ## correcting label of whole pic
    #correction(label_pred, n_x=int(np.ceil(data_900.shape[1]/d_x)), n_y=int(np.ceil(data_900.shape[0]/d_y)), clf)
    cross_valid = cross_validation(1, clf3)
    