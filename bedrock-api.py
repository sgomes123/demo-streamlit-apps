%pip install anthropic --quiet

# Import python's built-in regular expression library
import re
from anthropic import AnthropicBedrock

%store -r MODEL_NAME
%store -r AWS_REGION

client = AnthropicBedrock(aws_region=AWS_REGION)

def get_completion(messages, system_prompt=''):
    message = client.messages.create(
        model=MODEL_NAME,
        max_tokens=2000,
        temperature=0.0,
        messages=messages,
        system=system_prompt
    )
    return message.content[0].text