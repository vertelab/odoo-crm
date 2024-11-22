import logging
import requests
import re
from typing import Dict

from bs4 import BeautifulSoup

_logger = logging.getLogger(__name__)


def extract_arbetsstallen(soup) -> Dict[str, str]:
    # Find the main workplace table
    workplace_table = soup.find("div", {"id": "workplace-table"})

    # Initialize a dictionary to store key-value pairs
    workplace_details = {}

    if workplace_table:
        rows = workplace_table.find_all("tr")[1:]  # Exclude the first <tr>

        for row in rows:
            cols = row.find_all("td")
            if len(cols) == 1:  # Found a new workplace section
                # If this is not the first workplace, break
                if workplace_details:
                    break
            elif len(cols) == 2:  # Add key-value pairs for the first workplace
                # Strip trailing ":" from keys and normalize whitespace
                key = cols[0].get_text(strip=True).rstrip(":")
                value = cols[1].get_text(strip=True)
                workplace_details[key] = value

    return workplace_details


def extract_financial_statements(soup: BeautifulSoup) -> Dict[str, float]:
    metrics = {
        'omsattning': 0.0,
        'arets_resultat': 0.0,
        'ebitda': 0.0,
        'utdelning': 0.0
    }

    def safe_float_conversion(value: str) -> float:
        """Convert a string with KSEK to a float, handling negative values."""
        try:
            # Replace the Unicode minus sign (−) with the regular minus sign (-)
            value = value.replace('&#x2212;', '-')  # Ensure the minus sign is correctly handled
            value = value.replace('−', '-')  # Also handle direct Unicode minus sign

            clean_value = re.sub(r'[^\d.-]', '', value)  # Remove non-numeric characters except - and .

            # If 'KSEK' is found in value, convert to SEK by multiplying by 1000
            if 'KSEK' in value:
                return float(clean_value) * 1000
            else:
                return float(clean_value)
        except ValueError:
            return 0.0

    try:
        container = soup.find('div', id='oversikt-senaste-bokslut')
        if not container:
            return metrics

        # Extract Vue-bound attributes (e.g., :text="'203&#xA0;360 KSEK'")
        items = container.find_all('v-value-color-text')
        for item in items:
            text_attr = item.get(':text')
            if text_attr:
                # Ensure the negative symbol (if exists) is correctly decoded
                text_value = BeautifulSoup(text_attr, 'html.parser').text
                text_value = text_value.replace('&#x2212;', '-')  # Make sure negative sign is handled properly
                text_value = text_value.replace('−', '-')  # Handle the Unicode minus

                tooltip = item.find('span', class_='tooltip__text')
                if tooltip:
                    key = tooltip.text.strip().lower()
                    if 'omsättning' in key:
                        metrics['omsattning'] = safe_float_conversion(text_value)
                    elif 'årets resultat' in key:
                        metrics['arets_resultat'] = safe_float_conversion(text_value)
                    elif 'ebitda' in key:
                        metrics['ebitda'] = safe_float_conversion(text_value)
                    elif 'utdelning' in key:
                        metrics['utdelning'] = safe_float_conversion(text_value)

    except Exception as e:
        print(f"Error parsing financial statements: {e}")

    return metrics


def extract_companies(soup, municipality, crm_data, filter_params):
    # Find all company content-boxes on the current page
    company_boxes = soup.find_all("div", class_="content-box content-box--no-hover mt-2")
    companies_data = []

    for box in company_boxes:
        # Extract the link from the <a> tag
        a_tag = box.find("a")
        link = a_tag['href'] if a_tag else None

        # Extract content inside the inner content box
        inner_box = box.find("div", class_="content-box-inner content-box--no-hover")
        if inner_box:
            # Extract the name and address from the left column
            left_column = inner_box.find("div", class_="col-sm-6")
            name = left_column.find("h2", class_="mt-0 site-h3").get_text(strip=True) if left_column else None

            # Safely extract address, checking if it's None
            address = None
            if left_column:
                address_element = left_column.find("div", class_="mt-1 bolagsfakta-color--charcole-black")
                address = address_element.get_text(strip=True) if address_element else None

            # Initialize right_column as None
            right_column = None
            # Check for org number in both left and right columns
            org_number = None
            org_number_element = left_column.find(
                "span", class_="mt-1 bolagsfakta-color--charcole-black"
            ) if left_column else None
            if not org_number_element:
                right_column = inner_box.find("div", class_="col-sm-6 text-sm-right")
                org_number_element = right_column.find(
                    "span", class_="mt-1 bolagsfakta-color--charcole-black"
                ) if right_column else None

            if org_number_element:
                org_number = org_number_element.get_text(strip=True) if org_number_element else None

            # Extract corporate form from the right column
            corporate_form = None
            if right_column:
                corporate_form_elements = right_column.find_all("span")
                if corporate_form_elements:
                    corporate_form = corporate_form_elements[-1].get_text(strip=True)

            is_valid, company_extra_data = filter_companies(bolagsfakta_company_link=link, filter_params=filter_params)

            if is_valid:
                # Create a dictionary for each company
                company_record = {
                    "name": name,
                    "partner_name": name,
                    "street": address,
                    "org_number": org_number,
                    "corporate_form": corporate_form,
                    "bolagsfakta_company_link": link,
                    "municipality": municipality.id,
                    **crm_data,
                    **company_extra_data
                }
                companies_data.append(company_record)

    # Check for pagination
    pagination = soup.find("div", class_="pagination-standard")
    if pagination:
        next_page_link = get_next_page_link(pagination)
        if next_page_link:
            next_page_response = requests.get(next_page_link)
            next_page_soup = BeautifulSoup(next_page_response.content, 'html.parser')
            companies_data.extend(extract_companies(
                soup=next_page_soup, municipality=municipality, crm_data=crm_data, filter_params=filter_params
            ))

    return companies_data


def get_next_page_link(pagination):
    """Extracts the link to the next page from the pagination."""
    next_page_link = None
    next_page = pagination.find("li", class_="pagination-standard-list__item--active").find_next_sibling("li")
    if next_page:
        next_page_link = next_page.find("a")['href'] if next_page.find("a") else None
    return next_page_link


def extra_data(soup):
    finance = extract_financial_statements(soup)
    arbetsstallen = extract_arbetsstallen(soup)

    return {
        **finance,
        'employee_range': arbetsstallen.get('Antal anställda', "0 anställda")
    }


def filter_companies(bolagsfakta_company_link, filter_params):
    response = requests.get(bolagsfakta_company_link)
    soup = BeautifulSoup(response.content, 'html.parser')

    company_extra_data = extra_data(soup)

    turn_over = company_extra_data.get('omsattning') >= filter_params.get('turn_over')
    # if arbetsstallen:
    employee_range = is_employee_count_in_range(
        filter_params.get('number_of_employees'), company_extra_data.get('employee_range')
    )

    return turn_over and employee_range, company_extra_data


def is_employee_count_in_range(employee_count: int, employee_range: str) -> bool:
    """
    Checks if the given employee_count falls within the employee_range.

    Args:
        employee_count (int): The number of employees to check.
        employee_range (str): The range of employees as a string (e.g., "0 anställda", "1-5 anställda").

    Returns:
        bool: True if employee_count falls within the range, False otherwise.
    """
    # Remove the "anställda" suffix and extra spaces
    range_cleaned = employee_range.replace("anställda", "").strip()

    try:
        # Parse the range
        if "-" in range_cleaned:
            min_count, max_count = map(int, range_cleaned.split("-"))
            return min_count <= employee_count <= max_count
        elif range_cleaned.isdigit():
            exact_count = int(range_cleaned)
            return exact_count == employee_count
        elif range_cleaned == "0":  # Handle exact case for 0 employees
            return employee_count == 0
    except ValueError:
        # If parsing fails, log or handle the error appropriately
        pass

    # If the range is not clear or parsing fails, return False
    return False


# old way to get financial statement
# def financial_statements(self, soup) -> Dict[str, float]:
#     metrics = {
#         'omsattning': None,
#         'arets_resultat': None,
#         'ebitda': None,
#         'utdelning': None
#     }
#
#     def safe_float_conversion(value):
#         """Safely convert string to float, handling any errors"""
#         if value is None:
#             return None
#         try:
#             # Remove commas and convert to float
#             return float(str(value).replace(',', ''))
#         except (ValueError, TypeError, AttributeError):
#             _logger.error(f"Could not convert value to float: {value}")
#             return None
#
#     try:
#         # 1. Find EBITDA
#         for row in soup.find_all('tr', class_='d-none d-lg-table-row'):
#             tooltip = row.find('span', class_='tooltip__text')
#             if tooltip and 'EBITDA' in tooltip.text:
#                 value_text = row.find_all('td')[1].get_text(strip=True)
#                 metrics['ebitda'] = safe_float_conversion(value_text)
#
#         # 2. Find Rörelsens omsättning
#         omsattning_row = soup.find('u', text='Rörelsens omsättning')
#         if omsattning_row:
#             row = omsattning_row.find_parent('tr')
#             value_text = row.find_all('td')[1].get_text(strip=True)
#             metrics['omsattning'] = safe_float_conversion(value_text)
#
#         # 3. Find Årets resultat
#         resultat_rows = soup.find_all('tr', class_='d-none d-lg-table-row table--bgcolor')
#         for row in resultat_rows:
#             tooltip = row.find('span', class_='tooltip__text')
#             if tooltip and tooltip.text.strip() == 'Årets resultat':
#                 value_text = row.find_all('td')[1].get_text(strip=True)
#                 metrics['arets_resultat'] = safe_float_conversion(value_text)
#                 break
#
#     except Exception as e:
#         _logger.error(f"Error parsing financial statements: {e}")
#
#     # Final check to ensure all non-None values are floats
#     for key in metrics:
#         if metrics[key] is not None:
#             metrics[key] = safe_float_conversion(metrics[key])
#
#     return metrics