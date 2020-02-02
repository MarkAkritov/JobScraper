# shebang to be added
# Crawler to scrape job postings and company information from https://staff.am/en/jobs

import re, json, time, datetime
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

    all_default_keys = (
        "Company_Title", "Total_views", "Followers", "Active_Jobs",
        "Jobs_History", "Job_Views", "Job_Title", "Application_Deadline",
        "Industry", "Employment_term", "Job_Category", "Job_type",
        "Job_Location", "Job_description", "Job_responsibilities", "Required_qualifications", 
        "Required_candidate_level", "Salary", "Additional_information", "Professional_skills",
        "Soft_skills"
    )
    
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
    
    default_job_list_keys = [
        "Job_description", "Job_responsibilities", "Required_qualifications", 
        "Required_candidate_level", "Salary", "Additional_information"
    ]
    job_list = response.css("div.job-list-content-desc.hs_line_break")
    job_list_keys = [i.strip().replace(":", "").replace(" ", "_") for i in job_list.css("h3::text").getall()]
    
    if len(default_job_list_keys) < len(job_list_keys):
        print("New 'h3' fields in job description list are present: \nCheck the output.")
    else:
        for key in default_job_list_keys:
            if key not in job_list_keys:
                extracted_data[key] = "None"
                
    for cnt, h3 in enumerate(job_list.css('h3'), start=1):
        
        key = h3.css("::text").get().strip().replace(":", "").replace(" ", "_")
        
        if key in ["Required_candidate_level", "Salary"]:
            extracted_data[key] = h3.css("span::text").get()
        else:
            values = h3.xpath("following-sibling::*[count(preceding-sibling::h3)=$cnt]", cnt=cnt)[:-1].css("::text").getall()
            extracted_data[key] = [value.strip() for value in values if value != "\n"]
            
    skills_info_keys = [i.replace(" ", "_") for i in response.css("div.soft-skills-list.clearfix h3::text").getall()]
    
    if "Professional_skills" in skills_info_keys:
        ind = skills_info_keys.index("Professional_skills")
        extracted_data["Professional_skills"] = response.css("div.soft-skills-list.clearfix")[ind].css("p span::text, .p::text").getall()
    else:
        extracted_data["Professional_skills"] = "None"
    if "Soft_skills" in skills_info_keys:
        ind = skills_info_keys.index("Soft_skills")
        extracted_data["Soft_skills"] = response.css("div.soft-skills-list.clearfix")[ind].css("p span::text, .p::text").getall()
    else:
        extracted_data["Soft_skills"] = "None"

    for key in all_default_keys:
        if key not in extracted_data.keys():
            print("Default field: '{}' is missing in extracted data.".format(key))
            extracted_data[key] = "None"

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

# Function to make dict data to be saved as csv
def format_to_csv(file):
    
    keys_to_format = (
        "Job_description", "Job_responsibilities", "Required_qualifications", 
        "Additional_information", "Professional_skills", "Soft_skills"
    )
    
    for key, value in file.items():
        if key in keys_to_format:
            file[key] = "\n".join(file[key])
            
    return file

# Function to save the data in a given file format
def save_files(file, *formats):
    
    date = datetime.date.today().strftime("%d.%m.%y")
    
    for ext in formats:
        
        if ext not in ("csv", "json"):
            print("Can't save in {} format.\nSaving both to 'csv' and 'json'.".format(ext))
            save_files(file, "csv", "json")
            break
        elif ext == "csv":
            file_csv = format_to_csv(file)
            try:
                file_csv = pd.DataFrame(file_csv)
                file_csv.to_csv("staff_" + date + ".csv")
            except ValueError:
                print("Unable to save 'csv': missing values are present.\nSaving to 'json'")
                save_files(file, "json")
                break
        elif ext == "json":
            with open("staff_" + date + ".json", "w") as f:
                f.write(json.dumps(file))



# Main function
def main():
    
	start_time = time.ctime()
	print(start_time)
	print("Starting crawling '{}'.".format(base_url))

	rs = requests.get(main_url)
	response = scrapy.http.HtmlResponse(url=rs.url, body=rs.text, encoding="utf-8")

    relative_paths_for_all_pages = get_relative_paths_for_all_pages(response, base_url, delay=5)
    absolute_paths = [base_url + path for path in relative_paths_for_all_pages]

    print(str(len(absolute_paths)) + " jobs detected.")
    print("Starting crawling job postings..")
    
    extracted_data = crawl_all_postings(absolute_paths)

    end_time = time.ctime()
    print(end_time)
    print("Ended crawling '{}'.".format(base_url))

    print(str(len(extracted_data["Company_Title"])) + "/" + len(absolute_paths) + " jobs scraped.")
    print("Saving files.")

    for key in data.keys():
    	print(key + ": " + str(len(data[key])))

    save_files(extracted_data, "csv", "json")
    
    return extracted_data

if __name__ == '__main__':
	extracted_data = main()
