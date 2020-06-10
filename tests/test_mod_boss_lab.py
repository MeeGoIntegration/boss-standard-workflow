import os, unittest

from boss.lab import Lab

class TestLab(unittest.TestCase):
    def setUp(self):
        self.lab = Lab()

    def tearDown(self):
        self.lab.cleanup()

    def test_snapshot_and_cleanup(self):
        snap = self.lab.take_snapshot()
        self.assertEqual(len(self.lab._history), 2)
        for path in self.lab._history:
            self.assertTrue(os.path.exists(path))
        self.lab.real_path("test", snap)
        self.assertRaises(ValueError, self.lab.real_path, "test", 5)

    def test_store(self):
        self.lab.store("test", "testing")
        self.assertTrue(os.path.exists(self.lab.real_path("test")))
        self.assertEqual(self.lab.open("test").read(), "testing")

    def test_get_diff(self):
        self.lab.store("test", "testing")
        self.assertRaises(ValueError, self.lab.get_diff, "test", 5)
        self.assertRaises(ValueError, self.lab.get_diff, "test", 0, 3)
        self.assertEqual(len(self.lab.get_diff("test", 0, 0)), 0)
        snap = self.lab.take_snapshot()
        self.assertEqual(len(self.lab.get_diff("test", snap)), 0)

        self.lab.open("test", "w").write("newstuff")
        self.assertEqual(len(self.lab.get_diff("test", snap)), 2)

        self.lab.store("newfile", "newcontent")
        self.assertEqual(len(self.lab.get_diff("newfile", snap)), 1)

        os.remove(self.lab.real_path("test"))
        self.assertEqual(len(self.lab.get_diff("test", snap)), 1)

    def test_dir_creation(self):
        self.assertFalse(os.path.isdir(self.lab.real_path("test")))
        self.lab.mkdir("test")
        self.assertTrue(os.path.isdir(self.lab.real_path("test")))

        self.assertFalse(os.path.isdir(self.lab.real_path("foo/bar")))
        self.lab.makedirs("foo/bar")
        self.assertTrue(os.path.isdir(self.lab.real_path("foo/bar")))

    def test_open(self):
        self.lab.open(name="test", mode="w").write("testing")
        self.assertEqual(self.lab.open("test").read(), "testing")

        sid = self.lab.take_snapshot()
        self.assertEqual(self.lab.open("test", sid=sid).read(), "testing")
        self.assertRaises(ValueError, self.lab.open, "foo", "w", sid=sid)
        self.assertRaises(ValueError, self.lab.open, "test", "a", sid=sid)

    def test_bad_path(self):
        self.assertRaises(ValueError, self.lab.open, "../foo", "w")
        self.assertRaises(ValueError, self.lab.open, "/../foo", "w")
        self.assertRaises(ValueError, self.lab.mkdir, "../foo")
        self.assertRaises(ValueError, self.lab.makedirs, "foo/../bar")


    def test_context(self):
        class MyException(Exception):
            pass
        path = None
        try:
            with self.lab:
                path = self.lab.path
                raise MyException()
        except MyException:
            self.assertFalse(os.path.exists(path))

if __name__ == '__main__':
    unittest.main()
