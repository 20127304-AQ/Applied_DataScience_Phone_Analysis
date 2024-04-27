# Applied_DataScience_Phone_Analysis

## CRAWL DATA INSTRUCTION

## Set up
Before running the code, here are the pre-requisites:
+ Download the **Chromedriver** from [here](https://sites.google.com/chromium.org/driver/). Download the version that matches your current Chrome version. (In my case, I downloaded version 122.0.6261.94)
+ Install the required packages using the following command:
```
pip install -r requirements.txt
```
+ Make sure to have a stable internet connection.
+ Store the **Chromedriver** in the same directory as the source code. We will change the structure of the repository after the code is stable.

## How to run the code:
+ Run the following command:
```
python main.py
```
It will create a `data` folder containing the file with links to each product. 

To perform crawling, inside the notebook, change the name of the `data/some-name.csv` and replace the `some-name` with the current file name.

The execution time depends on the amount of data. 
***"Note: The crawl code can be run until 27/4/2024. There may be modifications to the code to address pop-ups or next-page buttons***
