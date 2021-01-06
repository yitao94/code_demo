# -*- coding: utf-8 -*-
"""
Created on Fri Feb 21 09:55:16 2020

goal:
    analysis data between rcs supplier data and ground truth data

version 1 - 20200513:
    1. check compliance of flag code
    2. convert rcs/gt whole day compilation from .csv to df
    
note:

# TODO: should consider about mean() and all_positive_mean() 
# TODO: seek for confidence probability
    
    
@author: YITAJIN
"""

import os
import re
import timeit
import pandas as pd
from sklearn.metrics import confusion_matrix #confusion matrix

from src.setting import *
from src.tool import *
from src.posID import road_no
from src.sup.supDA import *

import matplotlib.pyplot as plt # for ploting <https://blog.csdn.net/qiurisiyu2016/article/details/80187177>
import seaborn as sns #data visulization
sns.set(style='ticks') # set initial matplot style

#from dirScreen import input_dirScreen_compilance_check

# for general case
area_code_list = ["bj", "n"] #area_code_list = ["bj", "n"] #area_code = "bj" # "BJ"
vehicle_code_list = ["c","e"] #vehicle_code_list = ["c", "e"] #vehicle_code = "c"
analysis_code_list = ["rt", "at", "rc"]

## for testing example
#rcs_code_exp= "KU"
#area_code_exp = "BJ"
#vehicle_code_exp = "C"

# filename pattern for gt_in_single_day.csv, e.g. 2019-12-17_Tuesday.csv
gt_single_csv_pattern = r'\d\d\d\d-\d\d-\d\d.*\.csv'

# testing for single day for converted
#gt_single_csv_addr = GT_WHOLEDAY_TEST_CONVERTED

# define how many valid value in one timestamp
gt_value_per_ts = 3
# define maximal distance for valid data matching, default <= 500m
GT_RCS_MAX_DIST = 500
# define maximal time difference in seconds for valid data matching, defalut is None
GT_RCS_MAX_TIME = 5*60

def gt_vs_rcs (gt_df, rcs_df, max_dist=GT_RCS_MAX_DIST, max_time=GT_RCS_MAX_TIME, extend_da_flag=False, temp_thre = 10):
    """
    func:
        1. read ground truth in single day to dataframe and its timestamp
        2. read rcs compilation to dataframe and its timestamp
        3. match timestamp in ground truth with nearest in rcs
        4. calculation average/ condition in ground truth per timestamp
        5. make comparison with gt vs. rcs
        6. return comparison result:
            - road temperature difference (RT_gt - RT_rcs)
            - road condition comparison (RC_rcs whether amond RC_gt)
            - ambient temperature difference (AT_gt - AT_rcs)
    
    note:
        # TODO: add customized analysis unit
    
    param:
        input:
            gt_df: ground truth data in df
            rcs_df: rcs data in df
            max_dist: maximal distance between gt points and corresponding rcs point, default GT_RCS_MAX_DIST
            max_time: maximal time difference between gt timestamp and corresponding rcs timestamp, default GT_RCS_MAX_TIME
            temp_thre : threshold of temperature can be accepted, default by True, with threshold of 10 degree celsius 
                - False: no threshold/ 0
                - True: with threshold of <1> degree celsius
                - positive float: with threshold of <x> degree celsius in abs() (reason: most likely to be outdoor)
            # TODO: extend_da_flag: flag of extended analysis, default is True for road temperature and road condition, extra needs extends data analysis
        output:
            gt_rcs_rt_diff: road temperature difference with ground truth and rcs in list
            gt_rcs_rt_diff: road condition difference with ground truth and rcs in list
            gt_rcs_at_diff: ambient temperature difference with ground truth and rcs in list
    """        
    gt_vs_rcs_start = timeit.default_timer()
    
    # read all columns of rcs compilation df in list 
    rcs_comp_ts = rcs_df.columns 
    # read all columns of gt compilation df in list 
    gt_single_ts = gt_df.columns
    # map timestamp from ground truth to rcs timestamp
    gt_single_ts_mapto_rcs = ts_a_mapto_b(gt_single_ts, rcs_comp_ts, max_time)
    
    # TODO: add out of time and distance range as exception
    # TODO: consider None or invalid gt case
    
    # road temperature difference between gt and rcs (RT_gt - RT_rcs)
    gt_rcs_rt_diff = []
    # ambient temperature difference between gt and rcs (AT_gt - AT_rcs)
    gt_rcs_at_diff = []
    # road condition difference between gt and rcs (RT_gt v.s. RT_rcs), return True or False
    gt_rcs_rc_diff = []
    
    # read index list in each timestamp of ground truth
    for gt_single_ts_index_i in range(len(gt_single_ts)):
        processbar (r"[analysing-ga10001] gt-in-single-day v.s. rcs-in-compilation - {:.2f}%".format(gt_single_ts_index_i/len(gt_single_ts)*100), time0=gt_vs_rcs_start, time1=timeit.default_timer())
        gt_single_ts_no_list = gt_df.loc[pd.notnull(gt_df[gt_single_ts[gt_single_ts_index_i]])].index # e.g.: Int64Index([1, 2, 537], dtype='int64', name='no')
        # temporary difference stored list for same ts in different location
        gt_rcs_rt_diff_temp = [] # road temperature
        gt_rcs_at_diff_temp = [] # ambient temperature # TODO: consider AT
        gt_rcs_rc_diff_temp = [] # road condition
        
        for gt_single_ts_no_list_i in gt_single_ts_no_list:
            # Done: content needs convert format into list from string
            gt_single_ts_no_list_i_content = gt_df.loc[gt_single_ts_no_list_i,gt_single_ts[gt_single_ts_index_i]] # '[[683.72167627  15.76459312  15.51328945   1.           2.        ]]'
            
            #Error control of eval(gt_element)
            try:
                gt_single_ts_no_list_i_content = eval(re.sub(" +", ",", gt_single_ts_no_list_i_content).replace("[[,","[[").replace(",]]","]]")) # [[683.72167627,15.76459312,15.51328945,1.,2.,]]
            except :
                print(gt_single_ts[gt_single_ts_index_i], gt_single_ts_no_list_i, gt_single_ts_no_list_i_content)
                raise Exception
                
            gt_single_ts_no_list_i_dist = gt_single_ts_no_list_i_content[0][0]
            gt_single_ts_no_list_i_rt_r = gt_single_ts_no_list_i_content[0][1] # road temperature on right
            gt_single_ts_no_list_i_rt_l = gt_single_ts_no_list_i_content[0][2] # road temperature on left
            gt_single_ts_no_list_i_rc_r = gt_single_ts_no_list_i_content[0][3] # road condition on right
            gt_single_ts_no_list_i_rc_l = gt_single_ts_no_list_i_content[0][4] # road condition on left 
            
            if (gt_single_ts_no_list_i_dist<=max_dist):
                if (gt_single_ts_no_list_i_rt_r!=None or gt_single_ts_no_list_i_rt_l!=None): # at least one valid element in right or left
                    if (gt_single_ts_no_list_i_rt_r == None): # gt_single_ts_no_list_i_rt_l: valid 
                        gt_single_ts_no_list_i_rt_aver = gt_single_ts_no_list_i_rt_l
                    elif (gt_single_ts_no_list_i_rt_l == None): # gt_single_ts_no_list_i_rt_r: valid 
                        gt_single_ts_no_list_i_rt_aver = gt_single_ts_no_list_i_rt_r
                    else: # both valid
                        gt_single_ts_no_list_i_rt_aver = (gt_single_ts_no_list_i_rt_r+gt_single_ts_no_list_i_rt_l)/2
                else:
                    continue # jump to next turn in the loop if road temperature is invaild in both gt marwis
                
                # same logic with road temperature, but return in list
                if (gt_single_ts_no_list_i_rc_r!=None or gt_single_ts_no_list_i_rc_l!=None): 
                    if (gt_single_ts_no_list_i_rc_r == None): # gt_single_ts_no_list_i_rt_l: valid 
                        gt_single_ts_no_list_i_rc_comp = [GT_STRUC_SIG["RC_MAP"][gt_single_ts_no_list_i_rc_l]]
                    elif (gt_single_ts_no_list_i_rc_l == None): # gt_single_ts_no_list_i_rt_r: valid 
                        gt_single_ts_no_list_i_rc_comp = [GT_STRUC_SIG["RC_MAP"][gt_single_ts_no_list_i_rc_r]]
                    else: # both valid
                        gt_single_ts_no_list_i_rc_comp = [GT_STRUC_SIG["RC_MAP"][gt_single_ts_no_list_i_rc_r], GT_STRUC_SIG["RC_MAP"][gt_single_ts_no_list_i_rc_l]]
                else:
                    continue # jump to next turn in the loop if road temperature is invaild in both gt marwis
                
                # extend analysis
                if extend_da_flag:
                    
                    ###adding at here: for extend temporary variance
                    gt_single_ts_no_list_i_at_r = gt_single_ts_no_list_i_content[0][5] # ambient temperature on right
                    gt_single_ts_no_list_i_at_l = gt_single_ts_no_list_i_content[0][6] # ambient temperature on left 
                    
                    ###adding at here: for gt value check
                    # ambient temperature
                    if (gt_single_ts_no_list_i_at_r!=None or gt_single_ts_no_list_i_at_l!=None): 
                        if (gt_single_ts_no_list_i_at_r == None): # gt_single_ts_no_list_i_rt_l: valid 
                            gt_single_ts_no_list_i_at_aver = gt_single_ts_no_list_i_at_l
                        elif (gt_single_ts_no_list_i_at_l == None): # gt_single_ts_no_list_i_rt_r: valid 
                            gt_single_ts_no_list_i_at_aver = gt_single_ts_no_list_i_at_r
                        else: # both valid
                            gt_single_ts_no_list_i_at_aver = (gt_single_ts_no_list_i_at_r+gt_single_ts_no_list_i_at_l)/2
                    else:
                         continue # jump to next turn in the loop if road temperature is invaild in both gt marwis

            else: 
                continue # jump if gt unit is too far outside scope of distance
                
            # rcs data in nearest timestamp and distance    
            # error control of eval (rcs_in_None)
            try:
                rcs_ts_no_list_i_content = eval (rcs_df.loc[gt_single_ts_no_list_i, gt_single_ts_mapto_rcs[gt_single_ts_index_i]])
            except ValueError:
                continue
            
            rcs_ts_no_list_i_rt = rcs_ts_no_list_i_content[4] # road temperature
            rcs_ts_no_list_i_at = rcs_ts_no_list_i_content[5] # ambient temperature # TODO: consider AT
            rcs_ts_no_list_i_rc = rcs_ts_no_list_i_content[0] # road condition
            
            #add temperature threshold judgement
            if temp_thre:
                if extend_da_flag:
                    if abs(gt_single_ts_no_list_i_rt_aver-rcs_ts_no_list_i_rt)<=temp_thre and abs(gt_single_ts_no_list_i_at_aver-rcs_ts_no_list_i_at)<=temp_thre:
                        pass
                    else:
                        continue
                else:
                    if abs(gt_single_ts_no_list_i_rt_aver-rcs_ts_no_list_i_rt)<=temp_thre:
                        pass
                    else:
                        continue
            else:
                pass
                
            gt_rcs_rt_diff_temp.append([gt_single_ts_no_list_i, gt_single_ts_no_list_i_rt_aver-rcs_ts_no_list_i_rt])
            gt_rcs_rc_diff_temp.append([gt_single_ts_no_list_i, [road_condition_single_analysis(i,rcs_ts_no_list_i_rc) for i in gt_single_ts_no_list_i_rc_comp]])
            #gt_rcs_rc_diff_temp.append([gt_single_ts_no_list_i, rcs_ts_no_list_i_rc in gt_single_ts_no_list_i_rc_comp])
            
            ###adding at here: for appending in list
            # extend analysis
            if extend_da_flag:
                gt_rcs_at_diff_temp.append([gt_single_ts_no_list_i, gt_single_ts_no_list_i_at_aver-rcs_ts_no_list_i_at])

        gt_rcs_rt_diff.append([gt_single_ts[gt_single_ts_index_i], gt_rcs_rt_diff_temp]) 
        gt_rcs_rc_diff.append([gt_single_ts[gt_single_ts_index_i], gt_rcs_rc_diff_temp])
        
        ###adding at here: for appending in list
        # extend analysis
        if extend_da_flag:
            gt_rcs_at_diff.append([gt_single_ts[gt_single_ts_index_i], gt_rcs_at_diff_temp]) 
    
    # for return
    if extend_da_flag:
        return gt_rcs_rt_diff, gt_rcs_rc_diff, gt_rcs_at_diff
    else:
        return gt_rcs_rt_diff, gt_rcs_rc_diff
    
class GT_RCS_COMP(object):
    """
    class:
        to manage operation of comparison result between ground truth and rcs supplier data
    param:
        rcs_code - code for rcs supplier
        area_code - code for area
        vehicle_code - code for vehicle
    func:
        __init__(rcs_code, area_code):
            save self.varience
        
        _comp_df(csv_addr, _index_col, _low_memory):
            return pd.read_csv()

        gt_single_df(gt_filename,vehicle_code):
            call self._comp_df()
            return self.gt_single_df
        
        direct_comp(extend_analysis_flag, result_saving):
            prerequisist, need to run after such self.function():
                self.gt_single_df()
            save self.direct_comparison_result_in_list in .txt file
            return self.direct_comparison_result_in_list
        
    """
    def __init__(self, rcs_code="", area_code="", read_rcs_csv_flag=True):
        global gt_value_per_ts, GT_RCS_MAX_DIST, GT_RCS_MAX_TIME
        self.rcs_code = rcs_code
        self.area_code = area_code
        self._rcs_posID()
        
        if read_rcs_csv_flag:
            # read rcs compilation .csv
            #rcs_comp_df = pd.read_csv(RCS_DATA_FILE[rcs_code]["comp"][area_code], index_col=0, low_memory=False)
            self.rcs_comp_df = self._comp_df(RCS_DATA_FILE[self.rcs_code]["comp"][self.area_code])
            print("[done-ga10002] finish read dateframe of {} in {}.".format(self.rcs_code, self.area_code))
    
    def set_rcs_code(self, rcs_code):
        self.rcs_code = rcs_code
    
    def set_area_code(self, area_code):
        self.area_code = area_code    

    def set_vehicle_code(self, vehicle_code):
        self.vehicle_code = vehicle_code
        
    def _comp_df(self, csv_addr, _index_col=0, _low_memory=False):
        """
        <internal function>
        func:
            read .csv into dateframe
        """
        return pd.read_csv(csv_addr, index_col=_index_col, low_memory=_low_memory)

    def gt_df(self, gt_filename, vehicle_code="C"):
        self.vehicle_code = vehicle_code
        self.gt_filename = gt_filename
        # read gt single day .csv
        #gt_single_df = pd.read_csv(gt_single_csv_addr, index_col=0, low_memory=False)
        self.gt_single_df = self._comp_df(GT_DATA_FILE["convert"][self.area_code][self.vehicle_code]+"\\"+self.gt_filename)
        print("[done-ga10003] finish read dateframe of GT-{} in {} in {}.".format(self.vehicle_code, self.area_code, self.gt_filename.split(".")[0]))
        return self.gt_single_df
        
    def direct_comp(self, extend_analysis_flag=False, result_saving=True):
        """
        func:
            1st turn - direct comparison between ground truth and rcs, based on func: gt_vs_rcs() in ge_rcsDA.py
        dependency:
            - gt_vs_rcs (gt_df, rcs_df, max_dist=GT_RCS_MAX_DIST, max_time=GT_RCS_MAX_TIME, extend_da_flag=False)
        """
        global gt_value_per_ts, GT_RCS_MAX_DIST, GT_RCS_MAX_TIME
        self.max_dist = GT_RCS_MAX_DIST
        self.max_time = GT_RCS_MAX_TIME
        
        # run analysis function single-day-gt vs. compilation-rcs
        #gt_rcs_rt_diff, gt_rcs_rc_diff, gt_rcs_at_diff = gt_vs_rcs(gt_single_df, rcs_comp_df)
        direct_comp_start = timeit.default_timer()
        self.extend_analysis_flag = extend_analysis_flag
        if self.extend_analysis_flag:
            # TODO: need to extend output element if more output for analysis
            self.gt_rcs_rt_diff, self.gt_rcs_rc_diff, self.gt_rcs_at_diff = gt_vs_rcs(self.gt_single_df, self.rcs_comp_df, max_dist=self.max_dist, max_time=self.max_time, extend_da_flag=True)
            if result_saving:
                save_str_in_file(GT_DATA_FILE["convert"][self.area_code][self.vehicle_code]+"\\[Result-roadTemp]{}_vs_GT-{}_{}_".format(self.rcs_code, self.vehicle_code, self.area_code)+self.gt_filename.replace("csv","txt"), str(self.gt_rcs_rt_diff), save_type="w+")
                save_str_in_file(GT_DATA_FILE["convert"][self.area_code][self.vehicle_code]+"\\[Result-roadCond]{}_vs_GT-{}_{}_".format(self.rcs_code, self.vehicle_code, self.area_code)+self.gt_filename.replace("csv","txt"), str(self.gt_rcs_rc_diff), save_type="w+")
                save_str_in_file(GT_DATA_FILE["convert"][self.area_code][self.vehicle_code]+"\\[Result-ambiTemp]{}_vs_GT-{}_{}_".format(self.rcs_code, self.vehicle_code, self.area_code)+self.gt_filename.replace("csv","txt"), str(self.gt_rcs_at_diff), save_type="w+")            
            print("\n[done-ga10000] finish data comparison between ground truth on vehicle-{} and rcs-{} in {} in {:.2f} seconds.".format(self.vehicle_code, self.rcs_code, self.area_code, timeit.default_timer()-direct_comp_start))
            return self.gt_rcs_rt_diff, self.gt_rcs_rc_diff, self.gt_rcs_at_diff
        else:
            self.gt_rcs_rt_diff, self.gt_rcs_rc_diff = gt_vs_rcs(self.gt_single_df, self.rcs_comp_df, max_dist=self.max_dist, max_time=self.max_time, extend_da_flag=False)
            if result_saving:
                save_str_in_file(GT_DATA_FILE["convert"][self.area_code][self.vehicle_code]+"\\[Result-roadTemp]{}_vs_GT-{}_{}_".format(self.rcs_code, self.vehicle_code, self.area_code)+self.gt_filename.replace("csv","txt"), str(self.gt_rcs_rt_diff), save_type="w+")
                save_str_in_file(GT_DATA_FILE["convert"][self.area_code][self.vehicle_code]+"\\[Result-roadCond]{}_vs_GT-{}_{}_".format(self.rcs_code, self.vehicle_code, self.area_code)+self.gt_filename.replace("csv","txt"), str(self.gt_rcs_rc_diff), save_type="w+")
            print("\n[done-ga10001] finish data comparison between ground truth on vehicle-{} and rcs-{} in {} in {:.2f} seconds.".format(self.vehicle_code, self.rcs_code, self.area_code, timeit.default_timer()-direct_comp_start))
            return self.gt_rcs_rt_diff, self.gt_rcs_rc_diff
        
            # =============================================================================
            #         # save comparison result in local
            #         # road temperature difference
            #         file=open(gt_single_csv_addr.replace(gt_single_csv_addr.split("\\")[-1], "rt_{}.txt".format(gt_single_csv_addr.split("\\")[-1].split(".")[0])),'w')  
            #         file.write(str(gt_rcs_rt_diff));  
            #         file.close()
            #         # road condition difference
            #         file=open(gt_single_csv_addr.replace(gt_single_csv_addr.split("\\")[-1], "rc_{}.txt".format(gt_single_csv_addr.split("\\")[-1].split(".")[0])),'w')  
            #         file.write(str(gt_rcs_rc_diff));  
            #         file.close()
            #         #    # ambient temperature difference
            #         #    file=open(gt_single_csv_addr.replace(gt_single_csv_addr.split("\\")[-1], "at_{}.txt".format(gt_single_csv_addr.split("\\")[-1].split(".")[0])),'w')  
            #         #    file.write(str(gt_rcs_at_diff));  
            #         #    file.close()
            # =============================================================================
            # =============================================================================
            #     # read .txt in python
            #     file = open(("data.txt"),'r')
            #     label = [x.strip() for x in file]
            #     file.close()
            #     label=eval(label[0])
            # =============================================================================

    def _read_direct_comp_from_file (self, direct_comp_addr, **args):
        """
        <internal function>
        func:
            read direct_comparison_result.txt
            return eval("[list]") in list
        reference:
            use of */**args - <https://www.cnblogs.com/liangxiyang/p/11208899.html>
        """
        try: # for testing
            self.rcs_code = args["rcs_code"]
            self.area_code = args["area_code"]
            self.vehicle_code = args["vehicle_code"]
        except:
            pass
        
        _direct_comp_file = open(direct_comp_addr, 'r+')
        _direct_comp_str = [x.strip() for x in _direct_comp_file]
        _direct_comp_file.close()
        return eval(_direct_comp_str[0])
    
    def read_rt (self, direct_comp_addr):
        """
        func:
            load road_temperature_difference from file
        """
        self.gt_rcs_rt_diff = self._read_direct_comp_from_file(direct_comp_addr)
        self.list_origin = self.gt_rcs_rt_diff
        return self.gt_rcs_rt_diff
    
    def clean(self, list_origin=""):
        """
        func:
            clean list and delete empty element
        param:
            list_origin - in list
        """
        if list_origin:
            self.list_origin = list_origin
        
        counter_i = 0
        while (counter_i<len(self.list_origin)):
            if self.list_origin[counter_i][1]==[]:
                self.list_origin.pop(counter_i)
                continue
            counter_i += 1
        
        return self.list_origin
    
    def _rcs_posID(self):
        """
        <internal function>
        func:
            obtain start and end of posID
        """
        self.rcs_posID_df = road_no (CHINA_GPS[self.area_code])
        self.rcs_posID_start = self.rcs_posID_df[self.rcs_posID_df.index[0]]
        self.rcs_posID_end = self.rcs_posID_df[self.rcs_posID_df.index[-1]]
    
    def diff_by_posID(self, list_origin="", timestamp_flag=True):
        """
        func:
            output data comparison per position in list, in format:
                list[j](for pos_i) - [..., [timestamp_t (""), comparison_result], ...]
                j = pos_i - pos_start
                as if:
                    position\times  | ...   | times_x                                                   | ...
                    ----------------|-------|-----------------------------------------------------------|----
                    pos_start       | ...   | ...                                                       | ...
                    ...             | ...   | ...                                                       | ...
                    pos_i           | ...   | [timestamp_in_i_times_x, data_result_in_i_times_x]        | ...
                    pos_i+1         | ...   | [timestamp_in_i+1_times_x, data_result_in_i+1_times_x]    | ...
                    ...             | ...   | ...                                                       | ...
                    pos_end         | ...   | ...                                                       | ...
        param:
            list_origin - in list
            timestamp_flag - default by True
        """
        if list_origin:
            self.list_origin = list_origin

        self._rcs_posID()
        self.list_per_posID = [[]]*len(self.rcs_posID_df)
        
        for list_origin_line_i in self.list_origin:
            for result_in_line_i_j in list_origin_line_i[1]:
                pos_temp = result_in_line_i_j[0]
                if timestamp_flag:
                    data_temp = [list_origin_line_i[0], result_in_line_i_j[1]]
                else:
                    data_temp = [result_in_line_i_j[1]]
                
                # append data_temp into list_per_posID
                if self.list_per_posID[pos_temp-self.rcs_posID_start] == []:
                    self.list_per_posID[pos_temp-self.rcs_posID_start] = [data_temp]
                else:
                    self.list_per_posID[pos_temp-self.rcs_posID_start].append(data_temp)
        return self.list_per_posID
    
    def convert2_wo_ts(self, list_origin=""):
        """
        func:
            eliminate timestamp in the list
        """
        if list_origin:
            self.list_origin = list_origin
            
        self._rcs_posID()
        
        for line_i in range(len(self.list_origin)):
            for row_j in range(len(self.list_origin[line_i])):
                self.list_origin[line_i][row_j] = [self.list_origin[line_i][row_j][1]]
                
        return self.list_origin
        
    
    def statistic_by_posID(self, list_origin="", timestamp_flag=False):
        """
        recommend:
            run after diff_by_posID()
        func:
            calculate the average difference per position in list, in format:
                if timestamp_flag=False:
                    list[j](for pos_i) - [[result_aver, result_min, result_max, result_std(being root)]]
                    j = pos_i - pos_start
                    as if:
                        position\times  | result                                          
                        ----------------|----------
                        pos_start       | ...                                                   
                        ...             | ...                                                   
                        pos_i           | [result_aver, result_min, result_max, result_std] 
                        pos_i+1         | [result_aver, result_min, result_max, result_std]   
                        ...             | ...                                                
                        pos_end         | ...                                                    
        param:
            list_origin - in list
            timestamp_flag - default by False
        """
        if list_origin:
            self.list_origin = list_origin
            
        self._rcs_posID()
        self.list_per_posID = [[]]*len(self.rcs_posID_df)
        for list_origin_posID_i in range(len(self.rcs_posID_df)):
            if self.list_origin[list_origin_posID_i] == []:
                pass
            else:
                if timestamp_flag:
                    # TODO: consider case with timestamp
                    pass
                else:
                    list_origin_temp = np.array(self.list_origin[list_origin_posID_i])
                    #print(list_origin_temp)
                    temp_aver, temp_min, temp_max, temp_std = list_origin_temp.mean(), list_origin_temp.min(), list_origin_temp.max(), list_origin_temp.std()
                    self.list_per_posID[list_origin_posID_i] = [[temp_aver, temp_min, temp_max, temp_std]]
        return self.list_per_posID
                                    
class GT_RCS_RT(object):
    """
    class:
        use to operate road-temperature-related comparison between ground truth and rcs supplier
    """
    def __init__(self, rcs_code="", area_code="", temp_flag="RT"):
        self.rcs_code = rcs_code
        self.area_code = area_code
        self.GT_RCS_COMP = GT_RCS_COMP(rcs_code=self.rcs_code, area_code=self.area_code, read_rcs_csv_flag=False)
        self.rcs_posID_start, self.rcs_posID_end = self.GT_RCS_COMP.rcs_posID_start, self.GT_RCS_COMP.rcs_posID_end
        
        self.temp_flag = temp_flag
        if temp_flag == "RT":
            self.temp_type = "road temperature"
        elif temp_flag == "AT":
            self.temp_type = "ambient temperature"
    
    def read(self, direct_comp_addr, clean_flag=True):
        """
        func:
            load road_temperature_difference from file
            clean list and delete empty element, enable by clean_flag, which is True by default
        """
        self.rt = self.GT_RCS_COMP.read_rt(direct_comp_addr)
        if clean_flag:
            self.rt = self.GT_RCS_COMP.clean()
        return self.rt
    
    def by_posID(self, rt_origin="", timestamp_flag=True):
        """
        recommend: 
            run after read()
        param:
            rt_origin - in list
            timestamp_flag - True: add timestamp in data element, False: do not add timestamp in data element, dy default: True
        """
        if rt_origin:
            self.rt = rt_origin
        
        try:
            if timestamp_flag:
                self.rt_by_posID_with_ts = self.GT_RCS_COMP.diff_by_posID(self.rt, True)
                return self.rt_by_posID_with_ts
            else:
                self.rt_by_posID_wo_ts = self.GT_RCS_COMP.diff_by_posID(self.rt, False)
                return self.rt_by_posID_wo_ts
        except AttributeError:
            raise Exception("[error-ga10005] 'GT_RCS_RT' object has no attribute 'rt', please run read() or give the input list for by_posID().")
    
    def convert(self, rt_origin=""):
        """
        func:
            covert list with timestamp to without timestamp
        """
        if rt_origin:
            self.rt = rt_origin
            
        self.rt_by_posID_wo_ts = self.GT_RCS_COMP.convert2_wo_ts(copy.deepcopy(self.rt))
        return self.rt_by_posID_wo_ts
        
    
    # TODO: merge has bug when continues reading data
    def merge(self, listB, timestamp_flag=True):
        """
        recommend:
            run after by_posID()
        func:
            merge listB content to origin list
        param:
            timestamp_flag - if True, origin list is rt_by_posID_with_ts; if False, origin list is rt_by_posID_wo_ts; default by True
        """
        if timestamp_flag:
            self.rt_by_posID_with_ts = merge_list(self.rt_by_posID_with_ts, listB)
            return self.rt_by_posID_with_ts
        else:
            self.rt_by_posID_wo_ts = merge_list(self.rt_by_posID_wo_ts, listB)
            return self.rt_by_posID_wo_ts
    
    def statistic (self, timestamp_flag=False):
        """
        func:
            calculate the average value of each row in list-rt_by_posID_with/wo_ts
        param:
            timestamp_flag - if True, consider rt_by_posID_with_ts; if False, consider rt_by_posID_wo_ts; default by False
        note:
            # TODO: finish the average strategy with timestamp
        """
        if timestamp_flag:
            pass
        else:
            self.GT_RCS_COMP.list_origin = self.rt_by_posID_wo_ts
            self.rt_statistic = self.GT_RCS_COMP.statistic_by_posID()
            self._statistic_deconstruct() # to de-construct statistic tuple into aver_, min_, max_ std_
        return self.rt_statistic
    
    def _statistic_deconstruct (self, timestamp_flag=False):
        """
        <internal function>
        func:
            to de-construct statistic tuple into aver_, min_, max_ std_
        param:
            timestamp_flag - if True, need to consider timestamp; if False, do not need to consider timestamp; default by False
        """
        # init
        self.rt_aver = [None]*len(self.rt_statistic)
        self.rt_min = [None]*len(self.rt_statistic)
        self.rt_max = [None]*len(self.rt_statistic)
        self.rt_std = [None]*len(self.rt_statistic)
        
        if timestamp_flag:
            pass
        else:
            for line_counter_i in range(len(self.rt_statistic)):
                if self.rt_statistic[line_counter_i] == []:
                    pass
                else:
                    self.rt_aver[line_counter_i] = self.rt_statistic[line_counter_i][0][0]
                    self.rt_min[line_counter_i] = self.rt_statistic[line_counter_i][0][1]
                    self.rt_max[line_counter_i] = self.rt_statistic[line_counter_i][0][2]
                    self.rt_std[line_counter_i] = self.rt_statistic[line_counter_i][0][3]
                    
    def plt_statistic(self):
        """
        help <https://blog.csdn.net/qiurisiyu2016/article/details/80187177>
        """
#        plt.plot([i for i in range(self.rcs_posID_start,self.rcs_posID_end+1)],self.rt_aver,'gs')
#        plt.plot([i for i in range(self.rcs_posID_start,self.rcs_posID_end+1)],self.rt_min,'bp')
#        plt.plot([i for i in range(self.rcs_posID_start,self.rcs_posID_end+1)],self.rt_max,'ro')
        fig1 = plt.figure(num='{}_{}_{}-1'.format(self.temp_flag, self.rcs_code, self.area_code)) # RT_KU_BJ
        if self.rcs_posID_start > 1:
            rt_prefix = [0]*(self.rcs_posID_start-1)
            rt_aver = np.append(rt_prefix, self.rt_aver)
            rt_min = np.append(rt_prefix, self.rt_min)
            rt_max = np.append(rt_prefix, self.rt_max)
        else:
            rt_aver = self.rt_aver
            rt_min = self.rt_min
            rt_max = self.rt_max
        plt.plot(rt_aver,'gs',label="average") # 'gs'
        plt.plot(rt_min,'bp',label="minimum") # 'bp'
        plt.plot(rt_max,'ro',label="maxmum") # "ro"
        plt.title("{} comparison of {} with ground truth of positions in {} area".format(self.temp_type, self.rcs_code, self.area_code)) # road temperature comparison of SUP with ground truth of positions in BJ area
        plt.xlim(self.rcs_posID_start, self.rcs_posID_end)
        plt.xlabel('posID in {} area (from {} to {})'.format(self.area_code, self.rcs_posID_start, self.rcs_posID_end))
        plt.ylabel('{} difference in celsius'.format(self.temp_type))
        plt.legend(['average','minimum','maximum'])
        plt.show()
        #plt.close()
        return True
    
    def flatten(self):
        """
        func:
            flatten self.rt_by_posID_wo_ts into 1 dimension list
        """
        self.rt_total_wo_ts = []
        for data_i in self.rt_by_posID_wo_ts:
            self.rt_total_wo_ts  = np.append(self.rt_total_wo_ts, np.array(data_i).flatten())
        
        self.rt_total_wo_ts_mean = self.rt_total_wo_ts.mean()
        self.rt_total_wo_ts_min = self.rt_total_wo_ts.min()
        self.rt_total_wo_ts_max = self.rt_total_wo_ts.max()
        self.rt_total_wo_ts_std = self.rt_total_wo_ts.std()
        return self.rt_total_wo_ts
            
        
    def plt_hist(self):
        """
        func:
            plot histogram for total data
        """
#        self.rt_total_wo_ts = copy.deepcopy(self.rt_by_posID_wo_ts)
#        self.rt_total_wo_ts = np.array(self.rt_total_wo_ts).flatten()
        if len(self.rt_total_wo_ts.shape) > 1: # degrade multi-dim array to 1-dimension array
            self.rt_total_wo_ts = self.rt_total_wo_ts.flatten() 
        
        #plt.figure(num='{}_{}_{}-2'.format(self.temp_flag, self.rcs_code, self.area_code))
        f,ax=plt.subplots() # create a new plt frame window
        
        sns.distplot(self.rt_total_wo_ts)
        ax.grid(axis="y", alpha=0.75)
        ax.set_xlabel("temperature difference in celsius degree")
        ax.set_ylabel("frequency")
        ax.set_title("{} comparison of {} with ground truth in total-{} area".format(self.temp_type, self.rcs_code, self.area_code))
        ax.text(5,0.1,"arithmetic mean:{:.3f}\nstandard deviation:{:.3f}".format(self.rt_total_wo_ts_mean,self.rt_total_wo_ts_std),fontdict={"size":16,"color":"r"})
        # TODO: add auxiliary line for mean, etc.
        
        return True
    
if __name__ == '__main__':
    gt_rcsDA_start = timeit.default_timer()
    
    # check code compliance
    rcs_code, area_code, vehicle_code, analysis_code = [input_compliance_check(i) for i in [rcs_code_list, area_code_list, vehicle_code_list, analysis_code_list]] # translate flag code in compliance format
    #rcs_code, area_code = input_dirScreen_compilance_check([rcs_code, area_code])[0:2] # translate flag code in compliance format
    
    """
    1. return and saving result of direct comparison
    """
    """
    # create init class and save analysis result by direct comparison
    # should be comment if direct comparison result is saved
    for rcs_code in rcs_code_list:
        for area_code in area_code_list:
            # init/re-init class of GT_RCS_COMP()
            gt_rcs_comp = GT_RCS_COMP(rcs_code, area_code)
            for vehicle_code in vehicle_code_list:
                #print(rcs_code, area_code, vehicle_code)
                
                # scanning all files under folder of certain vehicle's ground truth in certain area  
                gt_file_list = list(os.walk(GT_DATA_FILE["convert"][area_code][vehicle_code]))[0][2]
                for gt_file_i in gt_file_list:
                    # choosing gt_single_day.csv
                    if re.match(gt_single_csv_pattern, gt_file_i):
                        gt_rcs_loop_start = timeit.default_timer()
                        # read gt in dataframe from csv into class
                        gt_df_temp = gt_rcs_comp.gt_df(gt_file_i,vehicle_code)
                        gt_rcs_rt_diff_temp, gt_rcs_rc_diff_temp = gt_rcs_comp.direct_comp()
                print("[done-ga10004] finish anlysis between GT-vehicle-{} and rcs-{} in {} in {} in {:.2f} seconds.".format(vehicle_code, rcs_code, area_code, gt_file_i.split(".")[0], timeit.default_timer()-gt_rcs_loop_start))
                print("="*10)
    """
#    gt_rcs_comp = GT_RCS_COMP(rcs_code_exp, area_code_exp)
#    gt_df_temp = gt_rcs_comp.gt_single_df("2019-12-17_Tuesday.csv",vehicle_code_exp)
#    gt_rcs_rt_diff_temp, gt_rcs_rc_diff_temp = gt_rcs_comp.direct_comp()
                
    """
    2. road-temperature-related data comparison and save
    """
    """
    # create init class and read result list from file by direct comparison
    gt_rcs_rt_temp = GT_RCS_RT(rcs_code_exp,area_code_exp)
    # read road_temp_result in list from .txt
    gt_rcs_rt_temp.read(gt_rcs_gt_addr_exp)
    # processing road_temp_result to result per position id
    gt_rcs_rt_temp_posID_with_ts = gt_rcs_rt_temp.by_posID()
    gt_rcs_rt_temp_posID_wo_ts = gt_rcs_rt_temp.by_posID(timestamp_flag=False)
    # calculate statistic result of each position ID
    gt_rcs_rt_statistic_temp_posID_wo_ts = gt_rcs_rt_temp.statistic()
    # ploting
    gt_rcs_rt_temp.plt_statistic()
    """
    """
    for rcs_code in rcs_code_list:
        rt_pattern = r"\[Result-roadTemp\]{}.*\.txt".format(rcs_code)
        rc_pattern = r"\[Result-roadCond\]{}.*\.txt".format(rcs_code)
        at_pattern = r"\[Result-ambiTemp\]{}.*\.txt".format(rcs_code)
        for area_code in area_code_list:
            # create init class and read result list from file by direct comparison
            gt_rcs_rt_temp = GT_RCS_RT(rcs_code, area_code)
            gt_rcs_rt_total_with_ts = [[]]*(gt_rcs_rt_temp.rcs_posID_end-gt_rcs_rt_temp.rcs_posID_start+1)
            gt_rcs_rt_total_wo_ts = [[]]*(gt_rcs_rt_temp.rcs_posID_end-gt_rcs_rt_temp.rcs_posID_start+1)
            
            gt_rcs_at_temp = GT_RCS_RT(rcs_code, area_code)
            gt_rcs_at_total_with_ts = [[]]*(gt_rcs_at_temp.rcs_posID_end-gt_rcs_at_temp.rcs_posID_start+1)
            gt_rcs_at_total_wo_ts = [[]]*(gt_rcs_at_temp.rcs_posID_end-gt_rcs_at_temp.rcs_posID_start+1)
            
            gt_rcs_rc_temp = GT_RCS_RT(rcs_code, area_code)
            gt_rcs_rc_total_with_ts = [[]]*(gt_rcs_rc_temp.rcs_posID_end-gt_rcs_rc_temp.rcs_posID_start+1)
            gt_rcs_rc_total_wo_ts = [[]]*(gt_rcs_rc_temp.rcs_posID_end-gt_rcs_rc_temp.rcs_posID_start+1)
            
            for vehicle_code in vehicle_code_list:
                file_list = list(os.walk(GT_DATA_FILE["convert"][area_code][vehicle_code]))[0][2]
#                file_counter = 0 # for debuging
                for file_i in file_list:
                    if re.match(rt_pattern, file_i):
                        print(file_i)
                        # read road_temp_result in list from .txt
                        gt_rcs_rt_temp.read(GT_DATA_FILE["convert"][area_code][vehicle_code]+"\\"+file_i)
                        # processing road_temp_result to result per position id
                        gt_rcs_rt_temp_posID_with_ts = gt_rcs_rt_temp.by_posID()
                        gt_rcs_rt_temp_posID_wo_ts = gt_rcs_rt_temp.by_posID(timestamp_flag=False)
                        
                        gt_rcs_rt_total_with_ts = merge_list(gt_rcs_rt_total_with_ts, gt_rcs_rt_temp_posID_with_ts)
                        gt_rcs_rt_total_wo_ts = merge_list(gt_rcs_rt_total_wo_ts, gt_rcs_rt_temp_posID_wo_ts)
                        
#                        # for less file debuging
#                        file_counter += 1
#                        if file_counter > 3:
#                            break
                    elif re.match(at_pattern, file_i):
                        print(file_i)
                        gt_rcs_at_temp.read(GT_DATA_FILE["convert"][area_code][vehicle_code]+"\\"+file_i)
                        gt_rcs_at_temp_posID_with_ts = gt_rcs_at_temp.by_posID()
                        gt_rcs_at_temp_posID_wo_ts = gt_rcs_at_temp.by_posID(timestamp_flag=False)
                        gt_rcs_at_total_with_ts = merge_list(gt_rcs_at_total_with_ts, gt_rcs_at_temp_posID_with_ts)
                        gt_rcs_at_total_wo_ts = merge_list(gt_rcs_at_total_wo_ts, gt_rcs_at_temp_posID_wo_ts)
                    
                    elif re.match(rc_pattern, file_i):
                        print(file_i)
                        gt_rcs_rc_temp.read(GT_DATA_FILE["convert"][area_code][vehicle_code]+"\\"+file_i)
                        gt_rcs_rc_temp_posID_with_ts = gt_rcs_rc_temp.by_posID()
                        gt_rcs_rc_temp_posID_wo_ts = gt_rcs_rc_temp.by_posID(timestamp_flag=False)
                        gt_rcs_rc_total_with_ts = merge_list(gt_rcs_rc_total_with_ts, gt_rcs_rc_temp_posID_with_ts)
                        gt_rcs_rc_total_wo_ts = merge_list(gt_rcs_rc_total_wo_ts, gt_rcs_rc_temp_posID_wo_ts)
            
            gt_rcs_rt_temp.rt_by_posID_with_ts = gt_rcs_rt_total_with_ts
            gt_rcs_rt_temp.rt_by_posID_wo_ts = gt_rcs_rt_total_wo_ts
#            # calculate statistic result of each position ID
#            gt_rcs_rt_statistic_temp_posID_wo_ts = gt_rcs_rt_temp.statistic()
#            # ploting
#            gt_rcs_rt_temp.plt_statistic()
            
            gt_rcs_at_temp.rt_by_posID_with_ts = gt_rcs_at_total_with_ts
            gt_rcs_at_temp.rt_by_posID_wo_ts = gt_rcs_at_total_wo_ts
            
            gt_rcs_rc_temp.rt_by_posID_with_ts = gt_rcs_rc_total_with_ts
            gt_rcs_rc_temp.rt_by_posID_wo_ts = gt_rcs_rc_total_wo_ts
            
            save_str_in_file("[GT Comparison] RT_{}_{}.txt".format(rcs_code, area_code), str(gt_rcs_rt_total_with_ts), save_type="w")
            save_str_in_file("[GT Comparison] AT_{}_{}.txt".format(rcs_code, area_code), str(gt_rcs_at_total_with_ts), save_type="w")
            save_str_in_file("[GT Comparison] RC_{}_{}.txt".format(rcs_code, area_code), str(gt_rcs_rc_total_with_ts), save_type="w")
            print("="*10)
    """
        
    """
    3. road-temperature-related data analysis
    """
    """
    temp_code_list = ["RT", "AT"]
    temp_total_list = []
    
    for rcs_code in rcs_code_list:
        for area_code in area_code_list:
            for temp_code in temp_code_list:
                # init analysis class
                anaysis_class_temp = GT_RCS_RT(rcs_code=rcs_code, area_code=area_code, temp_flag=temp_code)
                # read temperature result from file
                filename_temp = "[GT Comparison] {}_{}_{}.txt".format(temp_code, rcs_code, area_code) # [GT Comparison] AT_KU_BJ.txt               
                fileaddr_temp = RCS_DATA_DIR+"\\"+filename_temp
                anaysis_list_temp = anaysis_class_temp.read(direct_comp_addr=fileaddr_temp, clean_flag=False)
                anaysis_list_wo_ts_temp = anaysis_class_temp.convert()
                # statistics
                anaysis_class_temp.statistic()
                # plt
                #anaysis_class_temp.plt_statistic()
                temp_total_list.append(anaysis_class_temp.flatten())
                anaysis_class_temp.plt_hist()
    """

    """
    4. merged histogram comparison (only for testing)
    # TODO: need to be refactored into class - function 
    """       
    """
    f,ax=plt.subplots() # create a new plt frame window
        
    sns.distplot(temp_total_list[3], label="AT-KU-North")
    sns.distplot(temp_total_list[7], label="AT-PRE-North")
    ax.grid(axis="y", alpha=0.75)
    ax.set_xlabel("temperature difference in celsius degree")
    ax.set_ylabel("frequency")
    ax.set_title("ambient temperature comparison of KU/PRE with ground truth in total-North area")
    ax.legend()
    #ax.text(5,0.1,"arithmetic mean:{:.3f}\nstandard deviation:{:.3f}",fontdict={"size":16,"color":"r"})
    """
    
    """
    5. road condition analysis (only for testing)
    note:
        stupid but direct method for scripting
    """
    filename_temp = "[GT Comparison] RC_PRE_N.txt"
    fileaddr_temp = RCS_DATA_DIR+"\\"+filename_temp
    
    rc_confusion_matrix = np.zeros((3,3))
    
    anaysis_class_temp = GT_RCS_RT(rcs_code="PRE", area_code="N")
    anaysis_list_temp = anaysis_class_temp.read(direct_comp_addr=fileaddr_temp, clean_flag=False)
    anaysis_list_wo_ts_temp = anaysis_class_temp.convert()
    #anaysis_list_wo_ts_temp = anaysis_class_temp.flatten()
    
    for rc_per_pos in anaysis_list_wo_ts_temp:
        for rc_per_pos_per_ts in rc_per_pos:
            if len(rc_per_pos_per_ts[0]) == 1:
                i = rc_per_pos_per_ts[0]
            elif len(rc_per_pos_per_ts[0]) == 2:
                i, j = rc_per_pos_per_ts[0]
                if i==j:
                    i=i
                elif i==0 and i!=j:
                    i=j
                elif j==0 and i!=j:
                    i=i
                else:
                    pass
            
            if i == 0:
                rc_confusion_matrix[0][0] += 1
            elif i == 1:
                rc_confusion_matrix[0][1] += 1
            elif i == 2:
                rc_confusion_matrix[0][2] += 1
                
            elif i == 10:
                rc_confusion_matrix[1][0] += 1    
            elif i == 11:
                rc_confusion_matrix[1][1] += 1
            elif i == 12:
                rc_confusion_matrix[1][2] += 1
                
            elif i == 20:
                rc_confusion_matrix[2][0] += 1
            elif i == 21:
                rc_confusion_matrix[2][1] += 1
            elif i == 22:
                rc_confusion_matrix[2][2] += 1
            
    
    """
    for i in anaysis_list_wo_ts_temp:
        if i == 0:
            rc_confusion_matrix[0][0] += 1
        elif i == 1:
            rc_confusion_matrix[0][1] += 1
        elif i == 2:
            rc_confusion_matrix[0][2] += 1
            
        elif i == 10:
            rc_confusion_matrix[1][0] += 1    
        elif i == 11:
            rc_confusion_matrix[1][1] += 1
        elif i == 12:
            rc_confusion_matrix[1][2] += 1
            
        elif i == 20:
            rc_confusion_matrix[2][0] += 1
        elif i == 21:
            rc_confusion_matrix[2][1] += 1
        elif i == 22:
            rc_confusion_matrix[2][2] += 1
    """
    
    rc_confusion_matrix = array_dec_digit(rc_confusion_matrix,2)
    print(rc_confusion_matrix)
    rc_confusion_matrix_precentage = rc_confusion_matrix/rc_confusion_matrix.sum()*100 # percentage of confusion matrix
    rc_confusion_matrix_precentage = array_dec_digit(rc_confusion_matrix_precentage,2)
    print(rc_confusion_matrix_precentage)
    
    f,ax=plt.subplots()
    sns.heatmap(rc_confusion_matrix,annot=True,ax=ax) #plot hearmap
    ax.set_title("confusion matrix of road condition (0-dry, 1-wet, 2-slippery) in PRE in whole-N area") 
    ax.set_xlabel("Presky") 
    ax.set_ylabel("ground truth")
    
    
    