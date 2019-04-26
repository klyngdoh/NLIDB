import pymysql.cursors
import nltk
from nltk.corpus import wordnet
import datetime

# Connect to the database
connection = pymysql.connect(host='localhost',
                             user='root',
                             password='admin',
                             db='nlp',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)


def get_synonyms(word, pos):
    synonyms = []
    for syn in wordnet.synsets(word):
        if ("." + pos + ".") in syn.name():
            for l in syn.lemmas():
                synonyms.append(l.name().replace('_', ' '))
    return list(set(synonyms))


def get_select(text):
    ps = nltk.PorterStemmer()
    words = text.lower().split()
    stemmed_words = [ps.stem(word) for word in words]
    pos_tags = nltk.pos_tag(nltk.word_tokenize(text))
    if words[0] == "when" or "day" in words or "date" in words:
        for ship_syn in get_synonyms('ship', 'v'):
            if ship_syn in text:
                return "shipping_date"
        arrive_syns = get_synonyms("arrive", "v")
        arrive_syns.append("reach")
        arrive_syns.append("get here")
        for arrive_syn in arrive_syns:
            if arrive_syn in text:
                return "arrival_date"

        return "order_date"
    elif "status" in words or "where" in words:
        return "status"
    price_syns = get_synonyms("price", "n")
    price_syns.append("amount")
    price_syns.append("value")
    price_syns.append("charge")
    for word in price_syns:
        if word in words:
            return "price"
    if "how much" in text:
        return "price"
    return ""


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


def get_response(select, result):
    todays_date = datetime.date.today()
    if select == "price":
        return "The price of your order is $" + str(result["price"]) + "."
    elif "count" in select:
        if result["count(*)"] == 1:
            suffix = "s."
        else:
            suffix = "."
        return "You have placed " + str(result["count(*)"]) + " order" + suffix
    elif "avg" in select:
        return "Your average order price is $" + str(result["avg(price)"]) + "."
    elif "sum" in select:
        return "The total cost of your orders is $" + str(result["sum(price)"]) + "."
    elif select == "status":
        return "Your order is currently " + result["status"].lower() + "."
    elif select == "shipping_date":
        if result["shipping_date"] > todays_date:
            return "Your order will be shipped on " + str(todays_date) + "."
        elif result["shipping_date"] < todays_date:
            return "Your order was shipped on " + str(todays_date) + "."
        else:
            return "Your order is being shipped today."
    elif select == "order_date":
        return "Your order was placed on " + str(todays_date) + "."
    else:
        if result["arrival_date"] > todays_date:
            return "Your order will arrive on " + str(todays_date) + "."
        elif result["arrival_date"] < todays_date:
            return "Your order arrived on " + str(todays_date) + "."
        else:
            return "Your order will arrive today."


def get_extra_select(select, query):
    if "average" in query:
        return "avg(" + select + ")"
    elif "how many" in query:
        return "count(*)"
    elif "total" in query:
        return "sum(" + select + ")"
    else:
        return select


def main():
    print("Welcome to NLIDB!")

    user_record = fetchUserRecord()

    query = input("Enter your query: ")
    while query != "exit":

        if query == "switch user":
            user_record = fetchUserRecord()

        elif query == "help":
            print("The following commands are supported: ")
            print("\t\"switch user\" to switch users")
            print("\t\"exit\" to exit NLIDB")

        else:
            print("Processing query: \"" + query + "\"")
            select = get_extra_select(get_select(query.lower()), query.lower())
            sql = "select " + select + " from orders where customer_email=%s"
            result = fetchOneResult(sql, user_record["customer_email"])
            response = get_response(select, result)
            print(response)

        query = input("Enter your query: ")


def debug():
    res = get_synonyms("arrive", "v")
    res.append("reach")
    print(res)
    return


if __name__ == '__main__':
    main()
    #debug()

