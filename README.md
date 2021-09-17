# JobScraper

Monitoring of Armenian Labor Market via scraping job posting websites.

## Specifications & Requirements

* **Python** $\ge$ 3.7 (*3.9* *suggested*)

* **Pipenv** (*optional*)

* **Scrapy**

## Commands

* Setup the environment

    ```shell
    > git clone https://github.com/MarkAkritov/JobScraper.git
    > cd JobScraper
    > pip install pipenv # if not available
    > pipenv install
    > pipenv shell
    ```

    OR

    ```shell
    > git clone https://github.com/MarkAkritov/JobScraper.git
    > cd JobScraper
    > pip install -r requirements.txt
    ```

* Run crawling script

    ```shell
    > cd scrapers
    > python -m staff.py
    ```

Features and Fixes to be implemented:
> Provided in the following [**TODO** list](./TODO.md)
