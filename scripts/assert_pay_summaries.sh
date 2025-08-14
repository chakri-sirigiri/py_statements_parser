#!/bin/zsh


source .env.totals
echo $G_2013_1
echo $N_2013_1

# Function to assert values match expected values
assert_values() {
    local year=$1
    echo "year: $year"
    local month=$2
    echo "month: $month"
    local expected_gross=$3
    echo "expected_gross: $expected_gross"
    local expected_net=$4
    echo "expected_net: $expected_net"
    
    echo "=== Asserting ${year}-${month} ==="
    
    # Check if expected values are provided
    if [ -z "$expected_gross" ]; then
        echo "⚠️  Expected gross pay not provided for ${year}-${month}"
        return 0
    fi
    
    if [ -z "$expected_net" ]; then
        echo "⚠️  Expected net pay not provided for ${year}-${month}"
        return 0
    fi
    
    # Validate that expected values are numeric (allow decimals)
    if ! [[ "$expected_gross" =~ ^[0-9]+\.?[0-9]*$ ]]; then
        echo "❌ Expected gross pay '$expected_gross' is not a valid number for ${year}-${month}"
        return 1
    fi
    
    if ! [[ "$expected_net" =~ ^[0-9]+\.?[0-9]*$ ]]; then
        echo "❌ Expected net pay '$expected_net' is not a valid number for ${year}-${month}"
        return 1
    fi
    
    # Format month with leading zero for SQL date comparison
    local month_padded=$(printf "%02d" $month)
    
    # Get actual values from database
    local select_query="SELECT SUM(gross_pay), SUM(net_pay) FROM transactions_adp WHERE statement_date BETWEEN '${year}-${month_padded}-01' AND '${year}-${month_padded}-31';"
    echo "select_query: $select_query"
    local result=$(sqlite3 transactions.db "$select_query")
    local actual_gross=$(echo "$result" | cut -d'|' -f1)
    local actual_net=$(echo "$result" | cut -d'|' -f2)
    
    # Handle NULL values
    if [ "$actual_gross" = "" ] || [ "$actual_gross" = "NULL" ]; then
        actual_gross="0"
    fi
    if [ "$actual_net" = "" ] || [ "$actual_net" = "NULL" ]; then
        actual_net="0"
    fi
    
    echo "Expected: Gross=$expected_gross, Net=$expected_net"
    echo "Actual:   Gross=$actual_gross, Net=$actual_net"
    
    # Assert gross pay using awk for floating point comparison
    if awk "BEGIN {exit !($actual_gross == $expected_gross)}"; then
        echo "✅ Gross pay assertion PASSED"
    else
        echo "❌ Gross pay assertion FAILED: Expected $expected_gross, got $actual_gross"
        exit 1
    fi
    
    # Assert net pay using awk for floating point comparison
    if awk "BEGIN {exit !($actual_net == $expected_net)}"; then
        echo "✅ Net pay assertion PASSED"
    else
        echo "❌ Net pay assertion FAILED: Expected $expected_net, got $actual_net"
        exit 1
    fi
    
    echo ""
}

# 2013
assert_values "2013" "1" ${G_2013_1} ${N_2013_1}
assert_values "2013" "2" ${G_2013_2} ${N_2013_2}
assert_values "2013" "3" ${G_2013_3} ${N_2013_3}
assert_values "2013" "4" ${G_2013_4} ${N_2013_4}
assert_values "2013" "5" ${G_2013_5} ${N_2013_5}
assert_values "2013" "6" ${G_2013_6} ${N_2013_6}
assert_values "2013" "7" ${G_2013_7} ${N_2013_7}
assert_values "2013" "8" ${G_2013_8} ${N_2013_8}
assert_values "2013" "9" ${G_2013_9} ${N_2013_9}
assert_values "2013" "10" ${G_2013_10} ${N_2013_10}
assert_values "2013" "11" ${G_2013_11} ${N_2013_11}
assert_values "2013" "12" ${G_2013_12} ${N_2013_12}

# 2014
assert_values "2014" "1" ${G_2014_1} ${N_2014_1}
assert_values "2014" "2" ${G_2014_2} ${N_2014_2}
assert_values "2014" "3" ${G_2014_3} ${N_2014_3}
assert_values "2014" "4" ${G_2014_4} ${N_2014_4}
assert_values "2014" "5" ${G_2014_5} ${N_2014_5}
assert_values "2014" "6" ${G_2014_6} ${N_2014_6}
assert_values "2014" "7" ${G_2014_7} ${N_2014_7}
assert_values "2014" "8" ${G_2014_8} ${N_2014_8}
assert_values "2014" "9" ${G_2014_9} ${N_2014_9}
assert_values "2014" "10" ${G_2014_10} ${N_2014_10}
assert_values "2014" "11" ${G_2014_11} ${N_2014_11}
assert_values "2014" "12" ${G_2014_12} ${N_2014_12}

# 2015
assert_values "2015" "1" ${G_2015_1} ${N_2015_1}
assert_values "2015" "2" ${G_2015_2} ${N_2015_2}
assert_values "2015" "3" ${G_2015_3} ${N_2015_3} 
assert_values "2015" "4" ${G_2015_4} ${N_2015_4}
assert_values "2015" "5" ${G_2015_5} ${N_2015_5}
assert_values "2015" "6" ${G_2015_6} ${N_2015_6}
assert_values "2015" "7" ${G_2015_7} ${N_2015_7}
assert_values "2015" "8" ${G_2015_8} ${N_2015_8}
assert_values "2015" "9" ${G_2015_9} ${N_2015_9}
assert_values "2015" "10" ${G_2015_10} ${N_2015_10}
assert_values "2015" "11" ${G_2015_11} ${N_2015_11}
assert_values "2015" "12" ${G_2015_12} ${N_2015_12}

# 2016
assert_values "2016" "1" ${G_2016_1} ${N_2016_1}
assert_values "2016" "2" ${G_2016_2} ${N_2016_2}
assert_values "2016" "3" ${G_2016_3} ${N_2016_3}
assert_values "2016" "4" ${G_2016_4} ${N_2016_4}
assert_values "2016" "5" ${G_2016_5} ${N_2016_5}
assert_values "2016" "6" ${G_2016_6} ${N_2016_6}
assert_values "2016" "7" ${G_2016_7} ${N_2016_7}
assert_values "2016" "8" ${G_2016_8} ${N_2016_8}
assert_values "2016" "9" ${G_2016_9} ${N_2016_9}
assert_values "2016" "10" ${G_2016_10} ${N_2016_10}
assert_values "2016" "11" ${G_2016_11} ${N_2016_11}
assert_values "2016" "12" ${G_2016_12} ${N_2016_12}

# 2017
assert_values "2017" "1" ${G_2017_1} ${N_2017_1}
assert_values "2017" "2" ${G_2017_2} ${N_2017_2}
assert_values "2017" "3" ${G_2017_3} ${N_2017_3}
assert_values "2017" "4" ${G_2017_4} ${N_2017_4}
assert_values "2017" "5" ${G_2017_5} ${N_2017_5}
assert_values "2017" "6" ${G_2017_6} ${N_2017_6}
assert_values "2017" "7" ${G_2017_7} ${N_2017_7}
assert_values "2017" "8" ${G_2017_8} ${N_2017_8}
assert_values "2017" "9" ${G_2017_9} ${N_2017_9}
assert_values "2017" "10" ${G_2017_10} ${N_2017_10}
assert_values "2017" "11" ${G_2017_11} ${N_2017_11}
assert_values "2017" "12" ${G_2017_12} ${N_2017_12}

# 2018
assert_values "2018" "1" ${G_2018_1} ${N_2018_1}
assert_values "2018" "2" ${G_2018_2} ${N_2018_2}
assert_values "2018" "3" ${G_2018_3} ${N_2018_3}
assert_values "2018" "4" ${G_2018_4} ${N_2018_4}
assert_values "2018" "5" ${G_2018_5} ${N_2018_5}
assert_values "2018" "6" ${G_2018_6} ${N_2018_6}
assert_values "2018" "7" ${G_2018_7} ${N_2018_7}
assert_values "2018" "8" ${G_2018_8} ${N_2018_8}
assert_values "2018" "9" ${G_2018_9} ${N_2018_9}
assert_values "2018" "10" ${G_2018_10} ${N_2018_10}
assert_values "2018" "11" ${G_2018_11} ${N_2018_11}
assert_values "2018" "12" ${G_2018_12} ${N_2018_12}

# 2019
assert_values "2019" "1" ${G_2019_1} ${N_2019_1}
assert_values "2019" "2" ${G_2019_2} ${N_2019_2}
assert_values "2019" "3" ${G_2019_3} ${N_2019_3}
assert_values "2019" "4" ${G_2019_4} ${N_2019_4}
assert_values "2019" "5" ${G_2019_5} ${N_2019_5}
assert_values "2019" "6" ${G_2019_6} ${N_2019_6}
assert_values "2019" "7" ${G_2019_7} ${N_2019_7}
assert_values "2019" "8" ${G_2019_8} ${N_2019_8}
assert_values "2019" "9" ${G_2019_9} ${N_2019_9}
assert_values "2019" "10" ${G_2019_10} ${N_2019_10}
assert_values "2019" "11" ${G_2019_11} ${N_2019_11}
assert_values "2019" "12" ${G_2019_12} ${N_2019_12}

# 2020
assert_values "2020" "1" ${G_2020_1} ${N_2020_1}
assert_values "2020" "2" ${G_2020_2} ${N_2020_2}
assert_values "2020" "3" ${G_2020_3} ${N_2020_3}
assert_values "2020" "4" ${G_2020_4} ${N_2020_4}
assert_values "2020" "5" ${G_2020_5} ${N_2020_5}
assert_values "2020" "6" ${G_2020_6} ${N_2020_6}
assert_values "2020" "7" ${G_2020_7} ${N_2020_7}
assert_values "2020" "8" ${G_2020_8} ${N_2020_8}
assert_values "2020" "9" ${G_2020_9} ${N_2020_9}
assert_values "2020" "10" ${G_2020_10} ${N_2020_10}
assert_values "2020" "11" ${G_2020_11} ${N_2020_11}
assert_values "2020" "12" ${G_2020_12} ${N_2020_12}

# 2021
assert_values "2021" "1" ${G_2021_1} ${N_2021_1}
assert_values "2021" "2" ${G_2021_2} ${N_2021_2}
assert_values "2021" "3" ${G_2021_3} ${N_2021_3}
assert_values "2021" "4" ${G_2021_4} ${N_2021_4}
assert_values "2021" "5" ${G_2021_5} ${N_2021_5}
assert_values "2021" "6" ${G_2021_6} ${N_2021_6}
assert_values "2021" "7" ${G_2021_7} ${N_2021_7}
assert_values "2021" "8" ${G_2021_8} ${N_2021_8}
assert_values "2021" "9" ${G_2021_9} ${N_2021_9}
assert_values "2021" "10" ${G_2021_10} ${N_2021_10}
assert_values "2021" "11" ${G_2021_11} ${N_2021_11}
assert_values "2021" "12" ${G_2021_12} ${N_2021_12}

# 2022
assert_values "2022" "1" ${G_2022_1} ${N_2022_1}
assert_values "2022" "2" ${G_2022_2} ${N_2022_2}
assert_values "2022" "3" ${G_2022_3} ${N_2022_3}
assert_values "2022" "4" ${G_2022_4} ${N_2022_4}
assert_values "2022" "5" ${G_2022_5} ${N_2022_5}
assert_values "2022" "6" ${G_2022_6} ${N_2022_6}
assert_values "2022" "7" ${G_2022_7} ${N_2022_7}
assert_values "2022" "8" ${G_2022_8} ${N_2022_8}
assert_values "2022" "9" ${G_2022_9} ${N_2022_9}
assert_values "2022" "10" ${G_2022_10} ${N_2022_10}
assert_values "2022" "11" ${G_2022_11} ${N_2022_11}
assert_values "2022" "12" ${G_2022_12} ${N_2022_12}

# 2023
assert_values "2023" "1" ${G_2023_1} ${N_2023_1}
assert_values "2023" "2" ${G_2023_2} ${N_2023_2}
assert_values "2023" "3" ${G_2023_3} ${N_2023_3}
assert_values "2023" "4" ${G_2023_4} ${N_2023_4}
assert_values "2023" "5" ${G_2023_5} ${N_2023_5}
assert_values "2023" "6" ${G_2023_6} ${N_2023_6}
assert_values "2023" "7" ${G_2023_7} ${N_2023_7}
assert_values "2023" "8" ${G_2023_8} ${N_2023_8}
assert_values "2023" "9" ${G_2023_9} ${N_2023_9}
assert_values "2023" "10" ${G_2023_10} ${N_2023_10}
assert_values "2023" "11" ${G_2023_11} ${N_2023_11}
assert_values "2023" "12" ${G_2023_12} ${N_2023_12}

# 2024
assert_values "2024" "1" ${G_2024_1} ${N_2024_1}
assert_values "2024" "2" ${G_2024_2} ${N_2024_2}
assert_values "2024" "3" ${G_2024_3} ${N_2024_3}
assert_values "2024" "4" ${G_2024_4} ${N_2024_4}
assert_values "2024" "5" ${G_2024_5} ${N_2024_5}
assert_values "2024" "6" ${G_2024_6} ${N_2024_6}
assert_values "2024" "7" ${G_2024_7} ${N_2024_7}
assert_values "2024" "8" ${G_2024_8} ${N_2024_8}
assert_values "2024" "9" ${G_2024_9} ${N_2024_9}
assert_values "2024" "10" ${G_2024_10} ${N_2024_10}
assert_values "2024" "11" ${G_2024_11} ${N_2024_11}
assert_values "2024" "12" ${G_2024_12} ${N_2024_12}

# 2025
assert_values "2025" "1" ${G_2025_1} ${N_2025_1}
assert_values "2025" "2" ${G_2025_2} ${N_2025_2}
assert_values "2025" "3" ${G_2025_3} ${N_2025_3}
assert_values "2025" "4" ${G_2025_4} ${N_2025_4}
assert_values "2025" "5" ${G_2025_5} ${N_2025_5}
assert_values "2025" "6" ${G_2025_6} ${N_2025_6}
assert_values "2025" "7" ${G_2025_7} ${N_2025_7}

echo "🎉 All assertions completed successfully!"

