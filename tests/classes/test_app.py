import unittest
from PQEnalyzer.classes import App
from PQEnalyzer.classes import Reader
from PQAnalysis.traj.formats import MDEngineFormat

class TestApp(unittest.TestCase):

    def test__init__(self):
        file = "tests/data/md-01.en"
        reader = Reader([file], MDEngineFormat.PIMD_QMCF)
        app = App(reader)
        self.assertEqual(app.title(), "PQEnalyzer - MolarVerse")
        self.assertEqual(app.reader, reader)
    
