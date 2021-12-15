import sys

from src.Tagesgericht import TagesgerichtManager, read_file


def main(arg: str, lconfig: dict):
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
    for arg in sys.argv[1:]:
        main(arg=arg, lconfig=config)
