from collections import OrderedDict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from json import loads, dumps
from os import listdir, makedirs
from os.path import join, isdir, exists, isfile
from shutil import rmtree
from typing import List, Union
from unicodedata import normalize

from twitter import Api


def twitter_call(message: str, credentials: dict):
    """does a twitter API call
    taken from official twitter python github page
    https://github.com/bear/python-twitter/blob/master/examples/tweet.py"""
    consumer_key = credentials.get("API_KEY", "")
    consumer_secret = credentials.get("API_KEY_SECRET", "")
    access_key = credentials.get("ACCESS_TOKEN", "")
    access_secret = credentials.get("ACCESS_TOKEN_SECRET", "")
    encoding = credentials.get('ENCODING', "utf-8")
    api = Api(consumer_key=consumer_key, consumer_secret=consumer_secret,
              access_token_key=access_key, access_token_secret=access_secret,
              input_encoding=encoding, request_headers=None)
    try:
        status = api.PostUpdate(message)
    except UnicodeDecodeError:
        print("whoopsie")
        exit(2)
    print("{0} just posted: {1}".format(status.user.name, status.text))


def create_folder(dir_path: str) -> None:
    if not isdir(dir_path):
        makedirs(name=dir_path)


def remove_folder(dir_path: str) -> None:
    try:
        rmtree(path=dir_path)
    except OSError as e:
        print("Error: %s : %s" % (dir_path, e.strerror))


def write_file(path: str, json: bool, data: Union[str, dict]) -> None:
    """writes file content, if json is True content is json encoded"""
    with open(path, mode="w", encoding="utf-8", errors="strict") as file:
        if json:
            file.write(dumps(data))
        else:
            file.write(data)


def read_file(path: str, json: bool) -> Union[str, dict]:
    """reads a file content and returns it, if json is True content is json decoded"""
    with open(path, mode="r", encoding="utf-8", errors="strict") as file:
        data = file.read()
        if json:
            return loads(data)
        return data


@dataclass
class Calendaritem:
    """Calendaritem represents information about the message, file, sent or sendable status of the message"""
    message: str
    filepath: str
    item_date: date
    message_length: int
    message_max_length = 280
    message_length_exceeded: bool
    message_sendable: bool
    message_icon: str
    logentrys: list
    specialday: str

    def __init__(self, filepath: str, item_date: date) -> None:
        self.filepath = filepath
        self.item_date = item_date
        self.specialday = ""
        self.logentrys = []

    @staticmethod
    def normalize_to_nfc(data: str) -> str:
        """required to normalize message charset to NFC to get the same character count as twitter"""
        return normalize("NFC", data)

    def load_message(self):
        """loads a day item textfile under $year/$calendarweek/$daynum_$dayname.txt"""
        self.message = self.normalize_to_nfc(data=read_file(path=self.filepath, json=False))
        return self

    def initialize(self) -> None:
        """initialises internal variables. must be called after bessage loading"""
        self.message_length = len(self.message)
        self.message_length_exceeded = self.message_length > self.message_max_length
        self.message_sendable = bool(self.message_length and not self.message_length_exceeded)
        self.message_icon = ""

    def set_logs(self, log_list: list) -> None:
        """initially setting eventual existing logs to the day item after creation by Calendarweek class"""
        self.logentrys = log_list

    def add_log(self, message_sent: bool, message_stopped: bool, translate: dict) -> None:
        """adds a logentry regarding being sent or being stopped"""
        logitem = {
            "message_sent": message_sent,
            "log_date": str(datetime.now()),
            "error": self.get_error_text(translate=translate),
            "message": self.message,
            "message_stopped": message_stopped,
        }
        self.logentrys.append(logitem)

    def get_error_text(self, translate: dict, msg="") -> str:
        """returns a specific errortext depending on the cause of the error"""
        if not self.message_length:
            return translate.get("message empty", "message empty")
        elif self.message_length_exceeded:
            return translate.get("message too long", "message too long")
        return msg

    def get_rst_error_text(self, translate: dict) -> str:
        """creates a error text rst item if item has an error"""
        msg = ""
        if not self.message_length or self.message_length_exceeded:
            msg = "Info: " + self.get_error_text(translate=translate)
        return msg

    def has_been_sent(self, translate: dict) -> Union[bool, str]:
        """returns string with time is message has been sent, otherwise False"""
        for item in self.logentrys:
            if item.get("message_sent") and not item.get("message_stopped"):
                return " ".join([translate.get("sent at", "sent at"), "->", item.get("log_date")[:16]])
        return False

    def has_been_stopped(self, translate: dict) -> Union[bool, str]:
        """returns string with time is message has been stopped, otherwise False"""
        for item in self.logentrys:
            if item.get("message_sent") and item.get("message_stopped"):
                return " ".join([translate.get("stopped at", "stopped at"), "->", item.get("log_date")[:16]])
        return False


@dataclass
class Calendarweek:
    """Holds date information about this calendarweek, manages days and their messages"""
    year: str
    week: str
    first_day_of_week: date
    last_day_of_week: date
    items: dict
    week_icon: str

    def __init__(self, year: str, week: str) -> None:
        self.year = year
        self.week = week
        self.first_day_of_week, self.last_day_of_week = self.get_cw_from_to(year=self.year, week=self.week)
        self.items = {}
        self.week_icon = ""

    def prepare_week_report(self) -> None:
        """Prepares a week status indicator by iterating over each day and checking their status.
        also assigns utf-8 status emojis to messages"""
        symbol_ok = "✅"
        symbol_warn = "❎"
        symbol_fail = "❌"
        week_status = symbol_ok
        for day, data in self.items.items():
            if data.message_length_exceeded or not data.message_sendable:
                week_status = symbol_warn
            if data.message_length_exceeded:
                data.message_icon = symbol_fail
                continue
            if not data.message_sendable:
                data.message_icon = symbol_warn
                continue
            data.message_icon = symbol_ok
            self.items[day] = data
        self.week_icon = week_status

    @staticmethod
    def get_cw_from_to(year: str, week: str) -> List[date]:
        """Calculates the start and endday of a calendarweek only given a year and a weeknumber"""
        first_day_of_week = datetime.strptime(f"{year}-W{week}-1", "%Y-W%W-%w").date()
        last_day_of_week = first_day_of_week + timedelta(days=6.9)
        return [first_day_of_week, last_day_of_week]

    @staticmethod
    def get_real_date_by_year_cw_day(year: str, week: str, day: int) -> date:
        """creates a date object from year, week number and day of the week"""
        return datetime.strptime(f"{year}-W{week}-{day}", "%Y-W%W-%w").date()

    def add_file(self, filepath: str, item_date: date) -> None:
        """Initializes a Calendaeitem from a filepath"""
        ci = Calendaritem(filepath=filepath, item_date=item_date)
        ci.load_message()
        ci.initialize()
        self.items[item_date.weekday()] = ci

    def init_log_for_day(self, log: list, day_num: int) -> None:
        """sets a days log back to given log list.
        intendet to be called by Calendarweek durining parsing."""
        day_item = self.items[day_num]
        day_item.set_logs(log_list=log)
        self.items[day_num] = day_item


@dataclass
class TagesgerichtManager:
    """Initialisiert datetime mit now und basiert auf dem heutigen tag
    scans a given Data directory that must follow the structure of

    year/calendarweek/DAYNUM_DAYNAME.txt

    DAYNUM represents the day of the week starting with Monday at 0 and
    ending with sunday at 6

    DAYNAME is defined via weekday_map attribute mapping
    where weekday_map is a dict with DAYNUM as keys and the value as DAYNAME

    only calendarweeks with files should be logged
    the sent.log should come in here as well.
    if files are deleted, but the sendlog holds data for a day, it should be reported.
    like a normal item, with notice that files connected to the logentry couldn't be found.
    """
    year: int
    month: int
    day: int
    data_dir: str
    data: dict
    specialdays: dict
    today: date

    def __init__(self,
                 active_days: List[int],
                 data_dir: str,
                 translation: dict,
                 specialdays: dict,
                 credentials: dict
                 ):
        self.weekday_map = translation.get('weekday_map', {})
        self.active_days = active_days
        self.specialdays = specialdays
        self.credentials = credentials
        self.data_dir = data_dir
        self.year, self.month, self.day = self.get_now_datetime()
        self.today = date(self.year, self.month, self.day)
        self.day_num = self.today.weekday()
        self.current_week = str(self.today.isocalendar()[1])
        self.report_build_folder = "Sphinx-docs/report"
        self.data = {}
        self.translate = translation

    def get_today_from_calendarweek(self) -> Union[Calendaritem, bool]:
        """Returns current Calendaritem day from the Calendarweek"""
        self.init_manager()
        current_week_obj = self.get_current_week_obj()
        return current_week_obj.items.get(self.day_num, False)

    def get_current_week_obj(self) -> Union[Calendarweek, bool]:
        """Returns the current week object from Calendarweek"""
        return self.data.get(str(self.year), {}).get(str(self.current_week), False)

    def show_send_message(self) -> bool:
        """Returns in boolean if a send message should be shown"""
        current_day_obj = self.get_today_from_calendarweek()
        return current_day_obj and not current_day_obj.has_been_sent(
            translate=self.translate) and not current_day_obj.has_been_stopped(
            translate=self.translate) and current_day_obj.message_sendable

    def show_sold_out_message(self) -> bool:
        """Returns in boolean if a sold out message should be shown"""
        current_day_obj = self.get_today_from_calendarweek()
        return current_day_obj and current_day_obj.has_been_sent(
            translate=self.translate) and not current_day_obj.has_been_stopped(translate=self.translate)

    def send_sold_out_message(self) -> bool:
        """Sending the sold out message if a message for today has been sent before returns boolean if successful"""
        self.init_manager()
        current_day_obj = self.get_today_from_calendarweek()
        was_sent = current_day_obj.has_been_sent(translate=self.translate)
        was_stopped = current_day_obj.has_been_stopped(translate=self.translate)
        if was_sent and not was_stopped:
            twitter_call(message=self.translate.get("Meal of the day is sold-out!", "Meal of the day is sold-out!"), credentials=self.credentials)
            current_week_obj = self.get_current_week_obj()
            current_week_obj.items[self.day_num].add_log(message_sent=True, message_stopped=True,
                                                         translate=self.translate)
            self.write_week_logfile(week=self.current_week, items=current_week_obj.items)
            return True

    def send_message_for_today(self) -> bool:
        """Sends a message for today if there is one that is sendable returns boolean if successful"""
        self.init_manager()
        current_day_obj = self.get_today_from_calendarweek()
        if not current_day_obj:
            return False

        if current_day_obj.has_been_sent(translate=self.translate):
            return False

        current_week_obj = self.get_current_week_obj()
        if current_day_obj.message_sendable:
            twitter_call(message=current_day_obj.message, credentials=self.credentials)
            current_week_obj.items[self.day_num].add_log(
                message_sent=True,
                message_stopped=False,
                translate=self.translate
            )
            self.write_week_logfile(week=current_week_obj.week, items=current_week_obj.items)
            return True

        current_week_obj.items[self.day_num].add_log(message_sent=False, message_stopped=False,
                                                     translate=self.translate)
        self.write_week_logfile(week=current_week_obj.week, items=current_week_obj.items)
        return False

    def write_week_logfile(self, week: str, items: dict) -> None:
        """Writes a logfile from each day into a big log.json
        this will be used during initialization to restore days logitems"""
        logfile_path = str(join(self.data_dir, str(self.year), week, "log.json"))
        logfile_content = {}
        for day, data in items.items():
            if not logfile_content.get(str(day)) and not data.logentrys:
                continue
            logfile_content[str(day)] = data.logentrys
        write_file(path=logfile_path, json=True, data=logfile_content)

    @staticmethod
    def get_now_datetime():
        """Returns the current daterime year, month and day"""
        now = datetime.now()
        return now.year, now.month, now.day

    def init_manager(self) -> None:
        """Initing the manager will create required directorys for the current and next calendarweek if they dont exists
        and will then parse the data dir completely.
        all gathered information is then stored into the classes data propterty"""
        cw = date(self.year, self.month, self.day)
        cws = []
        for week_count in range(2):
            if week_count == 0 and not self.has_active_days_left_this_cw(active_days=self.active_days,
                                                                         day_num=self.day_num):
                cw = self.add_week(today=cw)
            self.create_file_structure(
                data_dir=self.data_dir,
                year=str(cw.isocalendar()[0]),
                week=str(cw.isocalendar()[1])
            )
            cws.append(cw.isocalendar())
            cw = self.add_week(today=cw)
        self.data = self.parse_year_dir(path=self.data_dir)

    @staticmethod
    def next_weekday(d: date, weekday: int) -> date:
        """adds days to a datetime object until a desired day it reached, returns that datatime obj"""
        days_ahead = weekday - d.weekday()
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        return d + timedelta(days_ahead)

    def add_week(self, today: date) -> date:
        """adds one week to a given datetime object, start of the week is monday"""
        next_monday = self.next_weekday(today, 0)
        return date(next_monday.year, next_monday.month, next_monday.day)

    @staticmethod
    def has_active_days_left_this_cw(active_days: list, day_num: int) -> bool:
        """Returns if with current configuration there are still active days left in the current calendarweek
        used by init method, if not, it will skip thos week and use next calendarweek as if it were this week.
        """
        if not len(active_days):
            return False
        for i in range(0, 7):
            if i < day_num:
                continue
            if i in active_days:
                return True
        return False

    def create_file_structure(self, data_dir: str, year: str, week: str) -> None:
        """Creates the filestructure for tagesgericht, called by init method"""
        path_year = str(join(data_dir, year))
        path_kw = str(join(data_dir, year, week))
        if not exists(path_year):
            create_folder(dir_path=path_year)
        if not exists(path_kw):
            create_folder(dir_path=path_kw)
        self.create_templates(active_days=self.active_days, folderpath=path_kw)

    def create_templates(self, active_days: list, folderpath: str) -> None:
        """creates the empty daytemplates within the calendarweeksfolder"""
        for day_num in active_days:
            day_name = self.weekday_map.get(str(day_num))
            filename = "{}_{}.txt".format(day_num, day_name)
            filepath = join(folderpath, filename)
            filepath = str(filepath)
            if isfile(filepath):
                continue
            try:
                write_file(path=filepath, data="", json=False)
            except Exception as e:
                print(self.translate.get("couldn't create file, check permissions",
                                         "couldn't create file, check permissions"))
                print(str(type(e)), str(e))

    def parse_year_dir(self, path: str) -> dict:
        """Iterates over each year and trys to initialize calendarweeks within them"""
        result = {}
        for year in listdir(path):
            year_dict = result.get(year, {})
            if year.endswith(".json"):
                continue
            cw_dir = str(join(path, year))
            if isdir(cw_dir):
                result[str(year)] = self.parse_week_dir(path=cw_dir, year_dict=year_dict, year=year)
        return result

    @staticmethod
    def get_new_calendarweek_obj(year: str, week: str) -> Calendarweek:
        """initializes and returns a new calendarweek item"""
        return Calendarweek(year=year, week=week)

    def parse_week_dir(self, path: str, year_dict: dict, year: str) -> dict:
        """parses a calendarweek dir and initializes days by found txt files.
        enriches the calendaritems with old logentrys"""
        for week in listdir(path):
            cw_files_dirpath = str(join(path, week))
            cw_logfile_dirpath = str(join(path, week, "log")) + ".json"
            day_logfiles = {}

            if isfile(path=cw_logfile_dirpath):
                day_logfiles = read_file(path=cw_logfile_dirpath, json=True)

            cw_obj = self.get_new_calendarweek_obj(year=year, week=week)
            for message_file in listdir(cw_files_dirpath):
                if message_file.endswith("log.json"):
                    continue
                if message_file.endswith(".txt"):
                    file_weekday = int(message_file.split("_")[0])
                    fday = date(
                        cw_obj.first_day_of_week.year,
                        cw_obj.first_day_of_week.month,
                        cw_obj.first_day_of_week.day
                    )
                    while fday.weekday() != file_weekday:
                        fday = fday + timedelta(days=1)

                    cw_obj.add_file(
                        filepath=str(join(cw_files_dirpath, message_file)),
                        item_date=fday
                    )
                    specialday = self.specialdays.get(fday.strftime("%d.%m"), False)
                    if specialday:
                        item = cw_obj.items[file_weekday]
                        item.specialday = specialday
                        cw_obj.items[file_weekday] = item

                    day_logfile = day_logfiles.get(str(file_weekday))
                    if day_logfile:
                        cw_obj.init_log_for_day(log=day_logfile, day_num=file_weekday)

            cw_obj.prepare_week_report()
            year_dict[str(week)] = cw_obj
        return year_dict

    def print_data(self) -> None:
        """Prints a short report, intended for usage on the terminal"""
        for year, yearcollection in OrderedDict(sorted(self.data.items())).items():
            for week, cw_obj in OrderedDict(sorted(yearcollection.items())).items():
                print("============================================\n{} {} {} - {} {}".format(
                    self.translate.get("calendarweek", "calendarweek"),
                    cw_obj.week,
                    cw_obj.first_day_of_week.strftime("%d.%m.%Y"),
                    cw_obj.last_day_of_week.strftime("%d.%m.%Y"),
                    cw_obj.week_icon
                ))

                ordered_week_items = OrderedDict(sorted(cw_obj.items.items())).items()
                for day_num, day_obj in ordered_week_items:
                    msgtext = ""
                    if day_obj.specialday:
                        msgtext += self.get_formatted_rst_quote(
                            quote=self.translate.get("Info", "Info"),
                            message=day_obj.specialday
                        )
                    been_sent = day_obj.has_been_sent(translate=self.translate)
                    if not been_sent:
                        msgtext += self.translate.get("unsent", "unsent")
                    else:
                        msgtext += been_sent
                    print(
                        day_obj.filepath,
                        day_obj.message_icon,
                        "",
                        day_obj.get_error_text(translate=self.translate, msg=msgtext) or day_obj.has_been_sent(
                            translate=self.translate)
                    )

    @staticmethod
    def get_rst_line_for_str(string: str, linetype: str) -> str:
        """Formats a underline for a heading in ReStructuredText"""
        line = ""
        for i in range(len(string) + 1):
            line += linetype
        return line

    def get_formatted_rst_header(self, message: str, doubled: bool, linetype: str) -> str:
        """Formats a a heading in ReStructuredText"""
        rst_line = self.get_rst_line_for_str(string=message, linetype=linetype)
        result = ""
        if doubled:
            result += rst_line + "\n"
        result += message + "\n"
        result += rst_line + "\n\n"
        return result

    @staticmethod
    def get_formatted_rst_quote(quote: str, message: str) -> str:
        """Formats a quote in ReStructuredText"""
        result = ""
        result += ":{}:\n\n".format(quote)
        for line in message.split("\n"):
            result += "    {}\n".format(line.strip())
        result += "\n"
        return result

    def return_week_as_rst_string(self, week: Calendarweek) -> str:
        """Formats a week report in ReStructuredText"""
        week_header = "{} {} {}".format(self.translate.get("calendarweek", "calendarweek"), week.week, week.week_icon)
        ret = self.get_formatted_rst_header(message=week_header, doubled=True, linetype="=")
        for day_num, day_data in OrderedDict(sorted(week.items.items())).items():
            day_header = "{}, {} {}".format(self.weekday_map.get(str(day_num)), day_data.item_date.strftime("%d.%m.%Y"),
                                            day_data.message_icon)
            ret += self.get_formatted_rst_header(message=day_header, doubled=False, linetype="^")
            if day_data.specialday:
                ret += self.get_formatted_rst_quote(quote=self.translate.get("Info", "Info"),
                                                    message=day_data.specialday)
            if not day_data.message_length:
                ret += self.get_formatted_rst_quote(quote=self.translate.get("Info", "Info"),
                                                    message=self.translate.get("message empty", "message empty"))
                continue
            if day_data.message_length_exceeded:
                ret += self.get_formatted_rst_quote(quote=self.translate.get("Error", "Error"),
                                                    message=self.translate.get("message too long", "message too long"))
            has_been_sent = day_data.has_been_sent(translate=self.translate)
            if has_been_sent:
                ret += self.get_formatted_rst_quote(quote=self.translate.get("Info", "Info"),
                                                    message=has_been_sent)

            has_been_stopped = day_data.has_been_stopped(translate=self.translate)
            if has_been_stopped:
                ret += self.get_formatted_rst_quote(quote=self.translate.get("Info", "Info"),
                                                    message=has_been_stopped)
            ret += self.get_formatted_rst_quote(quote="", message=day_data.message)

        return ret

    def get_report_legend(self, header: str, history: bool) -> str:
        """Formats a Legend in ReStructuredText"""
        if history:
            ok = "Message was sent"
            warn = "Message was not sent"
            error = "Message was not sent"
        else:
            ok = "Planned message can be sent"
            warn = "Planned message is empty"
            error = "Planned message cant be sent"
        legend = ":✅: {}\n:❎: {}\n:❌: {}".format(
            self.translate.get(ok, ok),
            self.translate.get(warn, warn),
            self.translate.get(error, error),
        )
        ret = ""
        ret += self.get_formatted_rst_header(message=header, doubled=False, linetype="=")
        ret += self.get_formatted_rst_quote(quote=self.translate.get("Legend", "Legend"), message=legend)
        return ret

    def create_rst_data(self) -> None:
        """creates rst data and files for sphinx autogen"""
        remove_folder(dir_path=self.report_build_folder)
        create_folder(dir_path=self.report_build_folder)
        planned_status = self.get_report_legend(
            header=self.translate.get("Future & Active calendar weeks", "Future & Active calendar weeks"),
            history=False
        )
        history = self.get_report_legend(
            header=self.translate.get("Past calendar weeks", "Past calendar weeks"),
            history=True
        )
        for year, yearcollection in OrderedDict(sorted(self.data.items())).items():
            for week, cw_obj in OrderedDict(sorted(yearcollection.items())).items():
                adltcw = not self.has_active_days_left_this_cw(active_days=self.active_days, day_num=self.day_num)
                if cw_obj.week < str(self.current_week) or (cw_obj.week == self.current_week and adltcw):
                    history += self.return_week_as_rst_string(week=cw_obj)
                    continue
                planned_status += self.return_week_as_rst_string(week=cw_obj)
        write_file(path="/".join([self.report_build_folder, "planned_status.rst"]), data=planned_status, json=False)
        write_file(path="/".join([self.report_build_folder, "history.rst"]), data=history, json=False)
