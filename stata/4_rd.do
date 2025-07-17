/*******************************************************************************
    Project: autoplay
    Author: Reha Tuncer
    Date: 15.07.2025
    Description: RD analysis after achieving day 1 goal
*******************************************************************************/

version 18
clear all
macro drop _all
set more off
set scheme s1mono, permanently	
set maxvar 32767
global graph_opts ///
    graphregion(fcolor(white) lcolor(white)) ///
    bgcolor(white) ///
    plotregion(lcolor(white))
	
global dpath "/Users/reha.tuncer/Documents/GitHub/autoplay/stata/"
global fpath "/Users/reha.tuncer/Documents/GitHub/autoplay/stata/figures/"


import delimited "${dpath}long_format_data.csv", clear

bysort participant_id: egen sum_mouseout = total(mouseout)
bysort participant_id: egen _t = max(sum_mouseout)
bysort participant_id: replace sum_mouseout = _t
drop _t

sum sum_mouseout
drop if sum_mouseout > 20

label define tasklbl 1 "type" 0 "watch"
label values task tasklbl

label define treatlbl 0 "control" 1 "treat"
label values treatment treatlbl

save "${dpath}long_format_data.dta", replace
use "${dpath}long_format_data.dta", clear

gen distance_from_target = cumulative_work - timechoice
gen achieved_target = (distance_from_target >= 0)

* Find target achievement time for each participant
bysort participant_id: egen _t = min(second) if achieved_target == 1
bysort participant_id: egen target_achievement_time = max(_t)
drop _t

preserve
bysort participant_id: keep if  _n == 1
misstable sum // some never achieve plans
restore 


// needed?
// keep if abs(distance_from_target) <= 600

gen bin30 = round(distance_from_target/30)*30 // 30 sec bins 
gen bin60 = round(distance_from_target/60)*60 // 60 sec bins 
gen bin90 = round(distance_from_target/90)*90 // 90 sec bins 

// bysort bin30: egen type_mean = mean(task)
// bysort bin30: keep if _n == 1
rdplot task bin30, p(1)
graph export "${fpath}rd_bin30.png", replace

rdplot task bin60, p(1)
rdplot task bin90, p(1)
rdrobust task bin30, c(0) all vce(cluster participant_id)
rdrobust task bin60, c(0) all vce(cluster participant_id)
rdrobust task bin90, c(0) all vce(cluster participant_id)

rdplot task bin30 if -e(h_l) <= e(h_r), binselect(esmv) kernel(triangular) h(`e(h_l)' `e(h_r)') p(1)
rdplot task bin60 if -e(h_l) <= e(h_r), binselect(esmv) kernel(triangular) h(`e(h_l)' `e(h_r)') p(1)
rdplot task bin90 if -e(h_l) <= e(h_r), binselect(esmv) kernel(triangular) h(`e(h_l)' `e(h_r)') p(1)


//# video transition - time lost on autoplayOff
replace video_transition = 0 if task == 1
rename participant_id id
bysort id: egen total_transition = sum(video_transition)
preserve 
bysort id: keep if _n == 1
ttest total_transition, by(treatment) unequal
restore
save "${dpath}long_format_data.dta", replace
