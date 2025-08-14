# Overview
This file contains the patterns for the iPay statements, and guidelines for how to extract the data.

for pdfs ending with ytd, do not extract any data. coz this is the year-end summary. just continue to rename the file with pay data. example yyyy-mm-dd-ytd.pdf
for pdfs ending with bonus, do extract the bonus amount. and Statuary deductions (Federal, State, Local, Medicare, Social Security). do not extract any other data.
for pdfs ending with regular, do extract the regular pay amount. and Statuary deductions (Federal, State, Local, Medicare, Social Security). and other deductions (401K Loan Gp1, 401K Pretax, Dep Care, ESPP, FSA, etc).

in all bonus pdfs,
Gross pay = bonus amount
statuary deductions = sum of all statuary deductions (Federal, State, Local, Medicare, Social Security)
Net pay = extracted net pay value. if its 0, consider getting it from sum of all Checking* amounts

once extracted each of above values,
consider checking if net pay = gross pay - statuary deductions

in all regular pdfs,
Gross pay = sum of all income types (reguar, award, Contribution, Cola, Retro Contribtn, Retro Cola, retro pay)
statuary deductions = sum of all statuary deductions (Federal, State, Local, Medicare, Social Security)
other deductions = sum of all other deductions (401K Loan Gp1, 401K Pretax, Dep Care, ESPP, FSA, etc)
net pay = extracted net pay value. if its 0, consider getting it from sum of all Checking* amounts

once extracted each of above values,
consider checking if net pay = gross pay - statuary deductions - other deductions



in almost all pdfs,
there will be description followed by two values.
the first value is the amount for that paycheck, for that income/deduction.
the second value is the ytd amount for that paycheck, for that income/deduction.


##### Cola income, example 1
Cola 1 625 00
this paycheck's Cola income = $0
ytd paycheck's Cola income = $1,625.00

##### Cola income, example 2
Cola 125 00 $3 650 01
this paycheck's Cola income = $125.00
ytd paycheck's Cola income = $3,650.01

##### Cola income, example 3
Cola 125 00 * Excluded from federal taxable wages
this paycheck's Cola income = $0
ytd paycheck's Cola income = $125.00

##### Cola income, example 4
Cola 125 00 1 000 00 G T L 1 60 16 00
this paycheck's Cola income = $0
ytd paycheck's Cola income = $1,000.00

# Other income - Contribution income examples

##### Contribution income, example 1
Contribution 117 17 117 17
this paycheck's Contribution income = $117.17
ytd paycheck's Contribution income = $117.17

##### Contribution income, example 2
Contribution 117 17
this paycheck's Contribution income = $0
ytd paycheck's Contribution income = $117.17

##### Contribution income, example 3
Contribution 634 38 11 061 47
this paycheck's Contribution income = $634.38
ytd paycheck's Contribution income = $11,061.47

### Other Deductions

### Federal income tax deductions examples

##### Federal income tax deduction, example 1
Federal Income Tax -1 001 30 11 111 61
this paycheck's Federal income tax = $1,001.30
ytd paycheck's Federal income tax = $11,111.61

##### Federal income tax deduction, example 2
Federal Income Tax -1 001 30 22 222 91
this paycheck's Federal income tax = $1,001.30
ytd paycheck's Federal income tax = $22,222.91


#### 401K Loan Gp1 examples

##### 401K Loan Gp1, example 1
401K Loan Gp1 -123 12 1 234 56
this paycheck's 401K Loan Gp1 = $123.12
ytd paycheck's 401K Loan Gp1 = $1234.56

##### 401K Loan Gp1, example 2
401K Loan Gp1 -123 56 4 111 28
this paycheck's 401K Loan Gp1 = $123.56
ytd paycheck's 401K Loan Gp1 = $4111.28

#### 401K Pretax examples

##### 401K Pretax, example 1
401K Pretax -123 12* 1 234 56
this paycheck's 401K Pretax = $123.12
ytd paycheck's 401K Pretax = $1234.56

##### 401K Pretax, example 2
401K Pretax -1 234 57* 9 999 99
this paycheck's 401K Pretax = $1234.57
ytd paycheck's 401K Pretax = $9,999.99

##### 401K Pretax, example 3
401K Pretax 1 099 40
this paycheck's 401K Pretax = $0
ytd paycheck's 401K Pretax = $1,099.40

#### local income tax examples

##### local income tax, example 1
Brooklyn Income Tax -111 61 1 111 26
this paycheck's local income tax = $111.61
ytd paycheck's local income tax = $1111.26

##### local income tax, example 2
Brooklyn income tax -123 56 4 111 28
this paycheck's local income tax = $123.56
ytd paycheck's local income tax = $4111.28


##### local income tax, example 3
Cleveland Income Tax -111 61 1 111 26
this paycheck's local income tax = $111.61
ytd paycheck's local income tax = $1111.26

##### local income tax, example 4
Cleveland income tax -123 56 4 111 28
this paycheck's local income tax = $123.56
ytd paycheck's local income tax = $4111.28


#### Checking amount examples

##### Checking1 amount, example 1
Checking1 1 040 30 6 040 30
this paycheck's Checking amount = $1,040.30
ytd paycheck's Checking amount = $6,040.30

##### Checking1 amount, example 2
Checking1 4 489 62
this paycheck's Checking amount = $0
ytd paycheck's Checking amount = $4,489.62

#### Checking2 amount examples

##### Checking2 amount, example 1
Checking2 1 040 30
this paycheck's Checking amount = $0
ytd paycheck's Checking amount = $1,040.30

##### Checking3 amount, example 1
Checking3 1 040 30
this paycheck's Checking amount = $0
ytd paycheck's Checking amount = $1,040.30

#### Dep Care deductions examples

##### Dep Care deduction, example 1
Dep Care 1 040 30
this paycheck's Dep Care deduction = $0
ytd paycheck's Dep Care deduction = $1,040.30

##### Dep Care deduction, example 2
Dep Care 1 040 30 2 040 30
this paycheck's Dep Care deduction = $1,040.30
ytd paycheck's Dep Care deduction = $2,040.30


### ESPP deductions examples

##### ESPP deduction, example 1
Espp +991 02
this paycheck's ESPP deduction = $991.02
ytd paycheck's ESPP deduction = $991.02

##### ESPP deduction, example 2
Espp -467 80 1 403 40
this paycheck's ESPP deduction = $467.80
ytd paycheck's ESPP deduction = $1,403.40


* similar to ESPP, following other deduction examples holds true.
Hsa Plan
Illness Plan Lo
Legal
Life Ins
Pretax Dental
Pretax Medical
Pretax Vision
Pretax Dep Care
Pretax FSA
Pretax Hsa
Pretax 401K
Pretax 401K Loan Gp1
Taxable Off



* Similar to Federal income tax deductions, following other deduction examples holds true.
Social Security Tax
Medicare Tax
OH State Income Tax

* All below lines are considered local income tax deductions.
Brooklyn Income Tax
Cleveland Income Tax
NC State Income Tax

* Similar to Regular pay, following income examples holds true. all these fall under other_income column.
Award
Cola
Cola
Cola
Contribution
Contribution
Contribution
Pay
Performance 1
Performance 2
Performance 3
Performance 4
Performance 5
Performance 6
Performance 7
Retro Cola
Retro Cola
Retro Contribtn
Retro Contribtn
Retro Pay
Retro Skill Pay
Skillpay Allow
Taxable Perq
