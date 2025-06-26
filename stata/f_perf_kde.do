/*******************************************************************************
    Project: icfes referrals 
    Author: Reha Tuncer
    Date: 18.03.2025
    Description: figure performance by SES
*******************************************************************************/
global dpath "/Users/reha.tuncer/Documents/GitHub/icfes-referrals/stata/"
global fpath "/Users/reha.tuncer/Documents/GitHub/icfes-referrals/figures/"
set scheme s2color, permanently

use "appended.dta", clear
bysort other_id: egen avg_score = mean(z_other_score)
bysort other_id: keep if _n == 1
tabstat avg_score, by(otprogram) stat(mean sd semean n)

use "appended.dta", clear
keep if own_estrato == 1
bysort own_id: egen avg_score_low = mean(z_other_score) if other_estrato == 1
bysort own_id: egen avg_score_mid = mean(z_other_score)  if other_estrato == 2
bysort own_id: egen avg_score_high = mean(z_other_score)  if other_estrato == 3
tabstat avg_score_low avg_score_mid avg_score_high, by(other_estrato) stat(mean sd semean n)

use "appended.dta", clear
keep if own_estrato == 2
bysort own_id: egen avg_score_low = mean(z_other_score) if other_estrato == 1
bysort own_id: egen avg_score_mid = mean(z_other_score)  if other_estrato == 2
bysort own_id: egen avg_score_high = mean(z_other_score)  if other_estrato == 3
tabstat avg_score_low avg_score_mid avg_score_high, by(other_estrato) stat(mean sd semean n)

use "appended.dta", clear
keep if own_estrato == 3
bysort own_id: egen avg_score_low = mean(z_other_score) if other_estrato == 1
bysort own_id: egen avg_score_mid = mean(z_other_score)  if other_estrato == 2
bysort own_id: egen avg_score_high = mean(z_other_score)  if other_estrato == 3
tabstat avg_score_low avg_score_mid avg_score_high, by(other_estrato) stat(mean sd semean n)


twoway (kdensity other_score if other_estrato == 1) ///
(kdensity other_score if other_estrato == 2) /// 
(kdensity other_score if other_estrato == 3)

