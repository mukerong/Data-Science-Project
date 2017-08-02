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


def audit(filename):
    street_types = defaultdict(set)

    for event, elem in ET.iterparse(filename, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if tag.attrib['k'] == 'addr:street':
                    audit_street_type(street_types, tag.attrib['v'])
    return street_types


def audit_street_type(street_types, street_name):
    '''
    this function will return
    '''
    match = street_type_re.search(street_name)
    if match:
        street_type = match.group(0)
        if street_type not in expected:
            street_types[street_type].add(street_name)
    pprint.pprint(dict(street_types))

    
# write the sample file into a SQL database

# query this dataset through SQL query

# draw the conclusion
