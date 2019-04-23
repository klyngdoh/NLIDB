import pymysql.cursors

# Connect to the database
connection = pymysql.connect(host='localhost',
                             user='root',
                             password='',
                             db='nlp',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)


def fetchOneResult(query, params):
    try:
        with connection.cursor() as cursor:
            # Read a single record
            sql = query
            cursor.execute(sql, params)
            result = cursor.fetchone()
            return result
    except:
        print("An exception occured")


def fetchUserRecord():
    customer_email = input("Please enter your email: ")
    user_record = fetchOneResult("Select * from `orders` where `customer_email`=%s", (customer_email,))

    while user_record is None:
        print("User record not found!")
        customer_email = input("Please enter correct email: ")

        user_record = fetchOneResult("Select * from `orders` where `customer_email`=%s", (customer_email,))

    print("Welcome", user_record['customer_first'])
    return user_record


if __name__ == '__main__':

    print("Welcome to NLIDB!")

    user_record = fetchUserRecord()

    query = input("Enter your query: ")
    while query != "exit":
        print("Processing query", query)

        if query == "switch user":
            fetchUserRecord()

        if query == "help":
            print("The following commands are supported: ")
            print("\t\"switch user\" to switch users")
            print("\t\"exit\" to exit NLIDB")

        query = input("Enter your query: ")
