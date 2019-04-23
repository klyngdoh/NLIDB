import pymysql.cursors

# Connect to the database
connection = pymysql.connect(host='localhost',
                             user='root',
                             password='',
                             db='NLIDB',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)

if __name__ == '__main__':
    try:

        with connection.cursor() as cursor:
            # Read a single record
            sql = "SELECT * FROM `orders` WHERE `customer_name`=%s"
            cursor.execute(sql, ('KD',))
            results = cursor.fetchall()
            for result in results:
                print(result)
    finally:
        connection.close()