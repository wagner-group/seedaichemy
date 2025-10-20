import magic
import requests
import json

# load inverted extension
with open('tool/inverted_extensions.json', 'r') as f:
        inverted_extensions_dict = json.load(f)

def check_magic_num_response(content, filter = None, file_extension=""):
    if isinstance(content, requests.Response):
        try:
            head_bytes = next(content.iter_content(2048))
        except Exception as e:
            raise ValueError(f"Failed to read from response: {e}")
    elif isinstance(content, bytes):
        head_bytes = content[:2048]
    else:
        raise TypeError("`content` must be either `requests.Response` or `bytes`.")
    file_type = magic.from_buffer(head_bytes)
    mime_type = magic.from_buffer(head_bytes, mime=True)
    potential_file_types = inverted_extensions_dict.get(mime_type, None)
    file_extension = file_extension.lower()
    if file_extension != "":
        if (file_extension in file_type.lower()) \
           or (file_extension in mime_type.lower()) \
           or (potential_file_types and file_extension in potential_file_types):
            return True
    # start using specific filter if no file-extension provided
    elif filter != None:
        if (not filter(mime_type)):
            # print(f"not the desired filetype, the file's filetype is {file_type}, desired filetype {file_extension}")
            return False
    else:
        # print(f"didn't provide filter or file_extension")
        raise ValueError(f"didn't provide filter or file_extension to filter file")
    
    print(f"not the desired filetype, the file's filetype is {file_type}, desired filetype {file_extension}")
    return False


def check_magic_num_file(file_path, filter = None, file_extension=""):
    """
    Downloads files from Google Custom Search results based on a given query and file type.

    Args:
       response: web Request response
       filter: a function take in file_type and return false or true
       file_extension: filetype of the desired corpus
    Returns:
        bool: true for right filetype else false
    """
    file_type = magic.from_file(file_path)
    mime_type = magic.from_file(file_path, mime=True)
    potential_file_types = inverted_extensions_dict.get(mime_type, None)
    file_extension = file_extension.lower()
    if file_extension != "":
        if (file_extension in file_type.lower()) \
           or (file_extension in mime_type.lower()) \
           or (potential_file_types and file_extension in potential_file_types):
            return True
    # start using specific filter if no file-extension provided
    elif filter != None:
        if (not filter(mime_type)):
            return False
    else:
        raise ValueError(f"didn't provide filter or file_extension to filter file")
    return False

# generate file extension dictionary magic number check
# File extension to MIME type mapping adapted from:
# https://gist.github.com/Qti3e/6341245314bf3513abb080677cd1c93b
# Released under The Unlicense (public domain)
def generate_exntension_dict(dict_path):
    with open('tool/extensions.json', 'r') as f:
        extensions_dict = json.load(f)
    
    # revert dict
    inverted_extension_dict = {}
    for k, v in extensions_dict.items():
        mime_type = v['mime']
        signs = v['signs']
        inverted_extension_dict.setdefault(mime_type, []).append(k)

    with open('inverted_extensions.json', 'w') as f:
        json.dump(inverted_extension_dict, f, indent=2)

    return inverted_extension_dict


if __name__ == "__main__":
    ...
    # with open('tool/extensions.json', 'r') as f:
    #     extensions_dict = json.load(f)
    
    # # revert dict
    # inverted_extension_dict = {}
    # for k, v in extensions_dict.items():
    #     mime_type = v['mime']
    #     signs = v['signs']
    #     inverted_extension_dict.setdefault(mime_type, []).append(k)

    # with open('inverted_extensions.json', 'w') as f:
    #     json.dump(inverted_extension_dict, f, indent=2)
