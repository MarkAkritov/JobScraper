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

## Functionalities

* [x] When svaing to `.json`, stylize/prettify the content

* [x] Correct the encoding for *arm* characters (*UTF-8*)

* [x] Add URL to extracted data fields

* [x] Add Company URL to extracted data fields

* [ ] Save logs for a daily crawling (appending msg.-s in `main` function)

* [ ] Utilize `urllib.parse.urljoin` for base URL and relative pages' joining

* [ ] Add functionality for scraping **company** information

* [ ] Implement saving to `.csv` functionality

* [ ] Add progress bars

* [ ] Change data storing directory (currently in `notebooks/`)

* [ ] Need to check previous scraped data for avoiding duplicate crawling

* [ ] Need to update `Job_views` field daily

## Bugs

* [x] Fix company title fetching (currently `None`)

* [x] Store `int`-s & `float`-s properly in `.json` files (stored as `str`)

* [x] Recover URL-s for previous scraped data

## Database

* [ ] Setup RDBMS or NoSQL (**`PostgreSQL`**/**`SQLite`** or **`MongoDB`**/**`Redis`**)

* [ ] Setup ORM (Object Relational Mapper: **`SQLAlchemy.orm`**/**`PeeWee`**)

---
