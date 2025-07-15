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

import excel "${dpath}clean-data.xlsx", firstrow clear

drop treatment
gen treatment = 0 if Treatment == "Control"
replace treatment = 1 if Treatment == "Autoplay"
destring treatment, replace force

rename timeChoice typeChoice
rename typing_log seconds_typing

drop Treatment
rename captchas_submitted_total submit_type

sum mouseout*, det
keep if mouseout_typing + mouseout_watching <= 20
drop mouseout*
save "${dpath}cleaned_autoplay_data.dta", replace

describe
tab treatment
sum session_duration

// balance table 
clear all
use "${dpath}cleaned_autoplay_data.dta", replace

gen employment_3cat = .
replace employment_3cat = 1 if employment == "employed full time"
replace employment_3cat = 2 if inlist(employment, "employed part time", "self employed")
replace employment_3cat = 3 if inlist(employment, "unemployed looking for work", "unemployed not looking for work", "homemaker", "retired", "student", "unable to work")

gen emp_fulltime = (employment_3cat == 1)
gen emp_partself = (employment_3cat == 2) 
gen emp_notemployed = (employment_3cat == 3)

gen income_3cat = .
replace income_3cat = 1 if inlist(income, "0-10", "10-12", "12-15")
replace income_3cat = 2 if inlist(income, "15-20", "20-30", "30-50")
replace income_3cat = 3 if inlist(income, "50-70", "70+")

gen inc_low = (income_3cat == 1)
gen inc_middle = (income_3cat == 2)
gen inc_high = (income_3cat == 3)

gen marital_3cat = .
replace marital_3cat = 1 if marital == "married or domestic partnership"
replace marital_3cat = 2 if marital == "single"
replace marital_3cat = 3 if inlist(marital, "divorced", "widowed", "separated")

gen mar_married = (marital_3cat == 1)
gen mar_single = (marital_3cat == 2)
gen mar_previous = (marital_3cat == 3)

replace birthyear = 1972 if birthyear == 72 // 1ob
replace birthyear = 1964 if birthyear == -1964 // 1ob
gen age = 2025 - birthyear
gen gender_group = .
replace gender_group = 1 if gender == "female"
replace gender_group = 0 if gender == "male"

save "${dpath}cleaned_autoplay_data.dta", replace


display as text "=== BALANCE TABLE RESULTS ===" _newline

display as text "=== Age (continuous) ===" 
ttest age, by(treatment) unequal
global age_mean = r(mu_1)
global age_sd1 = r(sd_1)
global age_sd2 = r(sd_2)
global age_pvalue = r(p)
display "Overall Mean: " r(mu_1) ", P-value: " ${age_pvalue}

foreach v of varlist gender_group emp_fulltime emp_partself emp_notemployed inc_low inc_middle inc_high mar_married mar_single mar_previous {
    display _newline
    display as text "=== Proportion test for `v' ===" 
    
    quietly summarize `v'
    local mean = r(mean)
    local sd = r(sd)
    
    global `v'_mean = `mean'
    global `v'_sd = `sd'
    
    prtest `v', by(treatment)
    global `v'_pvalue = r(p)
    
    display "Proportion: " `mean' ", P-value: " ${`v'_pvalue}
}

display _newline
display as text "=== SUMMARY OF P-VALUES ===" _newline
display "Age: " ${age_pvalue}
display "Gender (female): " ${gender_group_pvalue}
display "Employment - Full time: " ${emp_fulltime_pvalue}
display "Employment - Part time/Self: " ${emp_partself_pvalue}  
display "Employment - Not employed: " ${emp_notemployed_pvalue}
display "Income - Low: " ${inc_low_pvalue}
display "Income - Middle: " ${inc_middle_pvalue}
display "Income - High: " ${inc_high_pvalue}
display "Marital - Married: " ${mar_married_pvalue}
display "Marital - Single: " ${mar_single_pvalue}
display "Marital - Previously married: " ${mar_previous_pvalue}

// summary table
cls

clear all
use "${dpath}cleaned_autoplay_data.dta", replace

replace typeChoice = typeChoice/1200 // divide by max time 
replace seconds_typing = seconds_typing/session_duration // divide by end time (pr. time worked)

gen day1done = (seconds_typing >= typeChoice) // did meet day 1 plan?
xtile choice5 = typeChoice, nq(5)
xtile choice2 = typeChoice, nq(2)


save "${dpath}cleaned_autoplay_data.dta", replace

foreach v of varlist typeChoice seconds_typing content videos_watched_total submit_type number_of_sessions average_session_length {
   quietly summarize `v'
   global `v'_mean = r(mean)
   global `v'_sd = r(sd)
   quietly summarize `v', detail
   global `v'_median = r(p50)
   global `v'_min = r(min)
   global `v'_max = r(max)
   
   quietly summarize `v' if treatment == 1
   global `v'_mean_t1 = r(mean)
   global `v'_sd_t1 = r(sd)
   quietly summarize `v' if treatment == 1, detail
   global `v'_median_t1 = r(p50)
   global `v'_min_t1 = r(min)
   global `v'_max_t1 = r(max)
   
   quietly summarize `v' if treatment == 0
   global `v'_mean_t0 = r(mean)
   global `v'_sd_t0 = r(sd)
   quietly summarize `v' if treatment == 0, detail
   global `v'_median_t0 = r(p50)
   global `v'_min_t0 = r(min)
   global `v'_max_t0 = r(max)
   
   ttest `v', by(treatment)
   global `v'_pvalue = r(p)
}

display "Variable Statistics Summary:"
display _newline

foreach v of varlist typeChoice seconds_typing content videos_watched_total submit_type number_of_sessions average_session_length {
   display "`v' - Overall: Mean=" ${`v'_mean} " SD=" ${`v'_sd} " Median=" ${`v'_median} " Min=" ${`v'_min} " Max=" ${`v'_max}
   display "`v' - Treatment: Mean=" ${`v'_mean_t1} " SD=" ${`v'_sd_t1} " Median=" ${`v'_median_t1} " Min=" ${`v'_min_t1} " Max=" ${`v'_max_t1}
   display "`v' - Control: Mean=" ${`v'_mean_t0} " SD=" ${`v'_sd_t0} " Median=" ${`v'_median_t0} " Min=" ${`v'_min_t0} " Max=" ${`v'_max_t0}
   display "`v' - P-value: " ${`v'_pvalue}
   display _newline
}


ttest typeChoice == seconds_typing

// time spent as proportions
clear all
use "${dpath}cleaned_autoplay_data.dta", replace

gen prop_typing_choice = typeChoice/1200 // day 1 plan
gen type_act_prop = seconds_typing/session_duration // actualized day 2

global y1 type_act_prop 
global y2 videos_watched_total // poisson
global x1 prop_typing_choice

reg $y1 i.treatment c.$x1, vce(robust)
est store r1

poisson $y2 i.treatment c.$x1, vce(robust)

poisson $y2 i.treatment##c.$x1, vce(robust)
est store r2

teffects ra ($y1 $x1) (treatment), vce(robust)
teffects ra ($y2 $x1, poisson) (treatment), vce(robust)







sum content 
gen z_content = (content - r(mean))/r(sd)
kdensity z_content
tabstat z_content, by(treatment) stat(mean semean)

twoway (kdensity prop_typing_choice if treatment == 1) (kdensity prop_typing_choice if treatment == 2)

gen prop_typing = seconds_typing/end_time_log
twoway (kdensity prop_typing if treatment == 1) (kdensity prop_typing if treatment == 2)

gen prop_deviation = prop_typing - prop_typing_choice
twoway (kdensity prop_deviation if treatment == 1) (kdensity prop_deviation if treatment == 2)

sum prop*
tabstat prop*, by(treatment) stat(mean semean)

corr prop_deviation prop_typing_choice

scatter prop_deviation prop_typing_choice
scatter prop_deviation prop_typing_choice if prop_typing_choice < .25
scatter prop_deviation prop_typing_choice if prop_typing_choice > .45 & prop_typing_choice < .55
scatter prop_deviation prop_typing_choice if prop_typing_choice > .55

reg prop_deviation ib(2).choice3 
reg prop_deviation ib(2).choice3 treatment
reg prop_deviation prop_typing_choice treatment

// units of consumption or typing (std)
sum watchedVideo
gen z_vid = (watchedVideo - r(mean))/r(sd)
kdensity z_vid
tabstat z_vid, by(treatment) stat(mean semean)

corr z_vid prop_typing_choice
twoway lfitci z_vid prop_typing_choice || scatter z_vid prop_typing_choice
reg prop_typing_choice z_vid
reg z_vid ib(2).choice3 i.treatment
reg z_vid ib(2).choice3 i.treatment z_content

sum typeCount
gen z_type = (typeCount - r(mean))/r(sd)
kdensity z_type
tabstat z_type, by(treatment) stat(mean semean)

corr z_type prop_typing_choice
twoway lfitci z_type prop_deviation || scatter z_type prop_deviation

reg z_type ib(2).choice3 i.treatment
reg z_type ib(2).choice3 i.treatment z_content

// content
twoway (kdensity content if treatment == 1) (kdensity content if treatment == 2)


// DiD

clear all
use "${dpath}cleaned_autoplay_data.dta", replace

gen prop_typing_choice = typeChoice/session_duration
replace typeChoice = typeChoice/1200

reg prop_typing_choice i.treatment c.typeChoice, vce(robust)
est store r1

reg prop_typing_choice i.treatment##c.typeChoice, vce(robust)
est store r2

teffects ra (prop_typing_choice typeChoice) (treatment), vce(robust)
teffects ipw (prop_typing_choice) (treatment typeChoice gender_group), vce(robust)

teoverlap, ptlevel(1)

logit treatment typeChoice, vce(robust)
predict that
sum that 


// only after ipw
tebalance sum
tebalance density typeChoice
tebalance overid

teffects psmatch (prop_typing_choice) (treatment typeChoice), vce(robust)

teffects ipwra (prop_typing_choice) (treatment typeChoice), vce(robust)



