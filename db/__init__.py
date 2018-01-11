import sys
import pymysql
import logging.config
sys.path.append('..')
from utils.Row import Row

logging.config.fileConfig("../conf/logging.conf")


class db(object):

    def __init__(self, db_name):
        pass


class Connection(object):
#    def __init__(self, *, charset='utf8', db_name=None, **kwargs):

    def __init__(self, host='', user='', passwd='', db='', port=3306, charset='utf8', **kwargs):
 
        args = dict(host=host, user=user, password=passwd,
                    db=db, port=port, charset=charset)
        args.update(kwargs)

        self._host = host
        self._db = None
        self._db_args = args
        try:
            self.reconnect()
        except:
            logging.error("Cannot connect to MySQL on {}".format(
                self._host), exc_info=True)

    def __del__(self):
        self.close()

    def reconnect(self):
        self.close()
        self._db = pymysql.connect(**self._db_args)
        self._db.autocommit(False)

    def close(self):
        if self._db is not None:
            self._db.close()
            self._db = None

    def rollback(self):
        if self._db is not None:
            try:
                self._db.rollback()
            except Exception as e:
                logging.error("Can not rollback .{}".format(str(e)))

    def commit(self):
        if self._db is not None:
            try:
                self._db.commit()
            except Exception as e:
                self._db.rollback()
                logging.error("Can not commit .{}".format(str(e)))

    def _cursor(self):
        if self._db is None:
            self.reconnect()
        try:
            self._db.ping()
        except:
            self.reconnect()
        return self._db.cursor()

    def _execute(self, cursor, query, parameters):
        try:
            return cursor.execute(query, parameters)
        except pymysql.OperationalError:
            logging.error("Error execute on {}".format(self._host))
            self.close()
            raise

    def _executemany(self, cursor, query, parameters):
        try:
            return cursor.executemany(query, parameters)
        except pymysql.OperationalError:
            logging.error("Error executemany on {}".format(self._host))
            self.close()
            raise

    def query(self, query, *parameters):

        cursor = self._cursor()
        try:
            self._execute(cursor, query, parameters)
            column_names = [d[0] for d in cursor.description]
            return [Row(zip(column_names, row)) for row in cursor]
        finally:
            cursor.close()

    def execute(self, query, *parameters):
        cursor = self._cursor()
        try:
            ret = self._execute(cursor, query, parameters)
            try:
                self.commit()
            except Exception as e:
                self.rollback()
                raise Exception(e)
            return ret
        finally:
            cursor.close()

    def get(self, query, *parameters):
        cursor = self._cursor()
        try:
            self._execute(cursor, query, parameters)
            #print(cursor._executed)
            column_names = [d[0] for d in cursor.description]
            result = cursor.fetchone()
            if not result:
                return None
            return Row(zip(column_names, result))
        finally:
            cursor.close()

    def iter(self, query, *parameters):
        if self._db is None:
            self.reconnect()

        cursor = pymysql.cursors.SSCursor(self._db)
        try:
            self._execute(cursor, query, parameters)
            column_names = [d[0] for d in cursor.description]
            for row in cursor:
                yield Row(zip(column_names, row))
        finally:
            cursor.close()

    def update(self, query, *parameters):
        cursor = self._cursor()
        try:
            self._execute(cursor, query, parameters)
            ret = cursor.rowcount
            try:
                self.commit()
            except Exception as e:
                self.rollback()
                raise Exception(e)
            return ret

        finally:
            cursor.close()

    def update_safe(self, table_name, condition="", **kwargs):
        column, value = zip(*kwargs.items())
        if condition:
            condition='where %s' % condition
        query = "update {table_name} set {fields} {condition}".format(
            table_name=table_name,
            fields=",".join(['`%s`' % key + '=%({})s'.format(key) for key in column]),
            condition=condition)

        #print(query)

        cursor=self._cursor()
        try:
            # print(value)
            self._execute(cursor, query, kwargs)
            ret=cursor.rowcount
            try:
                self.commit()
            except Exception as e:
                self.rollback()
                raise Exception(e)
            return ret
        finally:
            cursor.close()


    def count(self, query, *parameters):
        cursor=self._cursor()
        try:
            self._execute(cursor, query, parameters)
            return cursor.fetchone()[0]
        finally:
            cursor.close()

    def insert(self, table_name, **kwargs):
        column, value=zip(*kwargs.items())
        query="INSERT INTO {table_name}({column}) values({value})".format(table_name = table_name,
                                                                            column = ','.join(
                                                                                ['`{}`'.format(x) for x in column]),
                                                                            value = ','.join('%s' for _ in value))
        # print(query)
        cursor=self._cursor()
        try:
            # print(value)
            self._execute(cursor, query, value)
            ret=cursor.rowcount
            try:
                self.commit()
            except Exception as e:
                self.rollback()
                raise Exception(e)
            return ret
        finally:
            cursor.close()

    def insert_bulk(self, table_name, parameters):
        if 0 == len(parameters):
            print("err: insert_bult 's parameters is None")
            return None
        args=[]
        values=[]
        for parameter in parameters:
            column, value=zip(*parameter.items())
            args.append(value)

        query="INSERT INTO {table_name}({column}) values({value})".format(table_name = table_name,
                                                                            column = ','.join(
                                                                                ['`{}`'.format(x) for x in column]),
                                                                            value = ','.join('%s' for _ in value))
        cursor=self._cursor()
        try:
            self._executemany(cursor, query, args)
            ret=cursor.rowcount
            try:
                self.commit()
            except Exception as e:
                self.rollback()
                raise Exception(e)
            return ret
        finally:
            cursor.close()

    def __test_bulk(self):
        data=[('2016-11-02', 'stark3', '18'), ('2016-11-02',
               'stark3', '18'), ('2016-11-02', 'stark3', '18')]
        cursor=self._cursor()
        stmt="INSERT INTO test_db(`birth`,`name`,`age`) VALUES (%s, %s, %s)"
        cursor.executemany(stmt, data)
        self.commit()
