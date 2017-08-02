import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET
import lxml
import cerberus
from collections import defaultdict

# set-up the file and tag I am going to use
osm_file = 'chicago_illinois.osm'
sample_file = 'sample_chicago.osm'
tag = ['node', 'way', 'relation']


# find the elements from the original .osm file
def get_element(osm_file, tags=('node', 'way', 'relation')):
    '''
    This function will read an XML file, get the element from desired tags.

    Parameters
    ----------
    osm_file: .xml or .osm file
        the XML or OSM file to be parsed

    tags: string or list
        the tag name that you want to get elements from.
        default is ['node', 'way', 'relation']

    Return
    ------
    .xml or .osm file
    '''

    context = iter(ET.iterparse(osm_file, events=('start', 'end')))
    _, root = next(context)

    for event, elem in context:
        if (event == 'end') and (elem.tag in tags):
            yield elem
            root.clear()


# write the generated elements into sample.osm file
k = 1000
with open(sample_file, 'wb') as output:
    output.write(bytes('<?xml version="1.0" encoding="UTF-8"?>\n', 'UTF-8'))
    output.write(bytes('<osm>\n  ', 'UTF-8'))

    for i, element in enumerate(get_element(osm_file)):
        if i % k == 0:
            output.write(ET.tostring(element, encoding='utf-8'))

    output.write(bytes('</osm>', 'UTF-8'))


# explore the data
def count_tag(filename):
    tags = {}
    for event, elem in ET.iterparse(filename):
        tag = elem.tag
        if tag not in tags:
            tags[tag] = 1
        else:
            tags[tag] += 1
    return tags


# check the error with k attribute
lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
keys = {"lower": 0, "lower_colon": 0, "problemchars": 0, "other": 0}


def key_type(filename, keys):
    '''
    This function will read through the k element and return its catogory

    Parameters
    ---
    filename: .xml or .osm file
        the file that is going to be analyzed
    keys: a dictionary
        a dictionary to show the catogory

    Return
    ---
    the updated keys(a dictionary)
    '''
    for event, element in ET.iterparse(filename):
        if element.tag == 'tag':
            key = element.get('k')
            if lower.search(key):
                keys['lower'] += 1
            elif re.findall(lower_colon, key):
                keys['lower_colon'] += 1
            elif re.findall(problemchars, key):
                keys['problemchars'] += 1
            else:
                keys['other'] += 1

    return keys


# check the error with street-type
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place",
            "Square", "Lane", "Road", "Trail", "Parkway", "Commons"]


def audit_street_type(street_types, street_name):
    '''
    This function find the street_name that doesn't match the expected list

    Parameters
    ---
    street_types: a dictionary
        it is a dictionary that contains the unique key of street types
    street_name: strings
        the street name found in .xml or .osm file

    Return
    ---
    None
    '''
    match = street_type_re.search(street_name)
    if match:
        street_type = match.group(0)
        if street_type not in expected:
            street_types[street_type].add(street_name)


def audit(filename):
    '''
    This function will read a file and print the street types

    Parameters
    ---
    filename: .xml or .osm file

    Return
    ---
    street_types dictionary
    '''
    street_types = defaultdict(set)

    for event, elem in ET.iterparse(filename, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if tag.attrib['k'] == 'addr:street':
                    audit_street_type(street_types, tag.attrib['v'])
    return street_types


# update the name based on mapping to the correct format
mapping = {"St": "Street",
           "St.": "Street",
           "Ave": 'Avenue',
           'Rd.': 'Road',
           'Dr': 'Drive',
           'E': 'East',
           'Highway': 'Highway'
           }


def update_name(name, mapping):
    '''
    This function will update the name based on the given mapping

    Parameters:
    ---
    name: the unexpected street name found in the file
    mapping: the mapping for updating the name

    Return:
    the updated name
    '''
    update_name = name.split(' ')[-1]
    if update_name in mapping:
        new_name = mapping[update_name]

        name = name.replace(update_name, new_name)

    return name


def update_file(filename):
    '''
    This function will bring audit() and update_name() functions together to
    update the street names to make them consistenct

    Parameters
    ---
    filename: the .xml or .osm file that needs to be updated

    Return
    ---
    the updated file
    '''
    street_types = audit(filename)
    for street_type, ways in street_types.items():
        for name in ways:
            name = update_name(name, mapping)

# write the sample file into a csv

# query this dataset through SQL query

# draw the conclusion
