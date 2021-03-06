# coding: utf8
""" 单元测试
"""
# coding: utf8
# before run this test you must create database first
# run: create database test default character set utf8  # in mysql-client

import unittest
from torndb import Connection
from tornorm import Base, set_


_CONNS_ = {}


def get_conn(db_name, pre_sqls=None):
    if db_name in _CONNS_:
        return _CONNS_[db_name]
    pre_sqls = pre_sqls or []
    _CONNS_[db_name] = db = Connection(host='localhost', database=db_name, user='root', password='toor')
    db._db_args.pop('init_command', None)
    db.execute("set TIME_ZONE = 'SYSTEM'")
    for sql in pre_sqls:
        db.execute(sql)
    return db


class TestOrm(Base):

    _table_name = 'test_orm'
    _rows = [
        'id', 'name', 'content', 'type'
    ]
    _per_page = 10

    @classmethod
    def get_conn(cls):
        return get_conn('test', pre_sqls=('set names utf8mb4', ))


class OrmTest(unittest.TestCase):

    def setUp(self):
        # 建立数据库表
        self.conn = get_conn('test')
        self.conn.execute("DROP TABLE IF EXISTS `test_orm`; CREATE TABLE `test_orm` (`id` int NOT NULL AUTO_INCREMENT,"
                          "name varchar(128),content varchar(64),`type` tinyint(2) DEFAULT 1,"
                          "PRIMARY KEY (`id`)) ENGINE=InnoDB DEFAULT CHARSET=utf8;")

    def test_new(self):
        t = TestOrm.new(name='test1', content='test', type=1)
        o = self.conn.get('select * from test_orm where name="test1"')
        self.assertTrue(t)
        self.assertEqual(t.id, o.id)

    def test_get(self):
        self._init_data()
        t = TestOrm.get(name='test0')
        self.assertTrue(t)
        self.assertEqual(t.type, 0)

    def test_exists(self):
        self._init_data()
        e = TestOrm.exists(name='test0')
        self.assertEqual(e, True)

    def test_find(self):
        # 插入三条数据
        for i in range(3):
            self._init_data()
        rs = TestOrm.find(name='test0')
        self.assertTrue(rs)
        self.assertEqual(len(rs), 3)

    def test_new_mul(self):
        data = [dict(name='test%s' % i, content='test%s' % i) for i in range(5)]
        # print '(****ddata: ', data
        rs = TestOrm.new_mul(True, *data)
        # sql, value = TestOrm.new_mul(False, *data)
        # print '***sql: ', sql
        # print '***values: ', value
        self.assertTrue(rs)
        # 此时数据库有五条数据
        rs = self.conn.query('select * from test_orm')
        # print '***rs: ', rs
        self.assertEqual(len(rs), 5)

    def test_page(self):
        # 插入十条数据
        for i in range(10):
            self._init_data()
        rs1 = TestOrm.page(page=1, per_page=6)
        self.assertEqual(len(rs1), 6)
        rs2 = TestOrm.page(page=2, per_page=6)
        self.assertEqual(len(rs2), 4)

    def test_delete(self):
        self._init_data()
        d = TestOrm.delete(name='test0')
        self.assertTrue(d)
        # 此时 表是空的
        c = self.conn.query('select * from test_orm')
        self.assertFalse(c)

    def test_cls_update(self):
        self._init_data()
        cu = TestOrm.cls_update(set_(name='test1'), name='test0')
        self.assertTrue(cu)
        r1 = self.conn.query('select * from test_orm where name="test0"')
        self.assertFalse(r1)
        r2 = self.conn.query('select * from test_orm where name="test1"')
        self.assertTrue(r2)

    def test_transaction(self):
        self._init_data()
        try:
            TestOrm.begin()
            sql, value = TestOrm.cls_update(commit=False, sets=set_(name="test1"), name="test0")
            TestOrm.execute_sql(sql, value, mode='execute')
            # raise Exception('rollback')
            TestOrm.commit()
            r = self.conn.query('select * from test_orm where name="test0"')
            self.assertFalse(r)
        except Exception as ex:
            print 'ex: ', ex
            TestOrm.rollback()
        r = self.conn.query('select * from test_orm where name="test1"')
        self.assertTrue(r)

    def test_update(self):
        self._init_data()
        o = TestOrm.get(name='test0')
        self.assertTrue(o)
        o = o.update(name='test1')
        self.assertEqual(o.name, 'test1')
        r2 = self.conn.query('select * from test_orm where name="test1"')
        self.assertTrue(r2)
        o.name = 'test2'
        o = o.save()
        self.assertEqual(o.name, 'test2')
        r2 = self.conn.query('select * from test_orm where name="test2"')
        self.assertTrue(r2)

    def _empty_table(self):
        self.conn.execute("delete from test_orm")

    def _init_data(self, name='test0', content='test', _type=0):
        self.conn.execute("insert into test_orm (name, content, type)values (%s, %s, %s)", name, content, _type)

    def tearDown(self):
        self._empty_table()
        # self.conn.execute("DROP TABEL test_orm")


if __name__ == '__main__':
    unittest.main()


