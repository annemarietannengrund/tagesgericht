from datetime import date, datetime
from unittest import TestCase
from unittest.mock import patch, call, mock_open, Mock

from src.Tagesgericht import Calendaritem, Calendarweek, TagesgerichtManager
from src.Tagesgericht import create_folder, remove_folder, write_file, read_file


class TestReadWriteDeleteFiles(TestCase):

    @patch("src.Tagesgericht.isdir")
    @patch("src.Tagesgericht.makedirs")
    def test_create_folder_calls_makedirs(self, makedirs, isdir):
        """tests if calling create_folder calls makedirs """
        isdir.return_value = False
        create_folder(dir_path="unittest/unittest")
        makedirs.assert_called_once_with(name="unittest/unittest")

    @patch("src.Tagesgericht.isdir")
    @patch("src.Tagesgericht.makedirs")
    def test_create_folder_exists_not_calls_makedirs(self, makedirs, isdir):
        """tests if calling create_folder, when folder exists, doesnt calls makedirs """
        isdir.return_value = True
        create_folder(dir_path="unittest/unittest")
        makedirs.assert_not_called()

    @patch("src.Tagesgericht.rmtree")
    def test_remove_folder(self, rmtree):
        """tests if calling remove_folder calls rmtree """
        remove_folder(dir_path="unittest")
        rmtree.assert_called_once_with(path="unittest")

    @patch("src.Tagesgericht.rmtree")
    @patch("src.Tagesgericht.print")
    def test_remove_folder_handles_exception(self, lprint, rmtree):
        """Asserts that in case an exception occurs, it is handled"""
        rmtree.side_effect = OSError("unittest_error")
        remove_folder(dir_path="unittest")
        self.assertRaises(Exception)
        rmtree.assert_called_once_with(path="unittest")
        lprint.assert_called_once_with("Error: unittest : None")

    @patch("builtins.open", new_callable=mock_open)
    def test_write_file(self, lopen):
        """Tests if write file is using its arguments as intended"""
        write_file(path="test.zxz", json=False, data="unittest")
        lopen.assert_has_calls([
            call("test.zxz", mode="w", encoding="utf-8", errors="strict"),
            call().__enter__(),
            call().write("unittest"),
            call().__exit__(None, None, None)
        ])

    @patch("builtins.open", new_callable=mock_open)
    def test_write_file_json(self, lopen):
        """checks that write_file is creting a file with json content if json flag is set to True"""
        write_file(path="test.json", json=True, data={"unittest": "unittest"})
        lopen.assert_has_calls([
            call("test.json", mode="w", encoding="utf-8", errors="strict"),
            call().__enter__(),
            call().write('{"unittest": "unittest"}'),
            call().write({"unittest": "unittest"}),
            call().__exit__(None, None, None)
        ])

    @patch("builtins.open", new_callable=mock_open, read_data="data")
    def test_read_file(self, lopen):
        """tests it open is called with appropiate arguments"""
        result = read_file(path="test.txt", json=False)
        lopen.assert_has_calls([
            call("test.txt", mode="r", encoding="utf-8", errors="strict"),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None)
        ])
        self.assertEqual("data", result)

    @patch("builtins.open", new_callable=mock_open, read_data='{"unittest":"unittest"}')
    @patch("src.Tagesgericht.loads", return_value={"unittest": "unittest"})
    def test_read_file_json(self, loads, lopen):
        """tests if loading a file as json decodes the json value to a object"""
        result = read_file(path="test.json", json=True)
        lopen.assert_has_calls([
            call("test.json", mode="r", encoding="utf-8", errors="strict"),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None)
        ])
        loads.assert_called_once_with('{"unittest":"unittest"}')
        self.assertEqual({"unittest": "unittest"}, result)


class TestCalendaritem(TestCase):

    @patch("src.Tagesgericht.read_file", return_value="unittest_file_contents")
    @patch("src.Tagesgericht.Calendaritem.normalize_to_nfc", return_value="unittest_file_contents")
    def test_calendaritem(self, normalize_to_nfc, lread_file):
        """tests that initializing an calendaritem sets all internal values"""
        item_date = datetime.now()
        filepath = "unittest"
        ci = Calendaritem(item_date=item_date, filepath=filepath)
        ci.load_message().initialize()
        normalize_to_nfc.assert_called_once_with(data="unittest_file_contents")
        lread_file.assert_called_once_with(path=filepath, json=False)
        self.assertEqual(filepath, ci.filepath)
        self.assertEqual("unittest_file_contents", ci.message)
        self.assertEqual(item_date, ci.item_date)
        self.assertEqual(len("unittest_file_contents"), ci.message_length)
        self.assertEqual(False, ci.message_length_exceeded)
        self.assertEqual(True, ci.message_sendable)
        self.assertEqual("", ci.message_icon)

    @patch("src.Tagesgericht.read_file", return_value="unittest_file_contents")
    def test_normalize_to_nfc(self, lread_file):
        """Asserts that function returns a string from a string"""
        item_date = datetime.now()
        filepath = "unittest"
        ci = Calendaritem(item_date=item_date, filepath=filepath)
        result = ci.normalize_to_nfc(data="unittest_file_contents")
        self.assertEqual("unittest_file_contents", result)
        lread_file.assert_not_called()

    @patch("src.Tagesgericht.read_file", return_value="unittest_file_contents")
    def test_set_logs(self, lread_file):
        """Tests that by calling set_logs on a calendaritem is overwriting its logs"""
        item_date = datetime.now()
        filepath = "unittest"
        ci = Calendaritem(item_date=item_date, filepath=filepath)
        ci.set_logs(log_list=[{"unittest": "unittest"}])
        self.assertEqual([{"unittest": "unittest"}], ci.logentrys)
        lread_file.assert_not_called()

    @patch("src.Tagesgericht.read_file", return_value="unittest_file_contents")
    @patch("src.Tagesgericht.datetime")
    @patch("src.Tagesgericht.Calendaritem.get_error_text", return_value="unittest error text")
    def test_add_log(self, get_error_text, ldatetime, lread_file):
        """Tests that adding a log really adds a logitem to a calendaritem"""
        ldatetime.now.return_value = datetime.now()
        filepath = "unittest"
        ci = Calendaritem(item_date=ldatetime.now.return_value, filepath=filepath)
        ci.message = "unittest_message"
        ci.add_log(message_sent=True, message_stopped=False, translate={})
        self.assertEqual([
            {
                "error": "unittest error text",
                "log_date": str(ldatetime.now.return_value),
                "message": "unittest_message",
                "message_sent": True,
                "message_stopped": False
            }],
            ci.logentrys
        )
        get_error_text.assert_called_once_with(translate={})
        lread_file.assert_not_called()

    def test_get_error_text(self):
        """tests that based on calendaritem propertys different error messages are set"""
        ci = Calendaritem(item_date=datetime.now(), filepath="unittest")
        ci.message_length = 0
        error_text = ci.get_error_text(translate={}, msg="unittest_message")
        self.assertEqual("message empty", error_text)

        ci.message_length = 1
        ci.message_length_exceeded = True
        error_text = ci.get_error_text(translate={}, msg="unittest_message")
        self.assertEqual("message too long", error_text)

        ci.message_length_exceeded = False
        error_text = ci.get_error_text(translate={}, msg="unittest_message")
        self.assertEqual("unittest_message", error_text)

    def test_get_rst_error_text(self):
        """Tests validity and format of a generated ReStructuredText error text"""
        ci = Calendaritem(item_date=datetime.now(), filepath="unittest")
        ci.message_length = 0
        error_text = ci.get_rst_error_text(translate={})
        self.assertEqual("Info: message empty", error_text)

        ci.message_length = 1
        ci.message_length_exceeded = True
        error_text = ci.get_rst_error_text(translate={})
        self.assertEqual("Info: message too long", error_text)

        ci.message_length_exceeded = False
        error_text = ci.get_rst_error_text(translate={})
        self.assertEqual("", error_text)

    def test_has_been_sent_false(self):
        """Assert that when no sent logentry exists has_been_sent returns False"""
        ci = Calendaritem(item_date=datetime.now(), filepath="unittest")
        ci.logentrys = [
            {"message_sent": False, "message_stopped": False}
        ]
        result = ci.has_been_sent(translate={})
        self.assertEqual(False, result)

    def test_has_been_sent_true(self):
        """Assert that when a sent logentry exists has_been_sent returns a string containing the sent date"""
        ci = Calendaritem(item_date=datetime.now(), filepath="unittest")
        ci.logentrys = [
            {"message_sent": True, "message_stopped": False, "log_date": "2021-06-13 12:30:00:534634363iZ+"}
        ]
        result = ci.has_been_sent(translate={})
        self.assertEqual("sent at -> 2021-06-13 12:30", result)

    def test_has_been_stopped_false(self):
        """Assert that when no stopped logentry exists has_been_sent returns False"""
        ci = Calendaritem(item_date=datetime.now(), filepath="unittest")
        ci.logentrys = [
            {"message_sent": True, "message_stopped": False}
        ]
        result = ci.has_been_stopped(translate={})
        self.assertEqual(False, result)

    def test_has_been_stopped_true(self):
        """Assert that when a stopped logentry exists has_been_sent returns a string containing the sent date"""
        ci = Calendaritem(item_date=datetime.now(), filepath="unittest")
        ci.logentrys = [
            {"message_sent": True, "message_stopped": True, "log_date": "2021-06-13 12:30:00:534634363iZ+"}
        ]
        result = ci.has_been_stopped(translate={})
        self.assertEqual("stopped at -> 2021-06-13 12:30", result)


class TestCalendarweek(TestCase):

    def setUp(self) -> None:
        calendaritem_mock0 = Mock()
        calendaritem_mock0.message = "test 1"
        calendaritem_mock0.filepath = "unittest/mock/test1.txt"
        calendaritem_mock0.item_date = date(2021, 6, 13)
        calendaritem_mock0.message_length = 0
        calendaritem_mock0.message_length_exceeded = False
        calendaritem_mock0.message_sendable = True
        calendaritem_mock0.message_icon = ""

        calendaritem_mock1 = Mock()
        calendaritem_mock1.message = "test 2"
        calendaritem_mock1.filepath = "unittest/mock/test2.txt"
        calendaritem_mock1.item_date = date(2021, 6, 13)
        calendaritem_mock1.message_length = 4
        calendaritem_mock1.message_length_exceeded = False
        calendaritem_mock1.message_sendable = True
        calendaritem_mock1.message_icon = ""

        self.calendaritem_mock0 = calendaritem_mock0
        self.calendaritem_mock1 = calendaritem_mock1

        self.weekday_map = {
            0: "Montag",
            1: "Dienstag",
            2: "Mittwoch",
            3: "Donnerstag",
            4: "Freitag",
            5: "Samstag",
            6: "Sonntag",
        }
        self.active_days = [0, 1, 2, 3, 4]
        self.data_dir = "unittest"

    def test_calendarweek(self):
        """Tests initialization of a calendarweek object"""
        cw = Calendarweek(year="2021", week="42")
        self.assertEqual(date(2021, 10, 18), cw.first_day_of_week)
        self.assertEqual(date(2021, 10, 24), cw.last_day_of_week)
        self.assertEqual("2021", cw.year)
        self.assertEqual("42", cw.week)
        self.assertEqual({}, cw.items)
        self.assertEqual("", cw.week_icon)

    @patch("src.Tagesgericht.Calendarweek.get_cw_from_to",
           return_value=["first_day_of_week_item", "last_day_of_week_item"])
    def test_get_cw_from_to_called(self, get_cw_from_to):
        """Tests that initializing a Calendarweek is calling get_cw_from_to """
        cw = Calendarweek(year="2021", week="42")
        get_cw_from_to.assert_called_once_with(year="2021", week="42")
        self.assertEqual(
            ["first_day_of_week_item", "last_day_of_week_item"],
            [cw.first_day_of_week, cw.last_day_of_week]
        )

    def test_prepare_week_report_all_ok(self):
        """tests prepare_week_report where all items are in perfect shape"""
        calendaritem_mock0 = self.calendaritem_mock0

        calendaritem_mock1 = self.calendaritem_mock1
        week_dict = {
            0: calendaritem_mock0,
            1: calendaritem_mock1,
        }
        cw = Calendarweek(year="2021", week="42")
        cw.items = week_dict
        cw.prepare_week_report()
        self.assertEqual("✅", cw.week_icon)
        self.assertEqual("✅", calendaritem_mock0.message_icon)
        self.assertEqual("✅", calendaritem_mock1.message_icon)

    def test_prepare_week_report_one_error(self):
        """tests prepare_week_report where all but one item are in perfect shape"""
        calendaritem_mock0 = self.calendaritem_mock0
        calendaritem_mock0.message_length = 300
        calendaritem_mock0.message_length_exceeded = True
        calendaritem_mock0.message_sendable = False

        calendaritem_mock1 = self.calendaritem_mock1
        week_dict = {
            0: calendaritem_mock0,
            1: calendaritem_mock1,
        }
        cw = Calendarweek(year="2021", week="42")
        cw.items = week_dict
        cw.prepare_week_report()
        self.assertEqual("❎", cw.week_icon)
        self.assertEqual("❌", calendaritem_mock0.message_icon)
        self.assertEqual("✅", calendaritem_mock1.message_icon)

    def test_prepare_week_report_one_empty(self):
        """tests prepare_week_report where one item is empty"""
        calendaritem_mock0 = self.calendaritem_mock0
        calendaritem_mock0.message_length = 0
        calendaritem_mock0.message_sendable = False

        calendaritem_mock1 = self.calendaritem_mock1
        week_dict = {
            0: calendaritem_mock0,
            1: calendaritem_mock1,
        }
        cw = Calendarweek(year="2021", week="42")
        cw.items = week_dict
        cw.prepare_week_report()
        self.assertEqual("❎", cw.week_icon)
        self.assertEqual("❎", calendaritem_mock0.message_icon)
        self.assertEqual("✅", calendaritem_mock1.message_icon)

    def test_get_real_date_by_year_cw_day(self):
        """tests if get_real_date_by_year_cw_day really returns an expected real date"""
        cw = Calendarweek(year="2021", week="42")
        items = cw.get_real_date_by_year_cw_day(year="2021", week="42", day=1)
        self.assertEqual(date(2021, 10, 18), items)

    @patch("src.Tagesgericht.Calendaritem.initialize")
    @patch("src.Tagesgericht.Calendaritem.load_message")
    def test_add_file(self, load_message, initialize):
        """Tests that adding a file here initializes a new day item in teh calendarweek"""
        cw = Calendarweek(year="2021", week="42")
        cw.add_file(filepath="unittest", item_date=date(2021, 6, 13))
        initialize.assert_called_once_with()
        load_message.assert_called_once_with()
        self.assertEqual(1, len(cw.items))

    def test_init_log_for_day(self):
        """tests that init log for the day function inits the log for the day from the calendarweek obj"""
        cw = Calendarweek(year="2021", week="42")
        day_item = Mock()
        cw.items = {
            0: day_item
        }
        cw.init_log_for_day(log=[{"unittest": "unittest"}], day_num=0)
        day_item.set_logs.assert_called_once_with(log_list=[{"unittest": "unittest"}])


class TestTagesgerichtManager(TestCase):

    def setUp(self) -> None:
        self.weekday_map = {
            0: "Montag",
            1: "Dienstag",
            2: "Mittwoch",
            3: "Donnerstag",
            4: "Freitag",
            5: "Samstag",
            6: "Sonntag",
        }
        self.active_days = [0, 1, 2, 3, 4]
        self.data_dir = "unittest"
        self.year = "2021"
        self.week = "42"

    @patch("src.Tagesgericht.TagesgerichtManager.get_now_datetime", return_value=[2021, 6, 13])
    @patch("src.Tagesgericht.read_file", return_value={})
    def test_init(self, lread_file, get_now_datetime):
        today = date(2021, 6, 13)
        cwm = TagesgerichtManager(
            weekday_map=self.weekday_map,
            active_days=self.active_days,
            data_dir=self.data_dir,
            language="de",
            specialdays={}
        )
        get_now_datetime.assert_has_calls([call()])
        self.assertEqual(today, cwm.today)
        self.assertEqual(6, cwm.day_num)
        self.assertEqual("23", cwm.current_week)
        lread_file.assert_called_once_with(path="translate_de.json", json=True)

    @patch("src.Tagesgericht.read_file", return_value={})
    def test_get_now_datetime(self, lread_file):
        cwm = TagesgerichtManager(
            weekday_map=self.weekday_map,
            active_days=self.active_days,
            data_dir=self.data_dir,
            language="de",
            specialdays={}
        )
        result = cwm.get_now_datetime()
        now = datetime.now()
        self.assertEqual((now.year, now.month, now.day), result)
        lread_file.assert_called_once_with(path="translate_de.json", json=True)

    @patch("src.Tagesgericht.TagesgerichtManager.add_week")
    @patch("src.Tagesgericht.TagesgerichtManager.parse_year_dir", return_value={})
    @patch("src.Tagesgericht.TagesgerichtManager.create_file_structure", return_value=None)
    @patch("src.Tagesgericht.read_file", return_value={})
    def test_init_manager_no_active_days_left(self, lread_file, create_file_structure, parse_year_dir, add_week):
        add_week.side_effect = [date(2021, 6, 19), date(2021, 6, 25), date(2021, 7, 4)]
        self.active_days = []
        parse_year_dir.return_value = "parsed_data"
        cwm = TagesgerichtManager(
            weekday_map=self.weekday_map,
            active_days=self.active_days,
            data_dir=self.data_dir,
            language="de",
            specialdays={}
        )
        cwm.year, cwm.month, cwm.day = 2021, 6, 13
        cwm.init_manager()
        create_file_structure.assert_has_calls([
            call(data_dir="unittest", year="2021", week="24"),
            call(data_dir="unittest", year="2021", week="25")
        ])
        add_week.assert_has_calls([
            call(today=date(2021, 6, 13)),
            call(today=date(2021, 6, 19))
        ])
        parse_year_dir.assert_called_once_with(path="unittest")
        self.assertEqual(cwm.data, "parsed_data")
        lread_file.assert_called_once_with(path="translate_de.json", json=True)

    @patch("src.Tagesgericht.TagesgerichtManager.add_week")
    @patch("src.Tagesgericht.TagesgerichtManager.parse_year_dir", return_value={})
    @patch("src.Tagesgericht.TagesgerichtManager.create_file_structure", return_value=None)
    @patch("src.Tagesgericht.read_file", return_value={})
    def test_init_manager_active_days_left(self, lread_file, create_file_structure, parse_year_dir, add_week):
        add_week.side_effect = [date(2021, 6, 19), date(2021, 6, 25)]
        self.active_days = [0, 1, 2, 3, 4, 5, 6]
        parse_year_dir.return_value = "parsed_data"

        cwm = TagesgerichtManager(
            weekday_map=self.weekday_map,
            active_days=self.active_days,
            data_dir=self.data_dir,
            language="de",
            specialdays={}
        )
        cwm.year, cwm.month, cwm.day = 2021, 6, 13
        cwm.init_manager()
        create_file_structure.assert_has_calls([
            call(data_dir="unittest", year="2021", week="23"),
            call(data_dir="unittest", year="2021", week="24")
        ])
        add_week.assert_has_calls([
            call(today=date(2021, 6, 13)),
            call(today=date(2021, 6, 19))
        ])
        parse_year_dir.assert_called_once_with(path="unittest")
        self.assertEqual(cwm.data, "parsed_data")
        lread_file.assert_called_once_with(path="translate_de.json", json=True)

    @patch("src.Tagesgericht.read_file", return_value={})
    def test_next_weekday(self, lread_file):
        today = date(2021, 12, 13)  # monday
        next_monday = date(2021, 12, 20)
        next_friday = date(2021, 12, 17)
        cwm = TagesgerichtManager(
            weekday_map=self.weekday_map,
            active_days=self.active_days,
            data_dir=self.data_dir,
            language="de",
            specialdays={}
        )
        result = cwm.next_weekday(d=today, weekday=0)
        self.assertEqual(next_monday, result)
        result = cwm.next_weekday(d=today, weekday=4)
        self.assertEqual(next_friday, result)
        lread_file.assert_called_once_with(path="translate_de.json", json=True)

    @patch("src.Tagesgericht.read_file", return_value={})
    def test_add_week(self, lread_file):
        today = date(2021, 12, 13)
        next_week = date(2021, 12, 20)
        cwm = TagesgerichtManager(
            weekday_map=self.weekday_map,
            active_days=self.active_days,
            data_dir=self.data_dir,
            language="de",
            specialdays={}
        )
        result = cwm.add_week(today=today)
        self.assertEqual(next_week, result)

        wednesay = date(2021, 12, 15)
        result = cwm.add_week(today=wednesay)
        self.assertEqual(next_week, result)
        lread_file.assert_called_once_with(path="translate_de.json", json=True)

    @patch("src.Tagesgericht.read_file", return_value={})
    def test_has_active_days_left_this_cw(self, lread_file):
        active_days = [0, 1, 2, 3, 4, 5, 6]
        current_day_num = 3
        cwm = TagesgerichtManager(
            weekday_map=self.weekday_map,
            active_days=self.active_days,
            data_dir=self.data_dir,
            language="de",
            specialdays={}
        )
        self.assertTrue(cwm.has_active_days_left_this_cw(active_days=active_days, day_num=current_day_num))
        active_days = [0, 1, 2, 3, 6]
        self.assertTrue(cwm.has_active_days_left_this_cw(active_days=active_days, day_num=current_day_num))
        active_days = [0, 1, 2]
        self.assertFalse(cwm.has_active_days_left_this_cw(active_days=active_days, day_num=current_day_num))
        active_days = []
        self.assertFalse(cwm.has_active_days_left_this_cw(active_days=active_days, day_num=current_day_num))
        lread_file.assert_called_once_with(path="translate_de.json", json=True)

    @patch("src.Tagesgericht.exists", return_value=False)
    @patch("src.Tagesgericht.makedirs")
    @patch("src.Tagesgericht.TagesgerichtManager.create_templates")
    @patch("src.Tagesgericht.join", side_effect=["unittest/2121", "unittest/2121/42"])
    @patch("src.Tagesgericht.read_file", return_value={})
    def test_create_file_structure(self, lread_file, join, create_templates, makedirs, exists):
        exists.side_effect = [False, False]
        cwm = TagesgerichtManager(
            weekday_map=self.weekday_map,
            active_days=self.active_days,
            data_dir=self.data_dir,
            language="de",
            specialdays={}
        )
        cwm.create_file_structure(data_dir=self.data_dir, year=self.year, week=self.week)
        join.assert_has_calls([
            call("unittest", "2021"),
            call("unittest", "2021", "42")
        ])
        create_templates.assert_called_once_with(active_days=[0, 1, 2, 3, 4], folderpath="unittest/2121/42")
        makedirs.assert_has_calls([
            call(name="unittest/2121")
        ])
        exists.assert_has_calls([
            call("unittest/2121")
        ])
        lread_file.assert_called_once_with(path="translate_de.json", json=True)

    @patch("src.Tagesgericht.exists", return_value=False)
    @patch("src.Tagesgericht.makedirs")
    @patch("src.Tagesgericht.TagesgerichtManager.create_templates")
    @patch("src.Tagesgericht.join", side_effect=["unittest/2121", "unittest/2121/42"])
    @patch("src.Tagesgericht.read_file", return_value={})
    def test_create_file_structure_exists(self, lread_file, join, create_templates, makedirs, exists):
        exists.side_effect = [True, True]
        cwm = TagesgerichtManager(
            weekday_map=self.weekday_map,
            active_days=self.active_days,
            data_dir=self.data_dir,
            language="de",
            specialdays={}
        )
        cwm.create_file_structure(data_dir=self.data_dir, year=self.year, week=self.week)
        join.assert_has_calls([
            call("unittest", "2021"),
            call("unittest", "2021", "42")
        ])
        create_templates.assert_called_once_with(active_days=[0, 1, 2, 3, 4], folderpath="unittest/2121/42")
        makedirs.assert_not_called()
        exists.assert_has_calls([
            call("unittest/2121")
        ])
        lread_file.assert_called_once_with(path="translate_de.json", json=True)

    @patch("src.Tagesgericht.write_file")
    @patch("src.Tagesgericht.join")
    @patch("src.Tagesgericht.isfile")
    @patch("src.Tagesgericht.read_file", return_value={})
    def test_create_templates(self, lread_file, isfile, join, lwrite_file):
        join.side_effect = [
            "unittest/0_Montag.txt",
            "unittest/1_Dienstag.txt",
            "unittest/2_Mittwoch.txt",
            "unittest/3_Donnerstag.txt",
            "unittest/4_Freitag.txt",
        ]
        isfile.side_effect = [
            True,
            False,
            True,
            False,
            True
        ]
        cwm = TagesgerichtManager(
            weekday_map=self.weekday_map,
            active_days=self.active_days,
            data_dir=self.data_dir,
            language="de",
            specialdays={}
        )
        cwm.create_templates(active_days=self.active_days, folderpath=self.data_dir)
        join.assert_has_calls([
            call("unittest", "0_Montag.txt"),
            call("unittest", "1_Dienstag.txt"),
            call("unittest", "2_Mittwoch.txt"),
            call("unittest", "3_Donnerstag.txt"),
            call("unittest", "4_Freitag.txt")
        ])
        isfile.assert_has_calls([
            call("unittest/0_Montag.txt"),
            call("unittest/1_Dienstag.txt"),
            call("unittest/2_Mittwoch.txt"),
            call("unittest/3_Donnerstag.txt"),
            call("unittest/4_Freitag.txt")
        ])
        lwrite_file.assert_has_calls([
            call(path="unittest/1_Dienstag.txt", data="", json=False),
            call(path="unittest/3_Donnerstag.txt", data="", json=False)
        ])
        lread_file.assert_called_once_with(path="translate_de.json", json=True)

    @patch("src.Tagesgericht.write_file")
    @patch("src.Tagesgericht.join")
    @patch("src.Tagesgericht.isfile")
    @patch("src.Tagesgericht.print")
    @patch("src.Tagesgericht.read_file", return_value={})
    def test_create_templates_handles_exception(self, lread_file, lprint, isfile, join, lwrite_file):
        join.side_effect = [
            "unittest/0_Montag.txt",
            "unittest/1_Dienstag.txt",
            "unittest/2_Mittwoch.txt",
            "unittest/3_Donnerstag.txt",
            "unittest/4_Freitag.txt",
        ]
        isfile.side_effect = [
            True,
            False,
            True,
            False,
            True
        ]
        lwrite_file.side_effect = Exception("unittest_exception")
        cwm = TagesgerichtManager(
            weekday_map=self.weekday_map,
            active_days=self.active_days,
            data_dir=self.data_dir,
            language="de",
            specialdays={}
        )
        cwm.create_templates(active_days=self.active_days, folderpath=self.data_dir)
        lprint.assert_has_calls([
            call("couldn't create file, check permissions"),
            call("<class 'Exception'>", "unittest_exception"),
            call("couldn't create file, check permissions"),
            call("<class 'Exception'>", "unittest_exception")
        ])
        join.assert_has_calls([
            call("unittest", "0_Montag.txt"),
            call("unittest", "1_Dienstag.txt"),
            call("unittest", "2_Mittwoch.txt"),
            call("unittest", "3_Donnerstag.txt"),
            call("unittest", "4_Freitag.txt")
        ])
        isfile.assert_has_calls([
            call("unittest/0_Montag.txt"),
            call("unittest/1_Dienstag.txt"),
            call("unittest/2_Mittwoch.txt"),
            call("unittest/3_Donnerstag.txt"),
            call("unittest/4_Freitag.txt")
        ])
        lwrite_file.assert_has_calls([
            call(path="unittest/1_Dienstag.txt", data="", json=False),
            call(path="unittest/3_Donnerstag.txt", data="", json=False)
        ])
        self.assertRaises(Exception)
        lread_file.assert_called_once_with(path="translate_de.json", json=True)

    @patch("src.Tagesgericht.TagesgerichtManager.parse_week_dir")
    @patch("src.Tagesgericht.join")
    @patch("src.Tagesgericht.listdir")
    @patch("src.Tagesgericht.isdir")
    @patch("src.Tagesgericht.read_file", return_value={})
    def test_parse_year_dir(self, lread_file, isdir, listdir, join, parse_week_dir):
        year = Mock()
        year.endswith.side_effect = [True, False]
        listdir.return_value = ["something.json", "2021"]
        parse_week_dir.return_value = {42: {0: "someday, monday, on calendarweek 42"}}
        join.return_value = "/".join([self.data_dir, "2021"])
        isdir.return_value = True
        cwm = TagesgerichtManager(
            weekday_map=self.weekday_map,
            active_days=self.active_days,
            data_dir=self.data_dir,
            language="de",
            specialdays={}
        )
        result = cwm.parse_year_dir(path=self.data_dir)
        parse_week_dir.assert_called_once_with(path="unittest/2021", year_dict={}, year="2021")
        join.called_once_with("unittest", "2021")
        listdir.called_once_with("unittest")
        isdir.called_once_with("unittest/2021")
        self.assertEqual({"2021": {42: {0: "someday, monday, on calendarweek 42"}}}, result)
        lread_file.assert_called_once_with(path="translate_de.json", json=True)

    @patch("src.Tagesgericht.read_file", return_value={})
    def test_get_new_calendarweek_obj(self, lread_file):
        cwm = TagesgerichtManager(
            weekday_map=self.weekday_map,
            active_days=self.active_days,
            data_dir=self.data_dir,
            language="de",
            specialdays={}
        )
        result = cwm.get_new_calendarweek_obj(year="2021", week="42")
        self.assertEqual(Calendarweek(year="2021", week="42"), result)
        lread_file.assert_called_once_with(path="translate_de.json", json=True)

    @patch("src.Tagesgericht.TagesgerichtManager.get_new_calendarweek_obj")
    @patch("src.Tagesgericht.join")
    @patch("src.Tagesgericht.listdir")
    @patch("src.Tagesgericht.read_file", side_effect=[{}, {"4": ["logentry1", "logentry2"]}])
    @patch("src.Tagesgericht.isfile", return_value=True)
    def test_parse_week_dir(self, isfile, lread_file, listdir, join, get_new_calendarweek_obj):
        listdir.side_effect = [
            ["42"],
            ["log.json", "0_Montag.txt", "4_Freitag.txt"],
        ]
        join.return_value = "/".join([self.data_dir, "2021", "42"])
        cw_obj0 = Mock()
        cw_obj0.first_day_of_week = date(2021, 12, 13)
        day_mock = Mock()
        day_mock.specialday = ""
        cw_obj0.items = {
            0: day_mock
        }
        get_new_calendarweek_obj.side_effect = [cw_obj0, ]

        cwm = TagesgerichtManager(
            weekday_map=self.weekday_map,
            active_days=self.active_days,
            data_dir=self.data_dir,
            language="de",
            specialdays={"13.12": "unittestday"}
        )
        result = cwm.parse_week_dir(year="2021", year_dict={}, path=self.data_dir)

        cw_obj0.init_log_for_day.assert_called_once_with(log=["logentry1", "logentry2"], day_num=4)
        get_new_calendarweek_obj.assert_called_once_with(year="2021", week="42")
        listdir.assert_has_calls([
            call("unittest"),
            call("unittest/2021/42")
        ])
        lread_file.assert_has_calls([
            call(path="translate_de.json", json=True),
            call(path="unittest/2021/42.json", json=True)
        ])
        isfile.assert_called_once_with(path="unittest/2021/42.json")
        join.assert_has_calls([
            call("unittest", "42"),
            call("unittest", "42", "log"),
            call("unittest/2021/42", "0_Montag.txt"),
            call("unittest/2021/42", "4_Freitag.txt")
        ])
        self.assertEqual({"42": cw_obj0}, result)

    @patch("src.Tagesgericht.print")
    @patch("src.Tagesgericht.read_file", return_value={})
    def test_print_data(self, lread_file, lprint):
        cwm = TagesgerichtManager(
            weekday_map=self.weekday_map,
            active_days=self.active_days,
            data_dir=self.data_dir,
            language="de",
            specialdays={}
        )
        ci0 = Mock()
        ci0.message_length = 13
        ci0.message_length_exceeded = False
        ci0.filepath = "unittest/unit.txt"
        ci0.message_icon = "✅"
        ci0.get_error_text.return_value = ""
        ci0.has_been_sent.return_value = "Message has ben sent at 2021-06-13 12:30"
        ci0.specialday = ""
        ci1 = Mock()
        ci1.message_length = 0
        ci1.message_length_exceeded = False
        ci1.filepath = "unittest/unit.txt"
        ci1.message_icon = "❎"
        ci1.get_error_text.return_value = "message empty"
        ci1.has_been_sent.return_value = False
        ci1.specialday = ""
        ci2 = Mock()
        ci2.message_length = 300
        ci2.message_length_exceeded = True
        ci2.filepath = "unittest/unit.txt"
        ci2.message_icon = "❌️"
        ci2.get_error_text.return_value = "message too long"
        ci2.has_been_sent.return_value = False
        ci2.specialday = "Unittest tag"
        cw_obj = Mock()
        cw_obj.week = "42"
        cw_obj.first_day_of_week = date(2021, 12, 13)
        cw_obj.last_day_of_week = date(2021, 12, 19)
        cw_obj.week_icon = "❎️"
        cw_obj.items = {
            0: ci0,
            1: ci1,
            2: ci2,
        }
        cwm.data = {
            "2021": {
                "42": cw_obj,
            }
        }
        cwm.print_data()

        lprint.assert_has_calls([
            call("============================================\ncalendarweek 42 13.12.2021 - 19.12.2021 ❎️"),
            call("unittest/unit.txt", "✅", "", "Message has ben sent at 2021-06-13 12:30"),
            call("unittest/unit.txt", "❎", "", "message empty"),
            call("unittest/unit.txt", "❌️", "", "message too long")
        ])
        lread_file.assert_called_once_with(path="translate_de.json", json=True)

    @patch("src.Tagesgericht.read_file", return_value={})
    def test_get_rst_line_for_str(self, lread_file):
        cwm = TagesgerichtManager(
            weekday_map=self.weekday_map,
            active_days=self.active_days,
            data_dir=self.data_dir,
            language="de",
            specialdays={}
        )
        line = cwm.get_rst_line_for_str(string="123456789", linetype="*")
        self.assertEqual("**********", line)
        lread_file.assert_called_once_with(path="translate_de.json", json=True)

    @patch("src.Tagesgericht.read_file", return_value={})
    def test_get_formatted_rst_header(self, lread_file):
        cwm = TagesgerichtManager(
            weekday_map=self.weekday_map,
            active_days=self.active_days,
            data_dir=self.data_dir,
            language="de",
            specialdays={}
        )
        line = cwm.get_formatted_rst_header(message="123456789", linetype="*", doubled=False)
        self.assertEqual("123456789\n**********\n\n", line)
        line = cwm.get_formatted_rst_header(message="123456789", linetype="*", doubled=True)
        self.assertEqual("**********\n123456789\n**********\n\n", line)
        lread_file.assert_called_once_with(path="translate_de.json", json=True)

    @patch("src.Tagesgericht.read_file", return_value={})
    def test_get_formatted_rst_quote(self, lread_file):
        cwm = TagesgerichtManager(
            weekday_map=self.weekday_map,
            active_days=self.active_days,
            data_dir=self.data_dir,
            language="de",
            specialdays={}
        )
        line = cwm.get_formatted_rst_quote(message="123456789", quote="quote")
        self.assertEqual(":quote:\n\n    123456789\n\n", line)
        lread_file.assert_called_once_with(path="translate_de.json", json=True)

    @patch("src.Tagesgericht.read_file", return_value={})
    def test_return_week_as_rst_string(self, lread_file):
        cwm = TagesgerichtManager(
            weekday_map=self.weekday_map,
            active_days=self.active_days,
            data_dir=self.data_dir,
            language="de",
            specialdays={}
        )
        ci0 = Mock()
        ci0.message_length = 13
        ci0.message_length_exceeded = False
        ci0.filepath = "unittest/unit.txt"
        ci0.message = "message test unittest 1"
        ci0.specialday = ""
        ci0.has_been_sent.return_value = "Message has ben sent at 2021-06-13 12:30"
        ci0.has_been_stopped.return_value = "Message has ben stopped at 2021-06-13 13:30"
        ci0.message_icon = "✅"
        ci0.item_date = date(2021, 12, 13)
        ci1 = Mock()
        ci1.message_length = 0
        ci1.message_length_exceeded = False
        ci1.filepath = "unittest/unit.txt"
        ci1.message = ""
        ci1.specialday = ""
        ci1.has_been_sent.return_value = False
        ci1.has_been_stopped.return_value = False
        ci1.message_icon = "❎️"
        ci1.item_date = date(2021, 12, 14)
        ci2 = Mock()
        ci2.message_length = 300
        ci2.message_length_exceeded = True
        ci2.filepath = "unittest/unit.txt"
        ci2.message = "message test unittest 3"
        ci2.specialday = "Unittest tag"
        ci2.has_been_sent.return_value = False
        ci2.has_been_stopped.return_value = False
        ci2.message_icon = "❌️"
        ci2.item_date = date(2021, 12, 15)
        cw_obj = Mock()
        cw_obj.week = "49"
        cw_obj.first_day_of_week = date(2021, 12, 13)
        cw_obj.last_day_of_week = date(2021, 12, 19)
        cw_obj.week_icon = "❎️"
        cw_obj.items = {
            0: ci0,
            1: ci1,
            2: ci2,
        }
        line = cwm.return_week_as_rst_string(week=cw_obj)
        self.assertEqual("===================\ncalendarweek 49 ❎️\n===================\n\nMontag, 13.12.2021 ✅" +
                         "\n^^^^^^^^^^^^^^^^^^^^^\n\n" + ":Info:\n\n    Message has ben sent at 2021-06-13 12:30\n\n" +
                         ":Info:\n\n    Message has ben stopped at 2021-06-13 13:30\n\n" +
                         "::\n\n    message test unittest 1\n\n" +
                         "Dienstag, 14.12.2021 ❎️\n^^^^^^^^^^^^^^^^^^^^^^^^\n\n:Info:\n\n    message empty\n\n" +
                         "Mittwoch, 15.12.2021 ❌️\n^^^^^^^^^^^^^^^^^^^^^^^^\n\n" + ":Info:\n\n    Unittest tag\n\n" +
                         ":Error:\n\n    message too long\n\n" +
                         "::\n\n    message test unittest 3\n\n", line)
        lread_file.assert_called_once_with(path="translate_de.json", json=True)

    @patch("src.Tagesgericht.TagesgerichtManager.get_formatted_rst_header")
    @patch("src.Tagesgericht.TagesgerichtManager.get_formatted_rst_quote")
    @patch("src.Tagesgericht.read_file", return_value={})
    def test_get_report_legend_report(self, lread_file, get_formatted_rst_quote, get_formatted_rst_header):
        get_formatted_rst_header.return_value = "unittest_header\n"
        get_formatted_rst_quote.return_value = "unittest_quote"
        cwm = TagesgerichtManager(
            weekday_map=self.weekday_map,
            active_days=self.active_days,
            data_dir=self.data_dir,
            language="de",
            specialdays={}
        )
        line = cwm.get_report_legend(header="unittest", history=False)
        get_formatted_rst_header.assert_called_once_with(
            message="unittest",
            doubled=False,
            linetype="="
        )
        get_formatted_rst_quote.assert_called_once_with(
            quote="Legend",
            message=":✅: Planned message can be sent\n" +
                    ":❎: Planned message is empty\n" +
                    ":❌: Planned message cant be sent"
        )
        self.assertEqual("unittest_header\nunittest_quote", line)
        lread_file.assert_called_once_with(path="translate_de.json", json=True)

    @patch("src.Tagesgericht.TagesgerichtManager.get_formatted_rst_header")
    @patch("src.Tagesgericht.TagesgerichtManager.get_formatted_rst_quote")
    @patch("src.Tagesgericht.read_file", return_value={})
    def test_get_report_legend_history(self, lread_file, get_formatted_rst_quote, get_formatted_rst_header):
        get_formatted_rst_header.return_value = "unittest_header\n"
        get_formatted_rst_quote.return_value = "unittest_quote"
        cwm = TagesgerichtManager(
            weekday_map=self.weekday_map,
            active_days=self.active_days,
            data_dir=self.data_dir,
            language="de",
            specialdays={}
        )
        line = cwm.get_report_legend(header="unittest", history=True)
        get_formatted_rst_header.assert_called_once_with(
            message="unittest",
            doubled=False,
            linetype="="
        )
        get_formatted_rst_quote.assert_called_once_with(
            quote="Legend",
            message=":✅: Message was sent\n" +
                    ":❎: Message was not sent\n" +
                    ":❌: Message was not sent"
        )
        self.assertEqual("unittest_header\nunittest_quote", line)
        lread_file.assert_called_once_with(path="translate_de.json", json=True)

    @patch("src.Tagesgericht.remove_folder")
    @patch("src.Tagesgericht.create_folder")
    @patch("src.Tagesgericht.TagesgerichtManager.get_report_legend")
    @patch("src.Tagesgericht.write_file")
    @patch("src.Tagesgericht.TagesgerichtManager.return_week_as_rst_string")
    @patch("src.Tagesgericht.read_file", return_value={})
    def test_create_rst_data(self,
                             lread_file,
                             return_week_as_rst_string,
                             lwrite_file,
                             get_report_legend,
                             lcreate_folder,
                             lremove_folder
                             ):
        return_week_as_rst_string.return_value = "unittest_week_rst_string"
        get_report_legend.side_effect = ["unittest_planned", "unittest_history"]
        ci0 = Mock()
        ci0.message_length = 13
        ci0.message_length_exceeded = False
        ci0.filepath = "unittest/unit.txt"
        ci0.message = "message test unittest 1"
        ci0.message_icon = "✅"
        ci0.item_date = date(2021, 12, 6)
        ci1 = Mock()
        ci1.message_length = 0
        ci1.message_length_exceeded = False
        ci1.filepath = "unittest/unit.txt"
        ci1.message = ""
        ci1.message_icon = "❎️"
        ci1.item_date = date(2021, 12, 7)
        ci2 = Mock()
        ci2.message_length = 300
        ci2.message_length_exceeded = True
        ci2.filepath = "unittest/unit.txt"
        ci2.message = "message test unittest 3"
        ci2.message_icon = "❌️"
        ci2.item_date = date(2021, 12, 8)
        cw_obj = Mock()
        cw_obj.week = "49"
        cw_obj.first_day_of_week = date(2021, 12, 6)
        cw_obj.last_day_of_week = date(2021, 12, 12)
        cw_obj.week_icon = "❎"
        cw_obj.items = {
            0: ci0,
            1: ci1,
            2: ci2,
        }

        ci0_1 = Mock()
        ci0_1.message_length = 13
        ci0_1.message_length_exceeded = False
        ci0_1.filepath = "unittest/unit.txt"
        ci0_1.message = "message test unittest 1"
        ci0_1.message_icon = "✅"
        ci0_1.item_date = date(2021, 12, 13)
        ci1_1 = Mock()
        ci1_1.message_length = 0
        ci1_1.message_length_exceeded = False
        ci1_1.filepath = "unittest/unit.txt"
        ci1_1.message = ""
        ci1_1.message_icon = "❎️"
        ci1_1.item_date = date(2021, 12, 14)
        ci2_1 = Mock()
        ci2_1.message_length = 300
        ci2_1.message_length_exceeded = True
        ci2_1.filepath = "unittest/unit.txt"
        ci2_1.message = "message test unittest 3"
        ci2_1.message_icon = "❌️"
        ci2_1.item_date = date(2021, 12, 15)
        cw_obj1 = Mock()
        cw_obj1.week = "50"
        cw_obj1.first_day_of_week = date(2021, 12, 13)
        cw_obj1.last_day_of_week = date(2021, 12, 19)
        cw_obj1.week_icon = "❎️"
        cw_obj1.items = {
            0: ci0_1,
            1: ci1_1,
            2: ci2_1,
        }

        cwm = TagesgerichtManager(
            weekday_map=self.weekday_map,
            active_days=self.active_days,
            data_dir=self.data_dir,
            language="de",
            specialdays={}
        )
        cwm.report_build_folder = "unittest"
        cwm.data = {"2021": {"49": cw_obj, "50": cw_obj1}}
        cwm.year, cwm.month, cwm.day = 2021, 12, 13
        cwm.today = date(cwm.year, cwm.month, cwm.day)
        cwm.day_num = cwm.today.weekday()
        cwm.current_week = cwm.today.isocalendar()[1]

        cwm.create_rst_data()
        lwrite_file.assert_has_calls([
            call(
                path="unittest/planned_status.rst",
                data="unittest_plannedunittest_week_rst_string",
                json=False
            ),
            call(
                path="unittest/history.rst",
                data="unittest_historyunittest_week_rst_string",
                json=False
            )
        ])
        return_week_as_rst_string.assert_has_calls([
            call(week=cw_obj),
            call(week=cw_obj1)
        ])
        get_report_legend.assert_has_calls([
            call(header="Future & Active calendar weeks", history=False),
            call(header="Past calendar weeks", history=True)
        ])
        lcreate_folder.assert_called_once_with(dir_path="unittest")
        lremove_folder.assert_called_once_with(dir_path="unittest")
        lread_file.assert_called_once_with(path="translate_de.json", json=True)

    @patch("src.Tagesgericht.join", return_value="unittest/log.json")
    @patch("src.Tagesgericht.write_file")
    @patch("src.Tagesgericht.read_file", return_value={})
    def test_write_week_logfile(self, lread_file, lwrite_file, ljoin):
        day_0 = Mock()
        day_0.logentrys = ["unittest logentry"]
        day_1 = Mock()
        day_1.logentrys = []

        items = {
            "0": day_0,
            "1": day_1,
        }
        cwm = TagesgerichtManager(
            weekday_map=self.weekday_map,
            active_days=self.active_days,
            data_dir=self.data_dir,
            language="de",
            specialdays={}
        )

        cwm.year, cwm.month, cwm.day = 2021, 12, 13

        cwm.write_week_logfile(week="42", items=items)
        lwrite_file.assert_called_once_with(path="unittest/log.json", json=True, data={"0": ["unittest logentry"]})
        ljoin.assert_called_once_with("unittest", "2021", "42", "log.json")
        lread_file.assert_called_once_with(path="translate_de.json", json=True)

    @patch("src.Tagesgericht.TagesgerichtManager.get_today_from_calendarweek")
    @patch("src.Tagesgericht.TagesgerichtManager.init_manager")
    @patch("src.Tagesgericht.read_file", return_value={})
    @patch("src.Tagesgericht.TagesgerichtManager.get_current_week_obj")
    @patch("src.Tagesgericht.write_file")
    @patch("src.Tagesgericht.join", return_value="unittest/2021/6/log.json")
    def test_send_message_for_today(self, ljoin, lwrite_file, get_current_week_obj, lread_file, init_manager,
                                    get_today_from_calendarweek):
        today_obj = get_today_from_calendarweek.return_value
        today_obj.has_been_sent.return_value = False
        today_obj.message_sendable.return_value = True
        today_obj.week = "42"
        get_today_from_calendarweek.return_value = today_obj
        week_obj = get_current_week_obj.return_value

        week_obj.has_been_sent.return_value = False
        get_current_week_obj.return_value = today_obj

        cwm = TagesgerichtManager(
            weekday_map=self.weekday_map,
            active_days=self.active_days,
            data_dir=self.data_dir,
            language="de",
            specialdays={}
        )
        cwm.send_message_for_today()
        ljoin.assert_called_once_with("unittest", "2021", "42", "log.json")
        lwrite_file.assert_called_once_with(path="unittest/2021/6/log.json", json=True, data={})
        init_manager.assert_called_once_with()
        get_today_from_calendarweek.assert_called_once_with()
        lread_file.assert_called_once_with(path="translate_de.json", json=True)

    @patch("src.Tagesgericht.TagesgerichtManager.get_today_from_calendarweek")
    @patch("src.Tagesgericht.TagesgerichtManager.init_manager")
    @patch("src.Tagesgericht.read_file", return_value={})
    @patch("src.Tagesgericht.TagesgerichtManager.get_current_week_obj")
    @patch("src.Tagesgericht.write_file")
    @patch("src.Tagesgericht.join", return_value="unittest/2021/6/log.json")
    def test_send_message_for_today_not_sendable(self, ljoin, lwrite_file, get_current_week_obj, lread_file,
                                                 init_manager, get_today_from_calendarweek):
        today_obj = get_today_from_calendarweek.return_value
        today_obj.has_been_sent.return_value = False
        today_obj.message_sendable = False
        today_obj.week = "42"
        get_today_from_calendarweek.return_value = today_obj
        week_obj = get_current_week_obj.return_value

        week_obj.has_been_sent.return_value = False
        get_current_week_obj.return_value = today_obj

        cwm = TagesgerichtManager(
            weekday_map=self.weekday_map,
            active_days=self.active_days,
            data_dir=self.data_dir,
            language="de",
            specialdays={}
        )
        result = cwm.send_message_for_today()
        self.assertEqual(False, result)
        ljoin.assert_called_once_with("unittest", "2021", "42", "log.json")
        lwrite_file.assert_called_once_with(path="unittest/2021/6/log.json", json=True, data={})
        init_manager.assert_called_once_with()
        get_today_from_calendarweek.assert_called_once_with()
        lread_file.assert_called_once_with(path="translate_de.json", json=True)

    @patch("src.Tagesgericht.TagesgerichtManager.get_today_from_calendarweek")
    @patch("src.Tagesgericht.TagesgerichtManager.init_manager")
    @patch("src.Tagesgericht.read_file", return_value={})
    @patch("src.Tagesgericht.TagesgerichtManager.get_current_week_obj")
    @patch("src.Tagesgericht.write_file")
    @patch("src.Tagesgericht.join", return_value="unittest/2021/6/log.json")
    def test_send_message_for_today_has_been_sent(self, ljoin, lwrite_file, get_current_week_obj, lread_file,
                                                  init_manager, get_today_from_calendarweek):
        today_obj = get_today_from_calendarweek.return_value
        today_obj.has_been_sent.return_value = True
        today_obj.message_sendable = False
        today_obj.week = "42"
        get_today_from_calendarweek.return_value = today_obj
        week_obj = get_current_week_obj.return_value

        week_obj.has_been_sent.return_value = False
        get_current_week_obj.return_value = today_obj

        cwm = TagesgerichtManager(
            weekday_map=self.weekday_map,
            active_days=self.active_days,
            data_dir=self.data_dir,
            language="de",
            specialdays={}
        )
        result = cwm.send_message_for_today()
        self.assertEqual(False, result)
        ljoin.assert_not_called()
        lwrite_file.assert_not_called()
        init_manager.assert_called_once_with()
        get_today_from_calendarweek.assert_called_once_with()
        lread_file.assert_called_once_with(path="translate_de.json", json=True)

    @patch("src.Tagesgericht.TagesgerichtManager.get_today_from_calendarweek")
    @patch("src.Tagesgericht.TagesgerichtManager.init_manager")
    @patch("src.Tagesgericht.read_file", return_value={})
    @patch("src.Tagesgericht.write_file")
    @patch("src.Tagesgericht.join", return_value="unittest/2021/6/log.json")
    def test_send_message_for_today_no_obj(self, ljoin, lwrite_file, lread_file, init_manager,
                                           get_today_from_calendarweek):
        get_today_from_calendarweek.return_value = None

        cwm = TagesgerichtManager(
            weekday_map=self.weekday_map,
            active_days=self.active_days,
            data_dir=self.data_dir,
            language="de",
            specialdays={}
        )
        result = cwm.send_message_for_today()
        self.assertEqual(False, result)
        ljoin.assert_not_called()
        lwrite_file.assert_not_called()
        init_manager.assert_called_once_with()
        get_today_from_calendarweek.assert_called_once_with()
        lread_file.assert_called_once_with(path="translate_de.json", json=True)

    @patch("src.Tagesgericht.read_file", return_value={})
    @patch("src.Tagesgericht.TagesgerichtManager.init_manager", return_value={})
    @patch("src.Tagesgericht.TagesgerichtManager.get_current_week_obj")
    def test_get_today_from_calendarweek(self, get_current_week_obj, init_manager, lread_file):
        cwm = TagesgerichtManager(
            weekday_map=self.weekday_map,
            active_days=self.active_days,
            data_dir=self.data_dir,
            language="de",
            specialdays={}
        )
        cwm.year = 2021
        cwm.current_week = 42
        cwm.day_num = 0
        cw_obj = Mock()
        cw_obj.items = {
            0: "unittest"
        }
        get_current_week_obj.return_value = cw_obj
        cwm.data = {
            "2021": {
                "42": cw_obj
            }
        }
        result = cwm.get_today_from_calendarweek()
        init_manager.assert_has_calls([""])
        get_current_week_obj.assert_has_calls([""])
        lread_file.assert_called_once_with(path="translate_de.json", json=True)
        self.assertEqual("unittest", result)

    @patch("src.Tagesgericht.read_file", return_value={})
    def test_get_current_week_obj(self, lread_file):
        cwm = TagesgerichtManager(
            weekday_map=self.weekday_map,
            active_days=self.active_days,
            data_dir=self.data_dir,
            language="de",
            specialdays={}
        )
        cwm.year = 2021
        cwm.current_week = 42
        cwm.day_num = 0
        cw_obj = Mock()
        cwm.data = {
            "2021": {
                "42": cw_obj
            }
        }
        result = cwm.get_current_week_obj()
        lread_file.assert_called_once_with(path="translate_de.json", json=True)
        self.assertEqual(cw_obj, result)

    @patch("src.Tagesgericht.read_file", return_value={})
    @patch("src.Tagesgericht.TagesgerichtManager.get_today_from_calendarweek")
    def test_show_send_message_all_false(self, get_today_from_calendarweek, lread_file):
        current_day_obj_mock = Mock()
        current_day_obj_mock.has_been_sent.return_value = False
        current_day_obj_mock.has_been_stopped.return_value = False
        current_day_obj_mock.message_sendable = False
        get_today_from_calendarweek.return_value = current_day_obj_mock

        cwm = TagesgerichtManager(
            weekday_map=self.weekday_map,
            active_days=self.active_days,
            data_dir=self.data_dir,
            language="de",
            specialdays={}
        )
        result = cwm.show_send_message()
        current_day_obj_mock.has_been_sent.assert_called_once_with(translate={})
        get_today_from_calendarweek.assert_called_once_with()
        lread_file.assert_called_once_with(path="translate_de.json", json=True)
        self.assertFalse(result)

    @patch("src.Tagesgericht.read_file", return_value={})
    @patch("src.Tagesgericht.TagesgerichtManager.get_today_from_calendarweek")
    def test_show_send_message_sendable(self, get_today_from_calendarweek, lread_file):
        current_day_obj_mock = Mock()
        current_day_obj_mock.has_been_sent.return_value = False
        current_day_obj_mock.has_been_stopped.return_value = False
        current_day_obj_mock.message_sendable = True
        get_today_from_calendarweek.return_value = current_day_obj_mock

        cwm = TagesgerichtManager(
            weekday_map=self.weekday_map,
            active_days=self.active_days,
            data_dir=self.data_dir,
            language="de",
            specialdays={}
        )
        result = cwm.show_send_message()
        current_day_obj_mock.has_been_sent.assert_called_once_with(translate={})
        get_today_from_calendarweek.assert_called_once_with()
        lread_file.assert_called_once_with(path="translate_de.json", json=True)
        self.assertTrue(result)

    @patch("src.Tagesgericht.read_file", return_value={})
    @patch("src.Tagesgericht.TagesgerichtManager.get_today_from_calendarweek")
    def test_show_send_message_already_sent(self, get_today_from_calendarweek, lread_file):
        current_day_obj_mock = Mock()
        current_day_obj_mock.has_been_sent.return_value = True
        current_day_obj_mock.has_been_stopped.return_value = False
        current_day_obj_mock.message_sendable = True
        get_today_from_calendarweek.return_value = current_day_obj_mock

        cwm = TagesgerichtManager(
            weekday_map=self.weekday_map,
            active_days=self.active_days,
            data_dir=self.data_dir,
            language="de",
            specialdays={}
        )
        result = cwm.show_send_message()
        current_day_obj_mock.has_been_sent.assert_called_once_with(translate={})
        get_today_from_calendarweek.assert_called_once_with()
        lread_file.assert_called_once_with(path="translate_de.json", json=True)
        self.assertFalse(result)

    @patch("src.Tagesgericht.read_file", return_value={})
    @patch("src.Tagesgericht.TagesgerichtManager.get_today_from_calendarweek")
    def test_show_send_message_already_has_bee_stopped(self, get_today_from_calendarweek, lread_file):
        current_day_obj_mock = Mock()
        current_day_obj_mock.has_been_sent.return_value = True
        current_day_obj_mock.has_been_stopped.return_value = True
        current_day_obj_mock.message_sendable = True
        get_today_from_calendarweek.return_value = current_day_obj_mock

        cwm = TagesgerichtManager(
            weekday_map=self.weekday_map,
            active_days=self.active_days,
            data_dir=self.data_dir,
            language="de",
            specialdays={}
        )
        result = cwm.show_send_message()
        current_day_obj_mock.has_been_sent.assert_called_once_with(translate={})
        get_today_from_calendarweek.assert_called_once_with()
        lread_file.assert_called_once_with(path="translate_de.json", json=True)
        self.assertFalse(result)

    @patch("src.Tagesgericht.read_file", return_value={})
    @patch("src.Tagesgericht.TagesgerichtManager.get_today_from_calendarweek")
    def test_show_sold_out_message_all_false(self, get_today_from_calendarweek, lread_file):
        current_day_obj_mock = Mock()
        current_day_obj_mock.has_been_sent.return_value = False
        current_day_obj_mock.has_been_stopped.return_value = False
        get_today_from_calendarweek.return_value = current_day_obj_mock

        cwm = TagesgerichtManager(
            weekday_map=self.weekday_map,
            active_days=self.active_days,
            data_dir=self.data_dir,
            language="de",
            specialdays={}
        )
        result = cwm.show_sold_out_message()
        current_day_obj_mock.has_been_sent.assert_called_once_with(translate={})
        get_today_from_calendarweek.assert_called_once_with()
        lread_file.assert_called_once_with(path="translate_de.json", json=True)
        self.assertFalse(result)

    @patch("src.Tagesgericht.read_file", return_value={})
    @patch("src.Tagesgericht.TagesgerichtManager.get_today_from_calendarweek")
    def test_show_sold_out_message_show(self, get_today_from_calendarweek, lread_file):
        current_day_obj_mock = Mock()
        current_day_obj_mock.has_been_sent.return_value = True
        current_day_obj_mock.has_been_stopped.return_value = False
        get_today_from_calendarweek.return_value = current_day_obj_mock

        cwm = TagesgerichtManager(
            weekday_map=self.weekday_map,
            active_days=self.active_days,
            data_dir=self.data_dir,
            language="de",
            specialdays={}
        )
        result = cwm.show_sold_out_message()
        current_day_obj_mock.has_been_sent.assert_called_once_with(translate={})
        get_today_from_calendarweek.assert_called_once_with()
        lread_file.assert_called_once_with(path="translate_de.json", json=True)
        self.assertTrue(result)

    @patch("src.Tagesgericht.read_file", return_value={})
    @patch("src.Tagesgericht.TagesgerichtManager.get_today_from_calendarweek")
    def test_show_sold_out_message_already_stopped(self, get_today_from_calendarweek, lread_file):
        current_day_obj_mock = Mock()
        current_day_obj_mock.has_been_sent.return_value = True
        current_day_obj_mock.has_been_stopped.return_value = True
        get_today_from_calendarweek.return_value = current_day_obj_mock

        cwm = TagesgerichtManager(
            weekday_map=self.weekday_map,
            active_days=self.active_days,
            data_dir=self.data_dir,
            language="de",
            specialdays={}
        )
        result = cwm.show_sold_out_message()
        current_day_obj_mock.has_been_sent.assert_called_once_with(translate={})
        get_today_from_calendarweek.assert_called_once_with()
        lread_file.assert_called_once_with(path="translate_de.json", json=True)
        self.assertFalse(result)

    @patch("src.Tagesgericht.read_file", return_value={})
    @patch("src.Tagesgericht.TagesgerichtManager.init_manager")
    @patch("src.Tagesgericht.TagesgerichtManager.get_current_week_obj")
    @patch("src.Tagesgericht.TagesgerichtManager.write_week_logfile")
    @patch("src.Tagesgericht.TagesgerichtManager.get_today_from_calendarweek")
    def test_send_sold_out_message(self, get_today_from_calendarweek, write_week_logfile, get_current_week_obj,
                                   init_manager, lread_file):
        current_week_obj_mock = Mock()
        mock_day = Mock()
        mock_day.has_been_sent.return_value = True
        mock_day.has_been_stopped.return_value = False
        current_week_obj_mock.items = {
            0: mock_day
        }
        get_today_from_calendarweek.return_value = mock_day
        current_week_obj_mock.has_been_stopped.return_value = True
        current_week_obj_mock.week = "42"
        get_current_week_obj.return_value = current_week_obj_mock

        cwm = TagesgerichtManager(
            weekday_map=self.weekday_map,
            active_days=self.active_days,
            data_dir=self.data_dir,
            language="de",
            specialdays={}
        )
        cwm.day_num = 0
        cwm.current_week = "42"
        result = cwm.send_sold_out_message()
        write_week_logfile.assert_called_once_with(
            week=current_week_obj_mock.week,
            items=current_week_obj_mock.items
        )
        mock_day.add_log.assert_called_once_with(message_sent=True, message_stopped=True, translate={})
        get_current_week_obj.assert_called_once_with()
        get_today_from_calendarweek.assert_called_once_with()
        init_manager.assert_called_once_with()
        lread_file.assert_called_once_with(path="translate_de.json", json=True)
        self.assertTrue(result)

    @patch("src.Tagesgericht.read_file", return_value={})
    @patch("src.Tagesgericht.TagesgerichtManager.init_manager")
    @patch("src.Tagesgericht.TagesgerichtManager.get_current_week_obj")
    @patch("src.Tagesgericht.TagesgerichtManager.write_week_logfile")
    @patch("src.Tagesgericht.TagesgerichtManager.get_today_from_calendarweek")
    def test_send_sold_out_message_not_sent_yet(self, get_today_from_calendarweek, write_week_logfile,
                                                get_current_week_obj, init_manager, lread_file):
        current_week_obj_mock = Mock()
        mock_day = Mock()
        mock_day.has_been_sent.return_value = False
        mock_day.has_been_stopped.return_value = False
        current_week_obj_mock.items = {
            0: mock_day
        }
        get_today_from_calendarweek.return_value = mock_day
        current_week_obj_mock.has_been_stopped.return_value = True
        current_week_obj_mock.week = "42"
        get_current_week_obj.return_value = current_week_obj_mock

        cwm = TagesgerichtManager(
            weekday_map=self.weekday_map,
            active_days=self.active_days,
            data_dir=self.data_dir,
            language="de",
            specialdays={}
        )
        cwm.day_num = 0
        cwm.current_week = "42"
        result = cwm.send_sold_out_message()
        write_week_logfile.assert_not_called()
        mock_day.add_log.assert_not_called()
        get_current_week_obj.assert_not_called()
        get_today_from_calendarweek.assert_called_once_with()
        init_manager.assert_called_once_with()
        lread_file.assert_called_once_with(path="translate_de.json", json=True)
        self.assertFalse(result)

    @patch("src.Tagesgericht.read_file", return_value={})
    @patch("src.Tagesgericht.TagesgerichtManager.init_manager")
    @patch("src.Tagesgericht.TagesgerichtManager.get_current_week_obj")
    @patch("src.Tagesgericht.TagesgerichtManager.write_week_logfile")
    @patch("src.Tagesgericht.TagesgerichtManager.get_today_from_calendarweek")
    def test_send_sold_out_message_already_sent(self, get_today_from_calendarweek, write_week_logfile,
                                                get_current_week_obj, init_manager, lread_file):
        current_week_obj_mock = Mock()
        mock_day = Mock()
        mock_day.has_been_sent.return_value = True
        mock_day.has_been_stopped.return_value = True
        current_week_obj_mock.items = {
            0: mock_day
        }
        get_today_from_calendarweek.return_value = mock_day
        current_week_obj_mock.has_been_stopped.return_value = True
        current_week_obj_mock.week = "42"
        get_current_week_obj.return_value = current_week_obj_mock

        cwm = TagesgerichtManager(
            weekday_map=self.weekday_map,
            active_days=self.active_days,
            data_dir=self.data_dir,
            language="de",
            specialdays={}
        )
        cwm.day_num = 0
        cwm.current_week = "42"
        result = cwm.send_sold_out_message()
        write_week_logfile.assert_not_called()
        mock_day.add_log.assert_not_called()
        get_current_week_obj.assert_not_called()
        get_today_from_calendarweek.assert_called_once_with()
        init_manager.assert_called_once_with()
        lread_file.assert_called_once_with(path="translate_de.json", json=True)
        self.assertFalse(result)
