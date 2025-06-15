import datetime

def get_formatted_datetime():
  """
  Gets the current date and time and formats it as MMDD_HH-mm-ss.

  Returns:
      str: The formatted datetime string.
  """
  now = datetime.datetime.now()
  # Format the datetime object using strftime()
  # %m: Month as a zero-padded decimal number.
  # %d: Day of the month as a zero-padded decimal number.
  # %H: Hour (24-hour clock) as a zero-padded decimal number.
  # %M: Minute as a zero-padded decimal number.
  # %S: Second as a zero-padded decimal number.
  formatted_string = now.strftime("%m%d_%H-%M-%S")
  return formatted_string
