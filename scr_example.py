from elmserial import *

# Andrea Patrucco, 01/12/2019
# Basic example for elmserial library.
# Opens the serial connection, starts polling (with very long timeout) OBD signals.

alfa = Elm327(comport = "COM33", baudrate = 38400)
alfa.open()
alfa.initialize()
# poll a single signal to avoid lag when doing this continuously.
alfa.poll_signal(12, parse_out = False)
alfa.add_to_poll_list(12)
alfa.add_to_poll_list(13)
alfa.add_to_poll_list(16)
alfa.add_to_poll_list(17)
alfa.poll(parse_out = True, timeout = 10000)
