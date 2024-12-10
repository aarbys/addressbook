import configparser

from .logger import log
import os

# Print config in human-readable form
# def printConfig(config):
#     for key in config:
#         print(key, config[key])
#         for k in config[key]:
#             print(f'  {k} = {config[key][k]} ({type(config[key][k])})')

dirname = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(dirname,"wb.ini")

config = configparser.ConfigParser()

config.read(CONFIG_FILE, encoding="utf-8")

#  printConfig(config)

# Validate config
def validate(config, section, key, valueType):
    checker = {
        int: config.getint,
        float: config.getfloat,
        bool: config.getboolean,
    }.get(valueType, config.get)

    try:
        v = checker(section, key)
        if checker is bool:
            config[section][key] = str(v).lower()
    except ValueError:
        log.error("Wrong value [%s]%s in %s", section, key, CONFIG_FILE)
        pass


validate(config, 'book', 'address', str)
validate(config, 'book', 'port', int)
validate(config, 'book', 'service', str)
validate(config, 'book', 'sipdomain', str)
validate(config, 'book', 'user_agent', str)
validate(config, 'book', 'translit', bool)
validate(config, 'book', 'skip_no_display_name', bool)
validate(config, 'book', 'show_lines', int)
validate(config, 'book', 'cache_expire_sec', int)
validate(config, 'proxy', 'address', str)
validate(config, 'proxy', 'port', int)
validate(config, 'www', 'static_location', str)
validate(config, 'www', 'info', str)


if config.get('book', 'sipdomain') == '':
    print(f"Run in demo mode. Configure SIP domain in {CONFIG_FILE}")

book_URI_TEMPLATE = "http://{address}:{port}/{service}?host=book" \
                     + "&user_agent={user_agent}" \
                     + "&domain={sipdomain}" \
                     + "&translit={translit}" \
                     + "&skip_no_disp={skip_no_display_name}"

urls = [book_URI_TEMPLATE.format(**config['book'])]
names = [config['book']['name']]
for i in range(int(config['book']['additional_servers'])):
    urls.append(book_URI_TEMPLATE.format(**config[f'server_{i}']))
    names.append(config[f"server_{i}"]['name'])
