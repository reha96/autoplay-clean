/*******************************************************************************
    Project: autoplay
    Author: Reha Tuncer
    Date: 02.07.2025
    Description: figure histogram time choice vs seconds typed - DUAL DISTRIBUTION
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
	
use "${dpath}cleaned_autoplay_data.dta", replace

preserve
// Generate descriptive statistics for both distributions
foreach var in typeChoice seconds_typing {
    quietly sum `var', detail
    scalar mean_`var' = r(mean)
    scalar median_`var' = r(p50)
    scalar sd_`var' = r(sd)
    scalar min_`var' = r(min)
    scalar max_`var' = r(max)
    scalar p25_`var' = r(p25)
    scalar p75_`var' = r(p75)
    scalar iqr_`var' = r(p75) - r(p25)
    scalar n_`var' = r(N)
}

// Generate boxplot statistics for both variables
foreach var in typeChoice seconds_typing {
    egen med_`var' = median(`var')
    egen lqt_`var' = pctile(`var'), p(25)
    egen uqt_`var' = pctile(`var'), p(75)
    egen iqr_stat_`var' = iqr(`var')
    egen mean_stat_`var' = mean(`var')
    gen l_`var' = `var' if(`var' >= lqt_`var' - 1.5*iqr_stat_`var')
    egen ls_`var' = min(l_`var')
    gen u_`var' = `var' if(`var' <= uqt_`var' + 1.5*iqr_stat_`var')
    egen us_`var' = max(u_`var')
}

// Set positions for boxplots
gen ypos_tc = -2    // Position for typeChoice boxplot
gen ypos_st = -4    // Position for seconds_typing boxplot

// Calculate common range for both variables
sum typeChoice
local min1 = r(min)
local max1 = r(max)
local n1 = r(N)
sum seconds_typing
local min2 = r(min)
local max2 = r(max)
local n2 = r(N)
local min = min(`min1',`min2')
local max = max(`max1',`max2')
local n = min(`n1',`n2')
local bins = 15
local width = (`max'-`min')/`bins'

// Create the dual histogram with boxplots
twoway (histogram seconds_typing, percent start(`min') width(`width') ///
        fcolor(orange%60) lcolor(gs4) lwidth(thin)) ///
       (histogram typeChoice, percent start(`min') width(`width') ///
        fcolor(dknavy%60) lcolor(gs4) lwidth(thin)) ///
       || rbar lqt_typeChoice uqt_typeChoice ypos_tc, horiz fcolor(dknavy*.7) lcolor(gs4) barw(1.2) ///
       || rbar med_typeChoice uqt_typeChoice ypos_tc, horiz fcolor(dknavy*.7) lcolor(gs4) barw(1.2) ///
       || rspike lqt_typeChoice ls_typeChoice ypos_tc, horiz lcolor(gs4) ///
       || rspike uqt_typeChoice us_typeChoice ypos_tc, horiz lcolor(gs4) ///
       || rcap ls_typeChoice ls_typeChoice ypos_tc, horiz msize(*1) lcolor(gs4) ///
       || rcap us_typeChoice us_typeChoice ypos_tc, horiz msize(*1) lcolor(gs4) ///
       || scatter ypos_tc mean_stat_typeChoice, msymbol(o) msize(*.5) fcolor(gs4) mcolor(gs4) ///
       || rbar lqt_seconds_typing uqt_seconds_typing ypos_st, horiz fcolor(orange*.7) lcolor(gs4) barw(1.2) ///
       || rbar med_seconds_typing uqt_seconds_typing ypos_st, horiz fcolor(orange*.7) lcolor(gs4) barw(1.2) ///
       || rspike lqt_seconds_typing ls_seconds_typing ypos_st, horiz lcolor(gs4) ///
       || rspike uqt_seconds_typing us_seconds_typing ypos_st, horiz lcolor(gs4) ///
       || rcap ls_seconds_typing ls_seconds_typing ypos_st, horiz msize(*1) lcolor(gs4) ///
       || rcap us_seconds_typing us_seconds_typing ypos_st, horiz msize(*1) lcolor(gs4) ///
       || scatter ypos_st mean_stat_seconds_typing, msymbol(o) msize(*.5) fcolor(gs4) mcolor(gs4) ///
       , xlabel(0(.125)1, format(%9.0g)) ///
         ylabel(0(5)30, gmax angle(0)) ///
         ytitle("Percent") ///
         xtitle("Proportion of 20 min. for typing") ///
         legend(order(1 "Actual" 2 "Planned") ring(0) pos(10) rows(2) region(lcolor(none))) ///
         title("Distribution of Planned vs Actual Typing Time") ///
         graphregion(color(white)) bgcolor(white) ///
         name(dual_hist, replace)

graph export "${fpath}dual_typechoice_hist.png", replace

// Display comparative descriptive statistics
display ""
display "DESCRIPTIVE STATISTICS COMPARISON"
display "=================================="
display ""
display _col(20) "Planned" _col(35) "Actual" 
display "Variable" _col(20) "(typeChoice)" _col(35) "(seconds_typing)"
display "--------" _col(20) "------------" _col(35) "---------------"
display "N" _col(20) %8.0f n_typeChoice _col(35) %8.0f n_seconds_typing
display "Mean" _col(20) %8.3f mean_typeChoice _col(35) %8.3f mean_seconds_typing
display "Median" _col(20) %8.3f median_typeChoice _col(35) %8.3f median_seconds_typing
display "Std Dev" _col(20) %8.3f sd_typeChoice _col(35) %8.3f sd_seconds_typing
display "Min" _col(20) %8.3f min_typeChoice _col(35) %8.3f min_seconds_typing
display "Max" _col(20) %8.3f max_typeChoice _col(35) %8.3f max_seconds_typing
display "25th pct" _col(20) %8.3f p25_typeChoice _col(35) %8.3f p25_seconds_typing
display "75th pct" _col(20) %8.3f p75_typeChoice _col(35) %8.3f p75_seconds_typing
display "IQR" _col(20) %8.3f iqr_typeChoice _col(35) %8.3f iqr_seconds_typing
display ""

// Calculate difference in means and test
scalar diff_means = mean_typeChoice - mean_seconds_typing
ttest typeChoice == seconds_typing
scalar ttest_pval = r(p)

display "MEAN COMPARISON"
display "==============="
display "Difference (Planned - Actual): " %8.3f diff_means
display "T-test p-value: " %8.4f ttest_pval
display ""

// Kolmogorov-Smirnov test for distribution equality
ksmirnov typeChoice = seconds_typing
scalar ks_statistic = r(D)
scalar ks_pval = r(p_cor)  // Corrected p-value

display "KOLMOGOROV-SMIRNOV TEST"
display "======================="
display "H0: Distributions are identical"
display "KS statistic (D): " %8.4f ks_statistic
display "P-value: " %8.4f ks_pval
if ks_pval < 0.05 {
    display "Result: Reject H0 at 5% level - distributions are significantly different"
}
else {
    display "Result: Fail to reject H0 at 5% level - no significant difference in distributions"
}
display ""

// Store results in a matrix for potential export
matrix descriptives = (mean_typeChoice, median_typeChoice, sd_typeChoice, p25_typeChoice, p75_typeChoice, min_typeChoice, max_typeChoice, n_typeChoice \ ///
                      mean_seconds_typing, median_seconds_typing, sd_seconds_typing, p25_seconds_typing, p75_seconds_typing, min_seconds_typing, max_seconds_typing, n_seconds_typing)
matrix rownames descriptives = "Planned" "Actual"
matrix colnames descriptives = "Mean" "Median" "Std_Dev" "P25" "P75" "Min" "Max" "N"

display "SUMMARY MATRIX"
display "=============="
matrix list descriptives

restore
