# List of features to add (TODO)

---

## Development Tools

* [x] Setup environment using **`Pipenv`** (*Python 3.9*)

* [x] Add **`.env`** & **`.env.template`** for environment variables

* [ ] Make **CLI** using **`click`** or **`Typer`**

* [ ] Add **`mypy`** tests

* [ ] Fully utilize `scrapy` **Spyders** (*currently works with* `requests`)

* [ ] Setup **`cron`** jobs for automatic daily scraping

## Architecture and code optimization

* [x] Add **type hints**

* [x] Stylize code to be max 80 char.-s per row

* [x] Convert all `str.format()` syntax to f-strings(`f"{}"`)

* [ ] Setup proper architecture for:
***Scraper*** - ***DB*** - ***DAE*** - ***API*** - ***Dashboard***

* [ ] Add **docstrings**

## Functionalities & changes

* [x] When svaing to `.json`, stylize/prettify the content

* [x] Correct the encoding for *arm* characters (*UTF-8*)

* [x] Add URL to extracted data fields

* [x] Add Company URL to extracted data fields

* [x] Add **`Foundation_date`** and **`Telephone`** fields to companies

* [x] Scrape all companies so that new companies can be detected properly

* [x] Add functionality for scraping **company** information

* [x] Change data storing directory (currently in `notebooks/`)

* [x] Add progress bars

* [x] Utilize **`collections.defaultdict`**

* [x] Utilize `urllib.parse.urljoin` for base URL and relative pages' joining

* [ ] Need to update `Job_views` field daily

* [ ] Implement saving to `.csv` functionality

* [ ] Save logs for a daily crawling (appending msg.-s in `main` function)

* [ ] Need to check previous scraped data for avoiding duplicate crawling

* [ ] Add summarizing daily logs with following fields:

    ```json
    {
        "date": {
            "date": "datetime",
            "weekday": "str",
            "postings": "int",
            "new_postings": "int",
            "new_companies": "int"
        }
    }
    ```

* [x] Change behaviour of crawler to store `new h3 field` message's info in
  `Additional_Info` field, instead of printing in the console

* [x] Change `tqdm` message so that it prints the URL being scraped

* [ ] Email notification if scraping fails for some reason

## Bugs

* [x] Fix company title fetching (currently `None`)

* [x] Store `int`-s & `float`-s properly in `.json` files (stored as `str`)

* [x] Recover URL-s for previous scraped data

* [x] Fix company storing data (`list.extend()` instead of `list.append()`)

* [x] Finalize Company info crawling in `main()` function

* [x] Fix bug related to `crawl_all_companies()` output (`list` instead of `dict`)

* [x] Fix Company `Info` field scraping (appends all companies together)

* [x] Strip scraped `str` data (eg.: `Company_Title`)

* [x] Fix scraping of `Additional_information` field

## Database

* [ ] Setup RDBMS or NoSQL (**`PostgreSQL`**/**`SQLite`** or **`MongoDB`**/**`Redis`**)

* [ ] Setup ORM (Object Relational Mapper: **`SQLAlchemy.orm`**/**`PeeWee`**)

---
