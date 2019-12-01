# pyelmserial
Basic Python interface to serial Elm 327 compatible OBD-2 readers

Usage:
- Define a COM port when declaring the Elm 327 object
- Use the .open() function to link the object with a serial port
- Use .initialize() to deliver basic commands
- Add signals you are interested into with .add_to_poll_list
- Use .poll() to periodically poll signals. Add timeout=X seconds to define how long; add parse_out if you want the output strings
  to be parsed immediately and added to log.
