from bs4 import BeautifulSoup
import requests
import pandas as pd
import ast
import json
import numpy as np
from pprint import pprint


def parse_field(row, data_stat, field_type='td', value_location='value', function=None, **kwargs):
	"""

	Args:
		data_stat: data_stat field for identifying data
		field_type: field type (a, th, td, div..)
		value_location: either 'value', 'csk', or some other field
		function: function to be applied after parsing
	"""
	cell = row.find_all(field_type, attrs={"data-stat": data_stat})[0]  # get the first instance
	if value_location == 'value':
		val = cell.text.strip()
	else:
		val = cell[value_location]

	return val


def parse_row(row, data_dicts=[]):
	d = {}
	for field_dict in data_dicts:
		d[field_dict['name']] = parse_field(row, **field_dict)

	return d


def get_table_rows(url, table_id, tbody=True, tr_class=None, data_dicts=None):
	page = requests.get(url)
	soup = BeautifulSoup(page.content, 'html.parser')
	table = soup.find(id=table_id)

	if tbody:
		table = table.find_all('tbody')[0]

	rows = table.find_all('tr', class_=tr_class)

	table_items = []
	if data_dicts is not None:
		for row in rows:
			d = parse_row(row, data_dicts)
			table_items.append(d)
		table = pd.DataFrame.from_records(table_items)

		table.replace('', None, inplace=True)
		dtypes = {v['name']: v['dtype'] for v in data_dicts if 'dtype' in v}

		for v in data_dicts:
			if 'function' in v and v['function'] is not None:
				table[v['name']] = table[v['name']].apply(v['function'])

		table = table.astype(dtypes)

	return table


def get_unique_headers(headers):
	headers_unique = []

	for i, h in enumerate(headers):
		h_orig = h
		k = 1
		while h in headers_unique:
			h = '{:}{:.0f}'.format(h_orig, k)
			k += 1
		headers_unique.append(h)
	return headers_unique


def get_table_simple(url, table_id, use_tbody=True):
	page = requests.get(url)
	soup = BeautifulSoup(page.content, 'html.parser')
	table = soup.find(id=table_id)
	headers = [th.text for th in table.select("tr th")]
	table = table.select_one("tbody")
	rows = table.select("tr")
	rows_parsed = [[td.text for td in row.find_all(["th", "td"])] for row in rows]

	if len(headers) > len(rows_parsed[0]):  # if more headers than data, assume we just need to trim
		headers = headers[:len(rows_parsed[0])]

	headers = get_unique_headers(headers)
	table = pd.DataFrame(rows_parsed, columns=headers)
	table.replace('', np.nan, inplace=True)
	return table
