from simple_term_menu import TerminalMenu
from sys import argv
from src.Tagesgericht import TagesgerichtManager, read_file


def bat_handler(arg: str, lconfig: dict):
    TM = TagesgerichtManager(
        weekday_map=lconfig.get('weekday_map'),
        active_days=lconfig.get('active_days'),
        data_dir=lconfig.get('data_dir'),
        language="de",
        specialdays=lconfig.get('specialdays'),
    )
    if arg == 'print_report':
        TM.init_manager()
        TM.print_data()
    elif arg == 'create_report':
        TM.init_manager()
        TM.create_rst_data()
    elif arg == 'send_tweet':
        result = TM.send_message_for_today()
        if not result:
            print(lconfig.get('translate', {}).get("Tweet was not sent, please see report for reason",
                                                   "Tweet was not sent, please see report for reason"))
            print(lconfig.get('translate', {}).get("you can close this window now"))
        else:
            print(result)
    elif arg == 'stop_tweet':
        result = TM.send_sold_out_message()
        if not result:
            print(lconfig.get('translate', {}).get("Tweet was not sent, please see report for reason",
                                                   "Tweet was not sent, please see report for reason"))
            print(lconfig.get('translate', {}).get("you can close this window now"))
        else:
            print(result)
    else:
        print('commend unknown', arg)

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


def main(lconfig: dict):
    lconfig['TagesgerichtManager'] = TagesgerichtManager(
        weekday_map=config.get('weekday_map'),
        active_days=config.get('active_days'),
        data_dir=config.get('data_dir'),
        language="de",
        specialdays=config.get('specialdays'),
    )

    while True:
        options = get_options(lconfig=config)
        terminal_menu = TerminalMenu(list(options.keys()))
        menu_entry_index = terminal_menu.show()
        if not menu_entry_index and menu_entry_index != 0:
            break
        options[list(options.keys())[menu_entry_index]](lconfig=config)


if __name__ == '__main__':
    credentials = read_file('credentials.json', json=True)
    config = {
        "credentials": {
            "API_KEY": credentials.get('API_KEY', ''),
            "API_KEY_SECRET": credentials.get('API_KEY_SECRET', ''),
            "BEARER_TOKEN": credentials.get('BEARER_TOKEN', ''),
            "ACCESS_TOKEN": credentials.get('ACCESS_TOKEN', ''),
            "ACCESS_TOKEN_SECRET": credentials.get('ACCESS_TOKEN_SECRET', ''),
        },
        "specialdays": read_file(path="specialdays.json", json=True),
        "data_dir": "Data/",
        "active_days": [0, 1, 2, 3, 4],
        'weekday_map': {
            0: 'Montag',
            1: 'Dienstag',
            2: 'Mittwoch',
            3: 'Donnerstag',
            4: 'Freitag',
            5: 'Samstag',
            6: 'Sonntag',
        },
        'translate': {
            "exit program": "Programm beenden",
            "create report": "Report erstellen",
            "Tweet was not sent, please see report for reason": "Tweet wurde nicht gesendet, bitte report einsehen für grund",
            "you can close this window now": "Sie können das Fenster nun schließen!"
        }
    }
    if argv[1:]:
        for arg in argv[1:]:
            bat_handler(arg=arg, lconfig=config)
        exit(0)
    main(lconfig=config)
    exit(0)
