# shebang to be added
# Crawler to scrape job postings and company information from https://staff.am/en/jobs

import re, json, time
import requests
import scrapy
from scrapy.http import HttpResponse
import pandas as pd

# URL variables
base_url = "https://staff.am"
main_url = base_url + "/en/jobs"

# Function to relative paths to job postings from a given page response
def get_relative_paths_from_one_page(page_response):
    
    relative_paths = page_response.css("div.web_item_card.hs_job_list_item a.load-more::attr(href)").getall()
    
    return relative_paths

# Function to get relative paths for all pages
def get_relative_paths_for_all_pages(first_page_response, base_url, delay=3):
    
    response = first_page_response
    relative_paths_for_all_pages = []
    
    while response.css("li.next a").get() is not None:
        
        relative_paths_for_all_pages.extend(get_relative_paths_from_one_page(response))
        rs = requests.get(base_url + response.css("li.next a::attr(href)").get())
        response = scrapy.http.HtmlResponse(url=rs.url, body=rs.text, encoding="utf-8")
        time.sleep(delay)
    
    # Adding relative paths of last page
    relative_paths_for_all_pages.extend(get_relative_paths_from_one_page(response))
        
    return relative_paths_for_all_pages

# Function to collect data from one job posting
def get_info_from_one_posting(absolute_path):
    
    rs = requests.get(absolute_path)
    response = scrapy.http.HtmlResponse(url=rs.url, body=rs.text, encoding="utf-8")
    
    extracted_data = {
        "Company_Title": response.css("h1.job_company_title::text").get(),
        "Total_views": response.css("div.col-lg-7.company_info_container p.company-page-views span::text").getall()[0],
        "Followers": response.css("div.col-lg-7.company_info_container p.company-page-views span::text").getall()[1],
        "Active_Jobs": response.css("p.company-active-job span::text").get(),
        "Jobs_History": response.css("p.company-job-history span::text").get(),
        "Job_Views": re.search("[0-9]+", response.css("div.statistics p::text").get()).group(),
        "Job_Title": response.css("div.col-lg-8 h2::text").get(),
        "Application_Deadline": re.search(r"Deadline: (.*)\s", response.css("div.col-lg-4.apply-btn-top p::text").get().replace("\n", " ")).group(1)
    }
    
    try:
        extracted_data["Industry"] = response.css("div.col-lg-7.company_info_container p.professional-skills-description span::text").getall()[-1]
    except IndexError:
        extracted_data["Industry"] = "None"

    job_info = [i.strip() for i in response.css("div.col-lg-6.job-info p::text").getall() if i != "\n"]
    
    extracted_data["Employment_term"] = job_info[0]
    extracted_data["Job_Category"] = job_info[1]
    extracted_data["Job_type"] = job_info[2]
    extracted_data["Job_Location"] = job_info[3]

    job_list = response.css("div.job-list-content-desc.hs_line_break")
    job_list_keys = [i.strip().replace(":", "").replace(" ", "_") for i in job_list.css("h3::text").getall()]

    if "Salary" not in job_list_keys:
        extracted_data["Salary"] = "None"
    elif "Required_candidate_level" not in job_list_keys:
        extracted_data["Required_candidate_level"] = "None"
    elif "Additional_information" not in job_list_keys:
        extracted_data["Additional_information"] = "None"

    for key in job_list_keys:
        if key == "Job_description":
            extracted_data[key] = job_list.css("p span::text, p::text").get()
        elif key == "Job_responsibilities":
            # ISSUE: If <ul> s for the field are more than 1 potential wrong collection of data
            try:
                extracted_data[key] = "\n".join(job_list.css("ul")[0].css("li span::text, li::text").getall())
            except IndexError:
                # ISSUE: If sibling <p> s are more than 1 not collected
                extracted_data[key] = "\n".join(job_list.css("h3:contains(responsibilities) + p + p::text").getall())
        elif key == "Required_qualifications":
            try:
                extracted_data[key] = "\n".join(job_list.css("ul")[1].css("li span::text, li::text").getall())
            except IndexError:
                # ISSUE: If sibling <p> s are more than 1 not collected
                extracted_data[key] = "\n".join(job_list.css("h3:contains(qualifications) + p + p::text").getall())
        elif key == "Required_candidate_level":
            extracted_data[key] = job_list.css("h3 span::text, h3::text").getall()[0]
        elif key == "Salary":
            extracted_data[key] = job_list.css("h3 span::text, h3::text").getall()[1]
        elif key == "Additional_information":
            extracted_data[key] = "\n".join(job_list.css("div.additional-information p span::text, div.additional-information p::text").getall())
        else:
            extracted_data[key] = "New Field to be scraped"
            print("New Field to be scraped")
            
    skills_info_keys = [i.replace(" ", "_") for i in response.css("div.soft-skills-list.clearfix h3::text").getall()]
    
    if "Professional_skills" in skills_info_keys:
        ind = skills_info_keys.index("Professional_skills")
        extracted_data["Professional_skills"] = "\n".join(response.css("div.soft-skills-list.clearfix")[ind].css("p span::text, p::text").getall())
    else:
        extracted_data["Professional_skills"] = "None"
    if "Soft_skills" in skills_info_keys:
        ind = skills_info_keys.index("Soft_skills")
        extracted_data["Soft_skills"] = "\n".join(response.css("div.soft-skills-list.clearfix")[ind].css("p span::text, p::text").getall())
    else:
        extracted_data["Soft_skills"] = "None"

    return extracted_data

# Function to collect data from all job postings given absolute paths
def crawl_all_postings(absolute_paths, delay=10):
    
    extracted_data = {}
    
    i = 1
    
    for path in absolute_paths:
        print(path)
        print(str(i) + "/" + str(len(absolute_paths)), "Est.: " + str(round((10 * (len(absolute_paths) - i))/60, 2)) + "m.")
        i += 1
        extracted_data_from_posting = get_info_from_one_posting(path)
        
        for key, value in extracted_data_from_posting.items():
            
            if key not in extracted_data.keys():
                
                extracted_data[key] = []
                
            extracted_data[key].append(extracted_data_from_posting[key])
        
        time.sleep(delay)
    
    return extracted_data

# Function to collect data about companies
def crawl_all_companies(absolute_paths_companies):
    
    # TODO

    return ""

# Main function
def main():
    
    rs = requests.get(main_url)
    response = scrapy.http.HtmlResponse(url=rs.url, body=rs.text, encoding="utf-8")

    relative_paths_for_all_pages = get_relative_paths_for_all_pages(response, base_url, delay=5)
    absolute_paths = [base_url + path for path in relative_paths_for_all_pages]
    
    extracted_data = crawl_all_postings(absolute_paths)
    
    return extracted_data

if __name__ == '__main__':
	extracted_data = main()
	
