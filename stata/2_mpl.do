/*******************************************************************************
    Project: autoplay
    Author: Reha Tuncer
    Date: 28.06.2025
    Description: descriptives and analysis on cleaned data
*******************************************************************************/
//# preamble
version 18
clear all
macro drop _all
set more off
set scheme s2color, permanently
set maxvar 32767
global graph_opts ///
    graphregion(fcolor(white) lcolor(white)) ///
    bgcolor(white) ///
    plotregion(lcolor(white))
	
global dpath "/Users/reha.tuncer/Documents/GitHub/autoplay/stata/"
// global fpath "/Users/reha.tuncer/Documents/GitHub/icfes-referrals/figures/"
set scheme s2color, permanently	
	
// get a full dataset for standardizing
clear all
cls

import excel "${dpath}clean-MPL-data.xlsx", firstrow clear
capture rename A id
replace id = id + 1000
drop userTranscription

gen treat = treatment
gen mpl = 1
drop treatment
gen treatment = 1 if treat == "autoplayOffMPL"
replace treatment = 2 if treat == "autoplayOnMPL"
drop treat

gen exclude = 0 if trueWatch == "watchTrue"
replace exclude = 1 if trueWatch == "watchFalse"

gen typing_log = typing + notTyping

describe
summarize

misstable summarize
misstable patterns

label variable treatment "Treatment status"

save "${dpath}cleaned_mpl_data.dta", replace
