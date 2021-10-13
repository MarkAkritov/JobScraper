# shebang to be added
"""
# Crawler to scrape job postings and company information from https://staff.am/en/jobs
"""

from typing import Any, List, Set, Dict, Union, Callable

import os
import re, json, time, datetime
from collections import defaultdict
from urllib.parse import urljoin

from dotenv import load_dotenv
from tqdm import tqdm

import requests
import scrapy

import pandas as pd


# Data Types
ExtractedData = Dict[str, Union[List[Any]]]

# URL variables
load_dotenv()
BASE_URL: str = os.getenv("BASE_URL") # "https://staff.am"
MAIN_URL: str = urljoin(BASE_URL, os.getenv("MAIN_URL_ENDPOINT")) # "/en/jobs"

# Other Variables
extracted_data: ExtractedData


# Function to handle request's selector as lmabda function to return None
def selector_handler(
    response: scrapy.http.HtmlResponse,
    selector: Callable[[scrapy.http.HtmlResponse], Any]
) -> Any:
    try:
        return selector(response)
    except:
        return None

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
    response: scrapy.http.HtmlResponse,
    base_url: str,
    delay: int=1
) -> List[str]:

    relative_paths = []

    while response.css("li.next a").get() is not None:

        relative_paths.extend(
            get_relative_paths_from_one_page(response)
        )
        rs = requests.get(
            urljoin(
                base_url,
                response.css("li.next a::attr(href)").get()
            )
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
        "Professional_skills", "Soft_skills", "Other"
    )

    extracted_data = {
        "Company_Title": selector_handler(
            response,
            lambda response: (
                response
                .css("div.company-info > div > a > h1::text")
                .get()
                .strip()
            )
        ),
        "Company_URL": selector_handler(
            response,
            lambda response: (
                response
                .css("div.company-info > div > a::attr(href)")
                .get()
            )
        ),
        "URL": absolute_path,
        "Total_views": selector_handler(
            response,
            lambda response: int(
                response
                .css("div.col-lg-7.company_info_container p.company-page-views span::text")
                .getall()[0]
            )
        ),
        "Followers": selector_handler(
            response,
            lambda response: int(
                response
                .css("div.col-lg-7.company_info_container p.company-page-views span::text")
                .getall()[1]
            )
        ),
        "Active_Jobs": selector_handler(
            response,
            lambda response: int(
                response
                .css("p.company-active-job span::text")
                .get()
            )
        ),
        "Jobs_History": selector_handler(
            response,
            lambda response: int(
                response
                .css("p.company-job-history span::text")
                .get()
            )
        ),
        "Job_Views": selector_handler(
            response,
            lambda response: int(
                re.search(
                    "[0-9]+",
                    response.css("div.statistics p::text").get()
                ).group()
            )
        ),
        "Job_Title": selector_handler(
            response,
            lambda response: response.css("div.col-lg-8 h2::text").get()
        ),
        "Application_Deadline": selector_handler(
            response,
            lambda response: re.search(
                r"Deadline: (.*)\s",
                (
                    response
                    .css("div.col-lg-4.apply-btn-top p::text")
                    .get()
                    .replace("\n", " ")
                )
            ).group(1)
        ),
        "Other": defaultdict(list)
    }

    try:
        extracted_data["Industry"] = selector_handler(
            response,
            lambda response: (
                response
                .css("div.col-lg-7.company_info_container p.professional-skills-description span::text")
                .getall()
                [-1]
            )
        )
    except IndexError:
        extracted_data["Industry"] = None

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
        try:
            extracted_data[k] = job_info[i]
        except IndexError:
            extracted_data[k] = None

    default_job_list_keys = [
        "Job_description", "Job_responsibilities", "Required_qualifications",
        "Required_candidate_level", "Salary",
    ]
    job_list = response.css("div.job-list-content-desc.hs_line_break")

    extracted_data["Text"] = "".join(job_list.css("::text").getall())

    job_list_keys = [
        i.strip().replace(":", "").replace(" ", "_")
        for i in job_list.css("h3::text").getall()
    ]

    for key in default_job_list_keys:
        if key not in job_list_keys:
            extracted_data[key] = None

    for cnt, h3 in enumerate(job_list.css('h3'), start=1):

        key = h3.css("::text").get().strip().replace(":", "").replace(" ", "_")

        if key in ["Required_candidate_level", "Salary"]:
            extracted_data[key] = h3.css("span::text").get()
        else:
            values = h3.xpath(
                "following-sibling::*[count(preceding-sibling::h3)=$cnt]",
                cnt=cnt
            )[:-1].css("::text").getall()
            info = [
                value.strip()
                for value in values
                if value != "\n"
            ]
            if key not in all_default_keys:
                extracted_data["Other"][key] = info
            else:
                extracted_data[key] = [
                    value.strip()
                    for value in values
                    if value != "\n"
                ]

    extracted_data["Additional_information"] = selector_handler(
        response,
        lambda response: "".join(
            response
            .css("div.additional-information.information_application_block ::text")
            .getall()
        )
    )

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
        extracted_data["Professional_skills"] = None

    if "Soft_skills" in skills_info_keys:
        ind = skills_info_keys.index("Soft_skills")
        extracted_data["Soft_skills"] = (
            response
            .css("div.soft-skills-list.clearfix")[ind]
            .css("p span::text, .p::text")
            .getall()
        )
    else:
        extracted_data["Soft_skills"] = None

    for key in all_default_keys:
        if key not in extracted_data.keys():
            print(
                f"""
                Default field: '{key}' is missing in extracted data.
                """
            )
            extracted_data[key] = None

    return extracted_data

# Function to collect data from all job postings given absolute paths
def crawl_all_postings(
    absolute_paths: List[str],
    delay: int=3
) -> ExtractedData:

    extracted_data = defaultdict(list)

    with tqdm(absolute_paths) as pbar:

        for path in pbar:

            # print(path)
            extracted_data_from_posting = get_info_from_one_posting(path)

            for key, value in extracted_data_from_posting.items():
                extracted_data[key].append(value)

            with open("log.json", "w", encoding="utf-8") as l:
                json.dump(extracted_data, l, ensure_ascii=False)

            time.sleep(delay)
            pbar.set_description(f"URL {path}")

    return extracted_data

# Function to collect data for a single company
def crawl_company_info(url: str) -> ExtractedData:
    rs = requests.get(urljoin(BASE_URL, url))
    response = scrapy.http.HtmlResponse(
        url=rs.url, body=rs.text, encoding="utf-8"
    )

    return {
        "Company_Title": selector_handler(
            response,
            lambda response: (
                response
                .css("div.company-title-views > h1::text")
                .get()
                .strip()
            )
        ),
        "Company_URL": url,
        "Page views": selector_handler(
            response,
            lambda response: int(
                response
                .css("p.company-page-views > span::text")
                .get()
            )
        ),
        "Followers": selector_handler(
            response,
            lambda response: int(
                response
                .css("p.company-page-views > span#followers_count::text")
                .get()
            )
        ),
        "Active_jobs": selector_handler(
            response,
            lambda response: int(
                response
                .css("p.company-active-job > a > span::text")
                .get()
            )
        ),
        "Job_history": selector_handler(
            response,
            lambda response: int(
                response
                .css("p.company-job-history > span::text")
                .get()
            )
        ),
        "Info": selector_handler(
            response,
            lambda response: "".join(
                response
                .css("div.hs_text_block ::text")
                .getall()
            )
        ),
        "Industry": selector_handler(
            response,
            lambda response: (
                response
                .css("td:contains('Industry:')~td ::text")
                .get()
            )
        ),
        "Type": selector_handler(
            response,
            lambda response: (
                response
                .css("td:contains('Type:')~td ::text")
                .get()
            )
        ),
        "Date_of_Foundation": selector_handler(
            response,
            lambda response: (
                response
                .css("td:contains('Date of Foundation:')~td ::text")
                .get()
            )
        ),
        "Number_of_Employees": selector_handler(
            response,
            lambda response: (
                response
                .css("span:contains('Number of Employees:')~span ::text")
                .get()
            )
        ),
        "Location": selector_handler(
            response,
            lambda response: (
                response
                .css("span:contains('Location:')~span ::text")
                .get()
            )
        ),
        "Website": selector_handler(
            response,
            lambda response: (
                response
                .css("a.hs_company_website_btn::attr(href)")
                .get()
            )
        ),
        "Benefits": selector_handler(
            response,
            lambda response: ( # List[str]
                response
                .css("div.hs_benefit_view_block > div > div > span ::text")
                .getall()
            )
        ),
        "Social": selector_handler(
            response,
            lambda response: ( # List[str]
                response
                .css("div.mt15 > a::attr(href)")
                .getall()
            )
        ),
        "Contacts": selector_handler(
            response,
            lambda response: ( # List[str]
                response
                .css("span.hs_info_circle_icon~span::text")
                .getall()
            )
        ),
        "Geolocation": get_geolocation(response)
    }

def get_geolocation(rs):
    try:
        location = list(map( # List[float]
            float,
            re.search(
                "q=(([0-9]+\.[0-9]+,?){2})&",
                rs.css("iframe::attr(src)").getall()[-1]
            ).group(1).split(",")
        ))
    except AttributeError:
        return None
    return location

# Function to collect data about companies
def crawl_all_companies(
    relative_paths_companies: Union[List[str], Set[str]]
) -> ExtractedData:
    extracted_data = defaultdict(list)
    with tqdm(relative_paths_companies) as pbar:
        for url in pbar:
            company_data = crawl_company_info(url)
            for key, value in company_data.items():
                extracted_data[key].append(value)
        pbar.set_description(f"URL {url}")
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
            with open(
                "../data/postings/staff_" + date + ".json",
                mode="w",
                encoding="utf-8"
            ) as f:
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
        response, BASE_URL, delay=0.5
    )
    absolute_paths = [urljoin(BASE_URL, path) for path in relative_paths]

    print(str(len(absolute_paths)) + " jobs detected.")
    print("Starting crawling job postings..")

    # NOTE: Added index slice for testing purposes, remove for production
    extracted_data = crawl_all_postings(absolute_paths[:], delay=1)

    print(
        str(len(extracted_data["URL"])) + "/" +
        str(len(absolute_paths)) + " jobs scraped."
    )
    print("Saving files.")

    for key in extracted_data.keys():
    	print(key + ": " + str(len(extracted_data[key])))

    save_files(extracted_data, "json")

    company_urls = extracted_data["Company_URL"]
    try:
        with open(
            "../data/companies/companies.json",
            mode="r",
            encoding="utf-8"
        ) as f:
            companies = json.load(f)
            available_companies = companies["Company_URL"]
    except:
        companies = defaultdict(list)
        available_companies = set()

    new_companies = set(company_urls) - set(available_companies)

    print(f"Detected {len(new_companies)} new companies.")
    if len(new_companies) > 0:
        print("Starting crawling companies.")

        extracted_companies = crawl_all_companies(new_companies)

        print(
            f"Extracted {len(extracted_companies['Company_URL'])}/{len(new_companies)}"
        )

        for k in extracted_companies.keys():
            companies[k].extend(extracted_companies[k])

        with open(
            "../data/companies/companies.json",
            mode="w",
            encoding="utf-8"
        ) as f:
            json.dump(companies, f, indent=4, ensure_ascii=False)

    end_time = time.ctime()
    print(end_time)
    print(f"Ended crawling '{BASE_URL}'.")

    return extracted_data


if __name__ == '__main__':
	extracted_data = main()
