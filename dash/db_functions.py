

class Dbase():
    def fetchAssoc(cursor):
        """
        Creates a dict from fetched results
        """
        data = cursor.fetchone()
        if data is None:
            return -1
        desc = cursor.description

        dict = {}

        for (name, value) in zip(desc, data):
            dict[name[0]] = value

        return dict

    def executeQuery(cursor, query):
        """
        Executes a query
        """
        cursor.execute(query)