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
tags = ['node', 'way', 'relation']


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
mapping_st = {"St": "Street",
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


# write the sample file into a csv
node_fields = ['id', 'lat', 'lon', 'user', 'uid',
               'version', 'changeset', 'timestamp']
node_tags_fields = ['id', 'key', 'value', 'type']
way_fields = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
way_tags_fields = ['id', 'key', 'value', 'type']
way_nodes_fields = ['id', 'node_id', 'position']


def shape_element(element, node_attr_fields=node_fields,
                  way_attr_fields=way_fields,
                  problem_chars=problemchars, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements
    # YOUR CODE HERE
    if element.tag == 'node':
        for item in NODE_FIELDS:
            node_attribs[item] = element.get(item)
        for child in element:
            tag_dict = {}
            colon = child.get('k').find(':')
            if (child.tag == 'tag'):
                tag_dict['id'] = element.get('id')
                tag_dict['value'] = child.get('v')
                if (colon != -1):
                    type_value = child.get('k')[:colon]
                    key_value = child.get('k')[colon+1:]
                    tag_dict['type'] = type_value
                    tag_dict['key'] = key_value
                else:
                    tag_dict['key'] = child.get('k')
                    tag_dict['type'] = 'regular'
                tags.append(tag_dict)
        return {'node': node_attribs, 'node_tags': tags}
    elif element.tag == 'way':
        for item in WAY_FIELDS:
            way_attribs[item] = element.get(item)

        n = 0
        for child in element:
            if child.tag == 'nd':
                nd_dict = {}
                nd_dict['id'] = element.get('id')
                nd_dict['node_id'] = child.get('ref')
                nd_dict['position'] = n
                n += 1
                way_nodes.append(nd_dict)

            if (child.tag == 'tag'):
                way_tag_dict = {}
                colon = child.get('k').find(':')
                way_tag_dict['id'] = element.get('id')
                way_tag_dict['value'] = child.get('v')
                if (colon != -1):
                    type_value = child.get('k')[:colon]
                    key_value = child.get('k')[colon+1:]
                    way_tag_dict['type'] = type_value
                    way_tag_dict['key'] = key_value
                else:
                    way_tag_dict['key'] = child.get('k')
                    way_tag_dict['type'] = 'regular'
                tags.append(way_tag_dict)

        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}


def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w') as nodes_file, \
        codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
        codecs.open(WAYS_PATH, 'w') as ways_file, \
        codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
        codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])


# query this dataset through SQL query

# draw the conclusion
