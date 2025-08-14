#! /bin/zsh

input_folder=~/Downloads/statements_poc/staging
target_folder=~/Downloads/statements_poc/sorted

# Clear log
echo "" > app.log

clear
# Normal run
uv run main.py -fi ipay -f extract-transactions --input-folder=${input_folder} --target-folder=${target_folder} -v


echo "overriding some ipay info. press enter to continue"
read -r
sh scripts/private/override_some_ipay_info.sh

echo 'asserting pay summaries, press enter to continue'
read -r 

sh scripts/assert_pay_summaries.sh

echo 'done'