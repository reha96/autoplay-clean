/*******************************************************************************
    Project: icfes referrals 
    Author: Reha Tuncer
    Date: 18.03.2025
    Description: figures reading/math combined
*******************************************************************************/
global dpath "/Users/reha.tuncer/Documents/GitHub/icfes-referrals/stata/"
global fpath "/Users/reha.tuncer/Documents/GitHub/icfes-referrals/figures/"
set scheme s2color, permanently

	

keep if nomination
keep own_id tie other_score
collapse (mean) tie other_score , by(own_id)
rename tie tie_R
rename other_score other_score_R
save "${dpath}temp.dta", replace

clear all
use "${dpath}dataset_z.dta", clear
collapse (mean) tie other_score , by(own_id)
rename tie tie_N
rename other_score other_score_N
merge 1:1 own_id using "${dpath}temp.dta"
	
preserve	
foreach var in _R _N {
	egen med`var' = median(tie`var')
    egen lqt`var' = pctile(tie`var'), p(25)
    egen uqt`var' = pctile(tie`var'), p(75)
    egen iqr`var' = iqr(tie`var')
    egen mean`var' = mean(tie`var')
    gen l`var' = tie`var' if(tie`var' >= lqt`var'-1.5*iqr`var')
    egen ls`var' = min(l`var')
    gen u`var' =tie`var' if(tie`var' <= uqt`var'+1.5*iqr`var')
    egen us`var' = max(u`var')
}
gen ypos2 = -1.5
gen ypos = -3


// draw
sum tie_R
local min1 = r(min)
local max1 = r(max)
local n1 = r(N)
sum tie_N
local min2 = r(min)
local max2 = r(max)
local n2 = r(N)
local min = min(`min1',`min2')
local max = max(`max1',`max2')
local n = min(`n1',`n2')
local bins = 20
local width = (`max'-`min')/`bins'
    
twoway  (histogram tie_N, percent start(`min') width(`width') fcolor(orange%60) lcolor(gs4) lwidth(thin)) ///
(histogram tie_R, percent start(`min') width(`width') fcolor(dknavy%60) lcolor(gs4) lwidth(thin)) ///
       || rbar lqt_R uqt_R ypos, horiz fcolor(dknavy*.7) lcolor(gs4) barw(1.2) ///
       || rbar med_R uqt_R ypos, horiz fcolor(dknavy*.7) lcolor(gs4) barw(1.2) ///
       || rspike lqt_R ls_R ypos, horiz lcolor(gs4) ///
       || rspike uqt_R us_R ypos, horiz lcolor(gs4) ///
       || rcap ls_R ls_R ypos, horiz msize(*1) lcolor(gs4) ///
       || rcap us_R us_R ypos, horiz msize(*1) lcolor(gs4) ///
       || scatter ypos mean_R, msymbol(o) msize(*.5) fcolor(gs4) mcolor(gs4) ///
       || rbar lqt_N uqt_N ypos2, horiz fcolor(orange*.7) lcolor(gs4) barw(1.2) ///
       || rbar med_N uqt_N ypos2, horiz fcolor(orange*.7) lcolor(gs4) barw(1.2) ///
       || rspike lqt_N ls_N ypos2, horiz lcolor(gs4) ///
       || rspike uqt_N us_N ypos2, horiz lcolor(gs4) ///
       || rcap ls_N ls_N ypos2, horiz msize(*1) lcolor(gs4) ///
       || rcap us_N us_N ypos2, horiz msize(*1) lcolor(gs4) ///
       || scatter ypos2 mean_N, msymbol(o) msize(*.5) fcolor(gs4) mcolor(gs4) ///
       , xlabel(0(5)50) ///
         ylabel(0(10)60, gmax angle(0)) ///
         ytitle("Percent") ///
         xtitle("Nb. courses taken together ") ///
         legend(order(1 "Network" 2 "Referral") ring(0) pos(12) rows(1) region(lcolor(none))) ///
         title("Average courses taken for network and referrals") ///
         graphregion(color(white)) bgcolor(white) ///
         name(tie_hist, replace)
		  
    graph export "${fpath}tie_hist.png", replace
restore
	
	
	
/////////////////////////////
preserve	
// Generate descriptive statistics for both distributions
foreach var in tie_R tie_N {
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

// Display descriptive statistics table
display ""
display "DESCRIPTIVE STATISTICS COMPARISON"
display "=================================="
display ""
display _col(20) "Referrals" _col(35) "Network" 
display "Variable" _col(20) "(tie_R)" _col(35) "(tie_N)"
display "--------" _col(20) "-------" _col(35) "-------"
display "N" _col(20) %8.0f n_tie_R _col(35) %8.0f n_tie_N
display "Mean" _col(20) %8.2f mean_tie_R _col(35) %8.2f mean_tie_N
display "Median" _col(20) %8.2f median_tie_R _col(35) %8.2f median_tie_N
display "Std Dev" _col(20) %8.2f sd_tie_R _col(35) %8.2f sd_tie_N
display "Min" _col(20) %8.2f min_tie_R _col(35) %8.2f min_tie_N
display "Max" _col(20) %8.2f max_tie_R _col(35) %8.2f max_tie_N
display "25th pct" _col(20) %8.2f p25_tie_R _col(35) %8.2f p25_tie_N
display "75th pct" _col(20) %8.2f p75_tie_R _col(35) %8.2f p75_tie_N
display "IQR" _col(20) %8.2f iqr_tie_R _col(35) %8.2f iqr_tie_N
display ""

// Calculate difference in means and test
scalar diff_means = mean_tie_R - mean_tie_N
ttest tie_R == tie_N
scalar ttest_pval = r(p)

display "MEAN COMPARISON"
display "==============="
display "Difference (Referrals - Network): " %8.2f diff_means
display "T-test p-value: " %8.4f ttest_pval
display ""

// Kolmogorov-Smirnov test
ksmirnov tie_R = tie_N
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
matrix descriptives = (mean_tie_R, median_tie_R, sd_tie_R, p25_tie_R, p75_tie_R, min_tie_R, max_tie_R, n_tie_R \ ///
                      mean_tie_N, median_tie_N, sd_tie_N, p25_tie_N, p75_tie_N, min_tie_N, max_tie_N, n_tie_N)
matrix rownames descriptives = "Referrals" "Network"
matrix colnames descriptives = "Mean" "Median" "Std_Dev" "P25" "P75" "Min" "Max" "N"

display "SUMMARY MATRIX"
display "=============="
matrix list descriptives

//////////////////////////	
	
preserve	
foreach var in _R _N {
	egen med`var' = median(other_score`var')
    egen lqt`var' = pctile(other_score`var'), p(25)
    egen uqt`var' = pctile(other_score`var'), p(75)
    egen iqr`var' = iqr(other_score`var')
    egen mean`var' = mean(other_score`var')
    gen l`var' = other_score`var' if(other_score`var' >= lqt`var'-1.5*iqr`var')
    egen ls`var' = min(l`var')
    gen u`var' = other_score`var' if(other_score`var' <= uqt`var'+1.5*iqr`var')
    egen us`var' = max(u`var')
}
gen ypos2 = -1.5
gen ypos = -3
// draw
sum other_score_R
local min1 = r(min)
local max1 = r(max)
local n1 = r(N)
sum other_score_N
local min2 = r(min)
local max2 = r(max)
local n2 = r(N)
local min = min(`min1',`min2')
local max = max(`max1',`max2')
local n = min(`n1',`n2')
local bins = 20
local width = (`max'-`min')/`bins'
    
twoway  (histogram other_score_N, percent start(`min') width(`width') fcolor(orange%60) lcolor(gs4) lwidth(thin)) ///
(histogram other_score_R, percent start(`min') width(`width') fcolor(dknavy%60) lcolor(gs4) lwidth(thin)) ///
       || rbar lqt_R uqt_R ypos, horiz fcolor(dknavy*.7) lcolor(gs4) barw(1.2) ///
       || rbar med_R uqt_R ypos, horiz fcolor(dknavy*.7) lcolor(gs4) barw(1.2) ///
       || rspike lqt_R ls_R ypos, horiz lcolor(gs4) ///
       || rspike uqt_R us_R ypos, horiz lcolor(gs4) ///
       || rcap ls_R ls_R ypos, horiz msize(*1) lcolor(gs4) ///
       || rcap us_R us_R ypos, horiz msize(*1) lcolor(gs4) ///
       || scatter ypos mean_R, msymbol(o) msize(*.5) fcolor(gs4) mcolor(gs4) ///
       || rbar lqt_N uqt_N ypos2, horiz fcolor(orange*.7) lcolor(gs4) barw(1.2) ///
       || rbar med_N uqt_N ypos2, horiz fcolor(orange*.7) lcolor(gs4) barw(1.2) ///
       || rspike lqt_N ls_N ypos2, horiz lcolor(gs4) ///
       || rspike uqt_N us_N ypos2, horiz lcolor(gs4) ///
       || rcap ls_N ls_N ypos2, horiz msize(*1) lcolor(gs4) ///
       || rcap us_N us_N ypos2, horiz msize(*1) lcolor(gs4) ///
       || scatter ypos2 mean_N, msymbol(o) msize(*.5) fcolor(gs4) mcolor(gs4) ///
       , xlabel(30(10)100) ///
         ylabel(0(10)60, gmax angle(0)) ///
         ytitle("Percent") ///
         xtitle("Score") ///
         legend(order(1 "Network" 2 "Referral") ring(0) pos(12) rows(1) region(lcolor(none))) ///
         title("Average score of network and referrals") ///
         graphregion(color(white)) bgcolor(white) ///
         name(other_score_hist, replace)
		  
    graph export "${fpath}other_score_hist.png", replace
restore

preserve	

// Generate descriptive statistics for both distributions
foreach var in other_score_R other_score_N {
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

// Display descriptive statistics table
display ""
display "DESCRIPTIVE STATISTICS COMPARISON - ACADEMIC PERFORMANCE"
display "========================================================"
display ""
display _col(20) "Referrals" _col(35) "Network" 
display "Variable" _col(20) "(other_score_R)" _col(35) "(other_score_N)"
display "--------" _col(20) "---------------" _col(35) "---------------"
display "N" _col(20) %8.0f n_other_score_R _col(35) %8.0f n_other_score_N
display "Mean" _col(20) %8.2f mean_other_score_R _col(35) %8.2f mean_other_score_N
display "Median" _col(20) %8.2f median_other_score_R _col(35) %8.2f median_other_score_N
display "Std Dev" _col(20) %8.2f sd_other_score_R _col(35) %8.2f sd_other_score_N
display "Min" _col(20) %8.2f min_other_score_R _col(35) %8.2f min_other_score_N
display "Max" _col(20) %8.2f max_other_score_R _col(35) %8.2f max_other_score_N
display "25th pct" _col(20) %8.2f p25_other_score_R _col(35) %8.2f p25_other_score_N
display "75th pct" _col(20) %8.2f p75_other_score_R _col(35) %8.2f p75_other_score_N
display "IQR" _col(20) %8.2f iqr_other_score_R _col(35) %8.2f iqr_other_score_N
display ""

// Calculate difference in means and test
scalar diff_means = mean_other_score_R - mean_other_score_N
ttest other_score_R == other_score_N
scalar ttest_pval = r(p)

display "MEAN COMPARISON"
display "==============="
display "Difference (Referrals - Network): " %8.2f diff_means
display "T-test p-value: " %8.4f ttest_pval
display ""

// Kolmogorov-Smirnov test
ksmirnov other_score_R = other_score_N
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
matrix descriptives = (mean_other_score_R, median_other_score_R, sd_other_score_R, p25_other_score_R, p75_other_score_R, min_other_score_R, max_other_score_R, n_other_score_R \ ///
                      mean_other_score_N, median_other_score_N, sd_other_score_N, p25_other_score_N, p75_other_score_N, min_other_score_N, max_other_score_N, n_other_score_N)
matrix rownames descriptives = "Referrals" "Network"
matrix colnames descriptives = "Mean" "Median" "Std_Dev" "P25" "P75" "Min" "Max" "N"

display "SUMMARY MATRIX"
display "=============="
matrix list descriptives
