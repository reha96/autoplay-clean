/*******************************************************************************
    Project: autoplay
    Author: Reha Tuncer
    Date: 03.07.2025
    Description: figure CDF time typing
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
global fpath "/Users/reha.tuncer/Documents/GitHub/autoplay/stata/figures/"
set scheme s2color, permanently	
	
import delimited "${dpath}long_format_data.csv", clear

bysort participant_id: egen sum_mouseout = total(mouseout)
bysort participant_id: egen _t = max(sum_mouseout)
bysort participant_id: replace sum_mouseout = _t
drop _t

sum sum_mouseout
// bysort participant_id: keep if _n == 1 // to test if 40 obs. dropped : YES
drop if sum_mouseout > 20

save "${dpath}long_format_data.dta", replace
clear all

use "${dpath}long_format_data.dta", replace


* Sample 30 participants
preserve
bysort participant_id: keep if _n == 1
set seed 12345
sample 30, count
keep participant_id
tempfile sample_ids
save `sample_ids'
restore

merge m:1 participant_id using `sample_ids'
keep if _merge == 3
drop _merge

* Calculate work rate for each participant
bysort participant_id: egen max_second = max(second)
bysort participant_id: egen final_work = max(cumulative_work)
gen work_rate = final_work / max_second

* Create color categories
gen color_category = 1 if work_rate < 0.2
replace color_category = 2 if work_rate >= 0.2 & work_rate <= 0.8
replace color_category = 3 if work_rate > 0.8

xtile type3 = work_rate, nq(3)
tab type3 color_category

* Label the categories
label define color_cat 1 "Low (< 0.1)" 2 "Medium (0.1-0.9)" 3 "High (> 0.9)"
label values color_category color_cat

* Keep only data up to 1200 seconds
keep if second <= 1200


// plot
levelsof participant_id, local(participants)
local lineplot ""
foreach pid of local participants {
    sum color_category if participant_id == `pid', meanonly
    local cat = r(mean)
    
    if `cat' == 1 local pcolor "dknavy%50"
    if `cat' == 2 local pcolor "midblue%50" 
    if `cat' == 3 local pcolor "dkorange%50"
    
    local lineplot "`lineplot' (line cumulative_work second if participant_id == `pid', lcolor(`pcolor') lwidth(medium))"
}

twoway `lineplot', ///
    title("Typing patterns") ///
    xtitle("Total time (seconds)") ///
    ytitle("Typing (seconds)") ///
	xlabel(0(200)1200, gmax grid) ///
    ylabel(0(200)1200, gmax angle(0)) ///
    legend(ring(0) pos(10) rows(3) region(lcolor(none)) order(1 "Mostly type" 2 "Alternate" 5 "Mostly watch")) $graph_opts xsize(10) ysize(10)
	graph export "${fpath}typing_cdf.png", replace

	
///////////////////////////////////////////////////////////////////////////
use "${dpath}long_format_data.dta", replace

* Calculate work rate for each participant
bysort participant_id: egen max_second = max(second)
bysort participant_id: egen final_work = max(cumulative_work)
gen work_rate = final_work / max_second


* Keep only data up to 1200 seconds
keep if second <= 1200

* Create color categories
gen color_category = 1 if work_rate < 0.25
replace color_category = 2 if work_rate >= 0.25 & work_rate <= 0.75
replace color_category = 3 if work_rate > 0.75


* Create time quartiles
gen quartile = 1 if second <= 300    // Q1: 0-5min
replace quartile = 2 if second > 300 & second <= 600   // Q2: 5-10min  
replace quartile = 3 if second > 600 & second <= 900   // Q3: 10-15min
replace quartile = 4 if second > 900 & second <= 1200  // Q4: 15-20min

* Calculate work done in each quartile for each participant
sort participant_id second
by participant_id: gen work_in_period = cumulative_work - cumulative_work[_n-1]
by participant_id: replace work_in_period = cumulative_work if _n == 1

* Collapse to get total work per quartile per participant
collapse (sum) work_in_period, by(participant_id quartile color_category)

* Create category labels
gen category_label = 1 if color_category == 1
replace category_label = 2 if color_category == 2  
replace category_label = 3 if color_category == 3

label define category_labels 1 "Mostly watch" 2 "Alternate" 3 "Mostly type"
label values category_label category_labels

* Calculate mean work by quartile and category
collapse (mean) work_in_period, by(quartile category_label)

* Reshape to wide format for stacking
reshape wide work_in_period, i(category_label) j(quartile)
gsort -work_in_period4
* Create stacked bar chart
graph bar work_in_period1 work_in_period2 work_in_period3 work_in_period4, ///
    over(category_label) stack ///
    bar(1, fcolor(dknavy%90) lcolor(white)) ///
    bar(2, fcolor(dknavy%70) lcolor(white)) ///
    bar(3, fcolor(dknavy%50) lcolor(white)) ///
    bar(4, fcolor(dknavy%30) lcolor(white)) ///
    title("Typing time by quartile") ///
    ytitle("Typing (seconds)") ///
    ylabel(0(300)1200, angle(0)) ///
    legend(order(1 "Q1 (0-5min)" 2 "Q2 (5-10min)" 3 "Q3 (10-15min)" 4 "Q4 (15-20min)") ///
           pos(10) rows(4) ring(0) region(lcolor(none))) $graph_opts xsize(10) ysize(10) ///
   
graph export "${fpath}work_allocation_quartiles.png", replace
