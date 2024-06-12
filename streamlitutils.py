from datetime import datetime
import pytz
import re

# define a function to convert current datetime in the format of mm-dd-yyyy-hh24-min-sec
def get_current_datetime():
    utc_dt = datetime.now(pytz.utc)
    return utc_dt.strftime("%m-%d-%Y-%H-%M-%S")

# define a function to satisfy regular expression pattern: [a-zA-Z0-9-_.!*'()/]{1,1024}
def conform_to_regex(input_string):
    # Define the regular expression pattern
    pattern = r'^[a-zA-Z0-9-_.!*\'()/]{1,1024}$'
    # Check if the input string matches the pattern
    if re.match(pattern, input_string):
        return input_string
    else:
        # Remove characters that don't match the pattern
        cleaned_string = ''.join(char for char in input_string if re.match(r'[a-zA-Z0-9-_.!*\'()/]', char))
        # Truncate the string if it exceeds the maximum length
        cleaned_string = cleaned_string[:1024]
        return cleaned_string

# define a function to check filetype and return a boolean based on following filetypes 'mp3', 'mp4', 'm4a', 'x-m4a'
def check_filetype(filetype):
    if filetype in ['mp3', 'mp4', 'm4a', 'x-m4a']:
        return True
    else:
        return False