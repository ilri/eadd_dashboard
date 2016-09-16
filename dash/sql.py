import MySQLdb

class Dbase():
    def __init__(self, host, user, password, database):
        self.error = None
        self.passwd  = password
        self.db   = database
        self.host = host
        self.user  = user
        self.curQuery = ''

    def query(self):
        """
        Initialize a connection to the database and execute any query that needs execution
        """
        try:
            connection = MySQLdb.connect(user = self.user,  passwd = self.passwd, host = self.host, db = self.db)
            db = connection.cursor()
        except:
            print('Exception: Could not connect to Database')
            raise

        #now lets execute the passed query
        #print query
        try:
            db.execute(self.curQuery)
            self.lastInsertId = connection.insert_id()
            connection.commit()
            #get all the data as a dictionary
            return db.fetchall()

        except:
            print('Exception: Malformed Query "%s"' % query)
            raise

    def dictQuery(self):
        """
        Returns a dictionary as the results instead of a tuple
        """
        try:
            connection = MySQLdb.connect(user = self.user,  passwd = self.passwd, host = self.host, db = self.db)
            db = connection.cursor(MySQLdb.cursors.DictCursor)
        except:
            print('Exception: Could not connect to Database')
            raise
        #print query
        try:
            db.execute(self.curQuery)
            #get all the data as a dictionary
            return db.fetchall()

        except:
            print('Exception: Malformed Query "%s"' % query)
            raise