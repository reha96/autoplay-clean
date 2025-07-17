/*******************************************************************************
    Project: autoplay
    Author: Reha Tuncer
    Date: 02.07.2025
    Description: Histogram of deviations from time choice by treatment
*******************************************************************************/
version 18
clear all
macro drop _all
set more off
set maxvar 32767
global graph_opts ///
    graphregion(fcolor(white) lcolor(white)) ///
    bgcolor(white) ///
    plotregion(lcolor(white))
	
global dpath "/Users/reha.tuncer/Documents/GitHub/autoplay/stata/"
global fpath "/Users/reha.tuncer/Documents/GitHub/autoplay/stata/figures/"
set scheme s2color, permanently	

clear all
use "${dpath}cleaned_autoplay_data.dta", replace
descr

// Create deviation variable
replace seconds_typing = seconds_typing/session_duration
replace typeChoice = typeChoice/1200
gen deviation = seconds_typing - typeChoice

// Generate descriptive statistics for deviations by treatment
bysort treatment: sum deviation, detail

// Store treatment group statistics
preserve
collapse (mean) mean_dev=deviation (median) median_dev=deviation ///
         (sd) sd_dev=deviation (p25) p25_dev=deviation (p75) p75_dev=deviation ///
         (min) min_dev=deviation (max) max_dev=deviation (count) n_dev=deviation, by(treatment)
list
restore

// Generate boxplot statistics for deviations by treatment
foreach treat in 0 1 {
    egen med_dev_`treat' = median(deviation) if treatment == `treat'
    egen lqt_dev_`treat' = pctile(deviation) if treatment == `treat', p(25)
    egen uqt_dev_`treat' = pctile(deviation) if treatment == `treat', p(75)
    egen iqr_stat_dev_`treat' = iqr(deviation) if treatment == `treat'
    egen mean_stat_dev_`treat' = mean(deviation) if treatment == `treat'
    gen l_dev_`treat' = deviation if (deviation >= lqt_dev_`treat' - 1.5*iqr_stat_dev_`treat') & treatment == `treat'
    egen ls_dev_`treat' = min(l_dev_`treat')
    gen u_dev_`treat' = deviation if (deviation <= uqt_dev_`treat' + 1.5*iqr_stat_dev_`treat') & treatment == `treat'
    egen us_dev_`treat' = max(u_dev_`treat')
}

// Set positions for boxplots
gen ypos_control = -2    // Position for control boxplot
gen ypos_autoplay = -4   // Position for autoplay boxplot

// Calculate range for deviation variable
sum deviation
local min = r(min)
local max = r(max)
local n = r(N)
local bins = 11
local width = (`max'-`min')/`bins'

// Create the dual histogram with boxplots by treatment
twoway (histogram deviation if treatment == 0, percent start(`min') width(`width') ///
        fcolor(orange%60) lcolor(gs4) lwidth(thin)) ///
       (histogram deviation if treatment == 1, percent start(`min') width(`width') ///
        fcolor(dknavy%60) lcolor(gs4) lwidth(thin)) ///
       || rbar lqt_dev_0 uqt_dev_0 ypos_control, horiz fcolor(orange*.7) lcolor(gs4) barw(1.2) ///
       || rbar med_dev_0 uqt_dev_0 ypos_control, horiz fcolor(orange*.7) lcolor(gs4) barw(1.2) ///
       || rspike lqt_dev_0 ls_dev_0 ypos_control, horiz lcolor(gs4) ///
       || rspike uqt_dev_0 us_dev_0 ypos_control, horiz lcolor(gs4) ///
       || rcap ls_dev_0 ls_dev_0 ypos_control, horiz msize(*1) lcolor(gs4) ///
       || rcap us_dev_0 us_dev_0 ypos_control, horiz msize(*1) lcolor(gs4) ///
       || scatter ypos_control mean_stat_dev_0, msymbol(o) msize(*.5) fcolor(gs4) mcolor(gs4) ///
       || rbar lqt_dev_1 uqt_dev_1 ypos_autoplay, horiz fcolor(dknavy*.7) lcolor(gs4) barw(1.2) ///
       || rbar med_dev_1 uqt_dev_1 ypos_autoplay, horiz fcolor(dknavy*.7) lcolor(gs4) barw(1.2) ///
       || rspike lqt_dev_1 ls_dev_1 ypos_autoplay, horiz lcolor(gs4) ///
       || rspike uqt_dev_1 us_dev_1 ypos_autoplay, horiz lcolor(gs4) ///
       || rcap ls_dev_1 ls_dev_1 ypos_autoplay, horiz msize(*1) lcolor(gs4) ///
       || rcap us_dev_1 us_dev_1 ypos_autoplay, horiz msize(*1) lcolor(gs4) ///
       || scatter ypos_autoplay mean_stat_dev_1, msymbol(o) msize(*.5) fcolor(gs4) mcolor(gs4) ///
       , xlabel(-1(0.2)1, gmin gmax) ///
         ylabel(0(10)50, gmax angle(0)) ///
         ytitle("Percent") ///
         xtitle("Actual - Planned Typing (%)") ///
         legend(order(1 "Control" 2 "Autoplay") ring(0) pos(12) rows(1) region(lcolor(none))) ///
         title("Deviations from Time Choice by Treatment") ///
         graphregion(color(white)) bgcolor(white) ///
         name(deviation_hist, replace)

graph export "${fpath}deviation_hist.png", replace


// Two-sample t-test for mean differences
ttest deviation, by(treatment)
scalar ttest_pval = r(p)

ksmirnov deviation, by(treatment)
