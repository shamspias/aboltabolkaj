import argparse
import json
import xml.etree.ElementTree as ET
from typing import Any, Dict, Optional


class XMLToJSONConverter:
    """
    A class to convert XML data to JSON (via Python dictionary).

    This implementation preserves:
        - Element attributes (stored under "@attributes")
        - Element text (stored under "#text")
        - Tail text (stored under "#tail" if needed)
        - Child elements with the same name as a list
    """

    def convert_file(self, input_file: str, output_file: str, encoding: Optional[str] = "utf-8") -> None:
        """
        Parse an XML file and write its JSON representation to an output file.

        :param input_file: Path to the XML file to be converted.
        :param output_file: Path to the output JSON file.
        :param encoding: File encoding for the XML file (default: "utf-8").
        """
        tree = ET.parse(input_file)
        root = tree.getroot()
        xml_dict = self._element_to_dict(root)

        # Write JSON to file with indentation
        with open(output_file, "w", encoding=encoding) as f:
            json.dump(xml_dict, f, indent=4)

    def _element_to_dict(self, element: ET.Element) -> Dict[str, Any]:
        """
        Recursively convert an ElementTree element into a Python dictionary.

        :param element: The XML element to convert.
        :return: A dictionary representing this element and its children.
        """
        # Prepare the dictionary for this element
        elem_dict: Dict[str, Any] = {}

        # Capture attributes
        if element.attrib:
            elem_dict["@attributes"] = dict(element.attrib)

        # Capture text (if not empty or just whitespace)
        text = (element.text or "").strip()
        if text:
            elem_dict["#text"] = text

        # Process child elements
        for child in element:
            child_dict = self._element_to_dict(child)
            # child_dict will be {child_tag: {...}}
            child_tag = list(child_dict.keys())[0]

            # If this tag already exists, convert to a list or append to it
            if child_tag in elem_dict:
                if not isinstance(elem_dict[child_tag], list):
                    elem_dict[child_tag] = [elem_dict[child_tag]]
                elem_dict[child_tag].append(child_dict[child_tag])
            else:
                # Directly add the child dictionary
                elem_dict.update(child_dict)

        # Optionally capture tail text
        tail = (element.tail or "").strip()
        if tail:
            elem_dict["#tail"] = tail

        # Return dictionary with the current element's tag as the root key
        return {element.tag: elem_dict}


def main():
    """
    Command-line interface to convert an XML file to a JSON file.
    """
    parser = argparse.ArgumentParser(
        description="Convert an XML file to JSON, preserving all data."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to the input XML file",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to the output JSON file",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8",
        help="File encoding (default: utf-8)."
    )
    args = parser.parse_args()

    converter = XMLToJSONConverter()
    converter.convert_file(args.input, args.output, args.encoding)

    print(f"Successfully converted '{args.input}' to '{args.output}'.")


if __name__ == "__main__":
    main()
