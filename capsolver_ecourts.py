#!/usr/bin/env python3
"""e-Courts case scraper with CapSolver."""

import asyncio
import base64
import os
import sys
import time

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from playwright.async_api import async_playwright

from logger import logger

load_dotenv()

CAPSOLVER_API_KEY = os.getenv("CAPSOLVER_API_KEY")


def solve_captcha_with_capsolver(image_base64):
    task_payload = {
        "clientKey": CAPSOLVER_API_KEY,
        "task": {
            "type": "ImageToTextTask",
            "body": image_base64,
        },
    }

    try:
        response = requests.post("https://api.capsolver.com/createTask", json=task_payload, timeout=30)
        result = response.json()

        if result.get("errorId") == 0:
            if result.get("status") == "ready" and result.get("solution"):
                return result["solution"]["text"]

            task_id = result.get("taskId")
            time.sleep(2)

            for _ in range(30):
                poll_response = requests.post(
                    "https://api.capsolver.com/getTaskResult",
                    json={"clientKey": CAPSOLVER_API_KEY, "taskId": task_id},
                    timeout=30,
                )
                poll_data = poll_response.json()

                if poll_data.get("status") == "ready":
                    return poll_data["solution"]["text"]
                time.sleep(1)

        logger.warning("CapSolver task did not return a solution")
        return None

    except Exception:
        logger.exception("CapSolver API request failed")
        return None


def new_parse(html_content):
    soup = BeautifulSoup(html_content, "html.parser")

    case_data = {}

    fields = {
        "Case Type": "case_type",
        "Filing Number": "filing_number",
        "Filing Date": "filing_date",
        "Registration Number": "registration_number",
        "Registration Date": "registration_date",
    }
    details_table = soup.find("table", class_="case_details_table")
    if details_table:
        for label, key in fields.items():
            th = details_table.find("th", string=lambda s, l=label: s and l in s)
            case_data[key] = th.find_next("td").text.strip() if th else None

    status_fields = {
        "Next Hearing Date": "next_hearing_date",
        "Case Stage": "case_stage",
        "Sub Stage": "sub_stage",
        "Court Number and Judge": "court_name",
    }
    status_table = soup.find("table", class_="case_status_table")
    if status_table:
        for label, key in status_fields.items():
            th = status_table.find("th", string=lambda s, l=label: s and l in s)
            case_data[key] = th.find_next("td").text.strip() if th else None

    history_table = soup.find("table", class_="history_table")
    if history_table:
        case_data["case_history"] = []
        tbody = history_table.find("tbody")
        if tbody:
            history_rows = tbody.find_all("tr")
            for row in history_rows:
                cells = row.find_all("td")
                if len(cells) >= 4:
                    history_entry = {
                        "judge": cells[0].text.strip(),
                        "business_date": cells[1].text.strip(),
                        "hearing_date": cells[2].text.strip(),
                        "purpose": cells[3].text.strip(),
                    }
                    case_data["case_history"].append(history_entry)

    return case_data


async def scrape_ecourts(cnr_number):
    if not CAPSOLVER_API_KEY:
        logger.error("scrape_ecourts: missing CAPSOLVER_API_KEY")
        return None

    logger.info("scrape_ecourts start cnr=%s", cnr_number)
    playwright = await async_playwright().start()
    browser = None

    try:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})

        await page.goto("https://services.ecourts.gov.in/ecourtindia_v6/", wait_until="networkidle")
        await page.wait_for_timeout(2000)

        cnr_input = await page.query_selector("#cino")
        if not cnr_input:
            logger.error("scrape_ecourts: CNR input #cino not found cnr=%s", cnr_number)
            return None
        await cnr_input.fill(cnr_number)
        await page.wait_for_timeout(1000)

        error_div = await page.query_selector(".alert-danger")
        if error_div:
            is_visible = await error_div.is_visible()
            if is_visible:
                error_text = await page.inner_text("#msg-danger")
                logger.warning("scrape_ecourts: page error after CNR fill cnr=%s msg=%s", cnr_number, error_text)
                return None

        max_retries = 3
        captcha_success = False

        for attempt in range(max_retries):
            logger.info("scrape_ecourts cnr=%s captcha attempt %s/%s", cnr_number, attempt + 1, max_retries)

            captcha_img = await page.query_selector('img[src*="securimage"]')
            if not captcha_img:
                logger.error("scrape_ecourts: CAPTCHA image not found cnr=%s", cnr_number)
                return None

            captcha_screenshot = await captcha_img.screenshot()
            captcha_base64 = base64.b64encode(captcha_screenshot).decode("utf-8")

            captcha_solution = solve_captcha_with_capsolver(captcha_base64)
            if not captcha_solution:
                logger.warning("scrape_ecourts: CapSolver returned no text cnr=%s attempt=%s", cnr_number, attempt + 1)
                continue

            logger.info("scrape_ecourts: CAPTCHA solved cnr=%s attempt=%s", cnr_number, attempt + 1)

            captcha_input = await page.query_selector("#fcaptcha_code")
            if not captcha_input:
                logger.error("scrape_ecourts: #fcaptcha_code not found cnr=%s", cnr_number)
                return None

            submit_button = await page.query_selector("#searchbtn")
            if not submit_button:
                logger.error("scrape_ecourts: #searchbtn not found cnr=%s", cnr_number)
                return None

            await captcha_input.fill(captcha_solution)
            await page.wait_for_timeout(500)
            await submit_button.click()
            await page.wait_for_timeout(2000)

            error_div = await page.query_selector(".alert-danger")
            if error_div and await error_div.is_visible():
                error_text = await page.inner_text("#msg-danger")
                logger.warning("scrape_ecourts: post-submit error cnr=%s attempt=%s msg=%s", cnr_number, attempt + 1, error_text)

                if "captcha" in error_text.lower() or "verification" in error_text.lower():
                    if attempt < max_retries - 1:
                        logger.info("scrape_ecourts: retrying after CAPTCHA error cnr=%s", cnr_number)
                        await page.reload()
                        await page.wait_for_timeout(2000)
                        cnr_input = await page.query_selector("#cino")
                        await cnr_input.fill(cnr_number)
                        await page.wait_for_timeout(1000)
                        continue
                return None

            try:
                await page.wait_for_selector("#history_cnr", timeout=10000)
                captcha_success = True
                break
            except Exception:
                logger.warning("scrape_ecourts: #history_cnr not seen cnr=%s attempt=%s", cnr_number, attempt + 1)
                if attempt < max_retries - 1:
                    await page.reload()
                    await page.wait_for_timeout(2000)
                    cnr_input = await page.query_selector("#cino")
                    await cnr_input.fill(cnr_number)
                    await page.wait_for_timeout(1000)

        if not captcha_success:
            logger.error("scrape_ecourts: exhausted retries cnr=%s", cnr_number)
            return None

        history_html = await page.inner_html("#history_cnr")
        parsed = new_parse(history_html)
        logger.info("scrape_ecourts ok cnr=%s history_entries=%s", cnr_number, len(parsed.get("case_history") or []))
        return parsed

    except Exception:
        logger.exception("scrape_ecourts failed cnr=%s", cnr_number)
        return None
    finally:
        if browser is not None:
            await browser.close()
        await playwright.stop()


async def main():
    cnr_number = sys.argv[1]

    logger.info("CLI scrape cnr=%s", cnr_number)
    result = await scrape_ecourts(cnr_number)

    if result:
        logger.info("CLI scrape success cnr=%s keys=%s", cnr_number, list(result.keys()))
    else:
        logger.error("CLI scrape failed cnr=%s", cnr_number)


if __name__ == "__main__":
    asyncio.run(main())
