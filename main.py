from sys import argv

from src.Tagesgericht import TagesgerichtManager, read_file


def bat_handler(larg: str, lconfig: dict):
    tm = config['TagesgerichtManager']
    if larg == 'print_report':
        tm.init_manager()
        tm.print_data()
    elif larg == 'create_report':
        tm.init_manager()
        tm.create_rst_data()
    elif larg == 'send_tweet':
        result = tm.send_message_for_today()
        if not result:
            print(lconfig.get('translate', {}).get("Tweet was not sent, please see report for reason",
                                                   "Tweet was not sent, please see report for reason"))
            print(lconfig.get('translate', {}).get("you can close this window now"))
        else:
            print(result)
    elif larg == 'stop_tweet':
        result = tm.send_sold_out_message()
        if not result:
            print(lconfig.get('translate', {}).get("Tweet was not sent, please see report for reason",
                                                   "Tweet was not sent, please see report for reason"))
            print(lconfig.get('translate', {}).get("you can close this window now"))
        else:
            print(result)
    else:
        print('commend unknown', larg)


def create_report(lconfig: dict):
    cwm = lconfig.get('TagesgerichtManager')
    cwm.init_manager()
    cwm.print_data()
    cwm.create_rst_data()


def close_program(lconfig: dict):
    print(lconfig.get('translate', {}).get('exit program', "exit program"))
    exit(0)


def send_message(lconfig: dict):
    print("sending message")
    cwm = lconfig.get('TagesgerichtManager')
    cwm.send_message_for_today()


def send_sold_out_message(lconfig: dict):
    print("send_sold_out_message")
    cwm = lconfig.get('TagesgerichtManager')
    cwm.send_sold_out_message()


def get_options(lconfig: dict):
    cwm = lconfig.get('TagesgerichtManager')
    options = {
        lconfig.get('translate', {}).get('create report', 'create report'): create_report,
    }
    if cwm.show_send_message():
        options[lconfig.get('translate', {}).get('send message', 'send message')] = send_message
    elif cwm.show_sold_out_message():
        options[lconfig.get('translate', {}).get('send sold out', 'send sold out')] = send_sold_out_message
    options[lconfig.get('translate', {}).get('exit program', 'exit program')] = close_program
    return options


def load_language(code: str) -> dict:
    return read_file('languages/{}.json'.format(code), json=True)


def load_credentials() -> dict:
    return read_file('credentials.json', json=True)


def load_specialdays() -> dict:
    return read_file('specialdays.json', json=True)


def main(lconfig: dict):
    from simple_term_menu import TerminalMenu

    while True:
        options = get_options(lconfig=lconfig)
        terminal_menu = TerminalMenu(list(options.keys()))
        menu_entry_index = terminal_menu.show()
        if not menu_entry_index and menu_entry_index != 0:
            break
        options[list(options.keys())[menu_entry_index]](lconfig=config)


if __name__ == '__main__':
    config = {
        "credentials": load_credentials(),
        "specialdays": load_specialdays(),
        'translate': load_language(code='de'),
        "data_dir": "Data/",
        "active_days": [0, 1, 2, 3, 4],
    }

    config['TagesgerichtManager'] = TagesgerichtManager(
        active_days=config.get('active_days', []),
        data_dir=config.get('data_dir', 'Data'),
        translation=config.get('translate', {}),
        specialdays=config.get('specialdays', {}),
        credentials=config.get('credentials', {}),
    )

    # if main.py has been called with argument
    if argv[1:]:
        for arg in argv[1:]:
            bat_handler(larg=arg, lconfig=config)
        exit(0)
    # else it launches terminal menu
    main(lconfig=config)
    exit(0)
