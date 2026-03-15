import re
import os

log_file = "d:\\Genesis IT Lab\\Test-Gen-ChatBot\\User\\backend\\app.log"
# Let's check if there's a log file or we just read the console.
# Since it's run via run_command, we need the standard output... wait, I can't easily capture the previous output without read_terminal.
