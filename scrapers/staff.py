# shebang to be added
"""
# Crawler to scrape job postings and company information from https://staff.am/en/jobs
"""

from typing import Any, List, Set, Dict, Union

import os
import re, json, time, datetime

from dotenv import load_dotenv

import requests
import scrapy

import pandas as pd


# Data Types
ExtractedData = Dict[str, Union[List[Any]]]

# URL variables
load_dotenv()
BASE_URL: str = os.getenv("BASE_URL") # "https://staff.am"
MAIN_URL: str = BASE_URL + os.getenv("MAIN_URL_ENDPOINT") # "/en/jobs"

# Other Variables
extracted_data: ExtractedData


# Function to relative paths to job postings from a given page response
def get_relative_paths_from_one_page(
    page_response: scrapy.http.HtmlResponse
) -> List[str]:
    relative_paths = (
        page_response
        .css("div.web_item_card.hs_job_list_item a.load-more::attr(href)")
        .getall()
    )
    return relative_paths

# Function to get relative paths for all pages
def get_relative_paths_for_all_pages(
    first_page_response: scrapy.http.HtmlResponse,
    base_url: str,
    delay: int=1
) -> List[str]:

    response = first_page_response
    relative_paths = []

    while response.css("li.next a").get() is not None:

        relative_paths.extend(
            get_relative_paths_from_one_page(response)
        )
        rs = requests.get(
            base_url + response.css("li.next a::attr(href)").get()
        )
        response = scrapy.http.HtmlResponse(
            url=rs.url, body=rs.text, encoding="utf-8"
        )
        time.sleep(delay)

    # Adding relative paths of last page
    relative_paths.extend(
        get_relative_paths_from_one_page(response)
    )

    return relative_paths

# Function to collect data from one job posting
def get_info_from_one_posting(absolute_path: str) -> ExtractedData:

    rs = requests.get(absolute_path)
    response = scrapy.http.HtmlResponse(
        url=rs.url, body=rs.text, encoding="utf-8"
    )

    all_default_keys = (
        "Company_Title", "Company_URL", "URL", "Total_views", "Followers",
        "Active_Jobs", "Jobs_History", "Job_Views", "Job_Title",
        "Application_Deadline", "Industry", "Employment_term",
        "Job_Category", "Job_type", "Job_Location",
        "Job_description", "Job_responsibilities",
        "Required_qualifications", "Required_candidate_level",
        "Salary", "Additional_information",
        "Professional_skills", "Soft_skills"
    )

    extracted_data = {
        "Company_Title": (
            response
            .css("div.company-info > div > a > h1::text")
            .get()
        ),
        "Company_URL": (
            response
            .css("div.company-info > div > a::attr(href)")
            .get()
        ),
        "URL": absolute_path,
        "Total_views": int(
            response
            .css("div.col-lg-7.company_info_container p.company-page-views span::text")
            .getall()[0]
        ),
        "Followers": int(
            response
            .css("div.col-lg-7.company_info_container p.company-page-views span::text")
            .getall()[1]
        ),
        "Active_Jobs": int(response.css("p.company-active-job span::text").get()),
        "Jobs_History": int(response.css("p.company-job-history span::text").get()),
        "Job_Views": int(re.search(
            "[0-9]+",
            response.css("div.statistics p::text").get()
        ).group()),
        "Job_Title": response.css("div.col-lg-8 h2::text").get(),
        "Application_Deadline": re.search(
            r"Deadline: (.*)\s",
            (
                response
                .css("div.col-lg-4.apply-btn-top p::text")
                .get()
                .replace("\n", " ")
            )
        ).group(1)
    }

    try:
        extracted_data["Industry"] = (
            response
            .css("div.col-lg-7.company_info_container p.professional-skills-description span::text")
            .getall()
            [-1]
        )
    except IndexError:
        extracted_data["Industry"] = "None"

    job_info = [
        i.strip()
        for i in response.css("div.col-lg-6.job-info p::text").getall()
        if i != "\n"
    ]

    for i, k in enumerate(
        [
            "Employment_term",
            "Job_Category",
            "Job_type",
            "Job_Location"
        ]
    ):
        extracted_data[k] = job_info[i]

    default_job_list_keys = [
        "Job_description", "Job_responsibilities", "Required_qualifications",
        "Required_candidate_level", "Salary", "Additional_information"
    ]
    job_list = response.css("div.job-list-content-desc.hs_line_break")
    job_list_keys = [
        i.strip().replace(":", "").replace(" ", "_")
        for i in job_list.css("h3::text").getall()
    ]

    if len(default_job_list_keys) < len(job_list_keys):
        print(
            """
            New 'h3' fields in job description list are present:
            \tCheck the output.
            """
        )

    for key in default_job_list_keys:
        if key not in job_list_keys:
            extracted_data[key] = "None"

    for cnt, h3 in enumerate(job_list.css('h3'), start=1):

        key = h3.css("::text").get().strip().replace(":", "").replace(" ", "_")

        if key in ["Required_candidate_level", "Salary"]:
            extracted_data[key] = h3.css("span::text").get()
        else:
            values = h3.xpath(
                "following-sibling::*[count(preceding-sibling::h3)=$cnt]",
                cnt=cnt
            )[:-1].css("::text").getall()
            extracted_data[key] = [
                value.strip()
                for value in values
                if value != "\n"
            ]

    skills_info_keys = [
        i.replace(" ", "_")
        for i in response.css("div.soft-skills-list.clearfix h3::text").getall()
    ]

    if "Professional_skills" in skills_info_keys:
        ind = skills_info_keys.index("Professional_skills")
        extracted_data["Professional_skills"] = (
            response
            .css("div.soft-skills-list.clearfix")[ind]
            .css("p span::text, .p::text")
            .getall()
        )
    else:
        extracted_data["Professional_skills"] = "None"
    if "Soft_skills" in skills_info_keys:
        ind = skills_info_keys.index("Soft_skills")
        extracted_data["Soft_skills"] = (
            response
            .css("div.soft-skills-list.clearfix")[ind]
            .css("p span::text, .p::text")
            .getall()
        )
    else:
        extracted_data["Soft_skills"] = "None"

    for key in all_default_keys:
        if key not in extracted_data.keys():
            print(
                f"""
                Default field: '{key}' is missing in extracted data.
                """
            )
            extracted_data[key] = "None"

    return extracted_data

# Function to collect data from all job postings given absolute paths
def crawl_all_postings(
    absolute_paths: List[str],
    delay: int=3
) -> ExtractedData:

    extracted_data = {}

    i = 1

    for path in absolute_paths:

        print(path)
        print(
            str(i) + "/" + str(len(absolute_paths)),
            "Est.: " + str(round((10 * (len(absolute_paths) - i))/60, 2)) + "m."
        )
        i += 1
        extracted_data_from_posting = get_info_from_one_posting(path)

        for key, value in extracted_data_from_posting.items():
            if key not in extracted_data.keys():
                extracted_data[key] = []
            extracted_data[key].append(value)

        with open("log.json", "w", encoding="utf-8") as l:
            json.dump(extracted_data, l, ensure_ascii=False)

        time.sleep(delay)

    return extracted_data

# Function to collect data for a single company
def crawl_company_info(url: str) -> ExtractedData:
    rs = requests.get(BASE_URL + url)
    response = scrapy.http.HtmlResponse(
        url=rs.url, body=rs.text, encoding="utf-8"
    )

    return {
        "Company_Title": (
            response
            .css("div.company-title-views > h1::text")
            .get()
        ),
        "Company_URL": url,
        "Page views": int(
            response
            .css("p.company-page-views > span::text")
            .get()
        ),
        "Followers": int(
            response
            .css("p.company-page-views > span#followers_count::text")
            .get()
        ),
        "Active_jobs": int(
            response
            .css("p.company-active-job > a > span::text")
            .get()
        ),
        "Job_history": int(
            response
            .css("p.company-job-history > span::text")
            .get()
        ),
        "Info": "".join(
            response
            .css("div.hs_text_block ::text")
            .getall()
        ),
        "Industry": (
            response
            .css("td:contains('Industry:')~td ::text")
            .get()
        ),
        "Type": (
            response
            .css("td:contains('Type:')~td ::text")
            .get()
        ),
        "Number_of_Employees": (
            response
            .css("span:contains('Number of Employees:')~span ::text")
            .get()
        ),
        "Location": (
            response
            .css("span:contains('Location:')~span ::text")
            .get()
        ),
        "Website": (
            response
            .css("a.hs_company_website_btn::attr(href)")
            .get()
        ),
        "Benefits": ( # List[str]
            response
            .css("div.hs_benefit_view_block > div > div > span ::text")
            .getall()
        ),
        "Contacts": ( # List[str]
            response
            .css("div.mt15 > a::attr(href)")
            .getall()
        ),
        "Geolocation": list(map( # List[float]
            float,
            re.search(
                "q=(([0-9]+\.[0-9]+,?){2})&",
                response.css("iframe::attr(src)").getall()[-1]
            ).group(1).split(",")
        ))
    }


# Function to collect data about companies
def crawl_all_companies(
    absolute_paths_companies: Union[List[str], Set[str]]
) -> ExtractedData:
    extracted_data = {}
    for url in absolute_paths_companies:
        company_data = crawl_company_info(url)

        for key, value in company_data.items():
            if key not in extracted_data.keys():
                extracted_data[key] = []
            extracted_data[key].append(value)

    return extracted_data

# Function to make dict data to be saved as csv
def format_to_csv(data: ExtractedData) -> ExtractedData:

    keys_to_format = (
        "Job_description", "Job_responsibilities", "Required_qualifications",
        "Additional_information", "Professional_skills", "Soft_skills"
    )

    for key, value in data.items():
        if key in keys_to_format:
            data[key] = "\n".join(value)

    return data

# Function to save the data in a given file format
def save_files(data: ExtractedData, *formats) -> None:

    date = datetime.date.today().strftime("%d.%m.%y")

    for ext in formats:

        if ext not in ("csv", "json"):
            print(
                f"""
                Can't save in {ext} format.\nSaving both to 'csv' and 'json'.
                """
            )
            save_files(data, "csv", "json")
            break
        elif ext == "csv":
            # TODO: Implement properly
            data_csv = format_to_csv(data)
            try:
                data_csv = pd.DataFrame(data_csv)
                data_csv.to_csv("staff_" + date + ".csv")
            except ValueError:
                print(
                    """
                    Unable to save 'csv': missing values are present.
                    Saving to 'json'
                    """
                )
                save_files(data, "json")
                break
        elif ext == "json":
            with open("staff_" + date + ".json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)


# Main function
def main() -> ExtractedData:
    start_time = time.ctime()
    print(start_time)
    print(f"Starting crawling '{BASE_URL}'.")
    rs = requests.get(MAIN_URL)
    response = scrapy.http.HtmlResponse(
        url=rs.url, body=rs.text, encoding="utf-8"
    )

    relative_paths = get_relative_paths_for_all_pages(
        response, BASE_URL, delay=1
    )
    absolute_paths = [BASE_URL + path for path in relative_paths]

    print(str(len(absolute_paths)) + " jobs detected.")
    print("Starting crawling job postings..")

    # NOTE: Added index slice for testing purposes, remove for production
    extracted_data = crawl_all_postings(absolute_paths[:])

    # TODO: Implement company info crawling here
    company_urls = extracted_data["Company_URL"]

    with open("../data/companies/companies.json", "r") as f:
        available_companies = json.load(f)["Company_URL"]

    new_companies = set(company_urls) - set(available_companies)

    print(f"Detected {len(new_companies)} new companies.")
    print("Starting crawling comanies.")

    extracted_companies = crawl_all_companies(new_companies)

    print(
        f"Extracted {len(extracted_companies["Company_URL"])}/{len(new_companies)}"
    )




    end_time = time.ctime()
    print(end_time)
    print(f"Ended crawling '{BASE_URL}'.")

    print(
        str(len(extracted_data["URL"])) + "/" +
        str(len(absolute_paths)) + " jobs scraped."
    )
    print("Saving files.")

    for key in extracted_data.keys():
    	print(key + ": " + str(len(extracted_data[key])))

    save_files(extracted_data, "json")

    return extracted_data


if __name__ == '__main__':
	extracted_data = main()
