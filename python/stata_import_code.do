
* Stata import code:
import delimited "stata_dataset.csv", clear

* Set panel structure
xtset participant_id second

* Label variables
label variable participant_id "Participant ID"
label variable second "Second (0-1199)"
label variable work "Work indicator (1=typing, 0=watching)"
label variable cumulative_work "Cumulative work time"
label variable mouseout "Mouseout >20s indicator"
label variable treatment "Treatment assignment"
label variable timeChoice "Initial time choice preference"
label variable typeCount "Number of typing actions"
label variable watchedVideo "Amount of video watched"
label variable behavior_type "Behavioral classification"
label variable work_ratio "Overall work ratio"

* Create treatment dummy
encode treatment, generate(treatment_num)
generate autoplay = (treatment_num == 1) if !missing(treatment_num)
label variable autoplay "Autoplay treatment (1=on, 0=off)"

* Summary statistics
summarize
xtsum work

* Correlation matrix for key variables
correlate timeChoice typeCount watchedVideo work_ratio
