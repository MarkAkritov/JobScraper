# List of features to add (TODO)

---

## Development Tools

* [x] Setup environment using **`Pipenv`** (*Python 3.9*)

* [x] Add **`.env`** & **`.env.template`** for environment variables

* [ ] Make **CLI** using **`click`** or **`Typer`**

* [ ] Add **`mypy`** tests

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

* [x] Correct the encoding for *arm* characters

* [ ] Add functionality for scraping **company** information

* [ ] Implement saving to `.csv` functionality

* [ ] Save logs for a daily crawling (appending msg.-s in `main` function)

* [ ] Utilize `urllib.parse.urljoin` for base URL and relative pages' joining

* [ ] Add URL to extracted data fields

## Database

* [ ] Setup RDBMS (**`PostgreSQL`**/**`SQLite`**)

* [ ] Setup ORM (Object Relational Mapper: **`SQLAlchemy.orm`**/**`PeeWee`**)

---
