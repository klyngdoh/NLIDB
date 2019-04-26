import pymysql.cursors
from nltk.corpus import wordnet
import datetime
from contractions import CONTRACTION_MAP
import nltk
import re
import spacy


# Connect to the database
connection = pymysql.connect(host='localhost',
                             user='root',
                             password='admin',
                             db='nlp',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)

print("Initializing...")
stopword_list = nltk.corpus.stopwords.words('english')
stopword_list.remove('no')
stopword_list.remove('not')
stopword_list.remove('when')
stopword_list.remove('where')
stopword_list.remove('how')
nlp = spacy.load('en_core_web_md', parse=True, tag=True, entity=True)


def lemmatize_text(text):
    # Lemmatize the whole text
    text = nlp(text)
    text = ' '.join([word.lemma_ if word.lemma_ != '-PRON-' else word.text for word in text])
    return text


def remove_stopwords(text, is_lower_case=False):
    # Remove stop words like a, an, the, etc.
    tokens = nltk.word_tokenize(text)
    tokens = [token.strip() for token in tokens]
    if is_lower_case:
        filtered_tokens = [token for token in tokens if token not in stopword_list]
    else:
        filtered_tokens = [token for token in tokens if token.lower() not in stopword_list]
    filtered_text = ' '.join(filtered_tokens)
    return filtered_text


def expand_contractions(text, contraction_mapping=CONTRACTION_MAP):
    # Expand words like don't, doesn't, etc. to help with POS tagging
    contractions_pattern = re.compile('({})'.format('|'.join(contraction_mapping.keys())),
                                      flags=re.IGNORECASE | re.DOTALL)

    def expand_match(contraction):
        match = contraction.group(0)
        first_char = match[0]
        expanded_contraction = contraction_mapping.get(match) \
            if contraction_mapping.get(match) \
            else contraction_mapping.get(match.lower())
        expanded_contraction = first_char + expanded_contraction[1:]
        return expanded_contraction

    expanded_text = contractions_pattern.sub(expand_match, text)
    expanded_text = re.sub("'", "", expanded_text)
    return expanded_text


def simple_stemmer(text):
    # Convert the word to the Stem word
    ps = nltk.porter.PorterStemmer()
    text = ' '.join([ps.stem(word) for word in text.split()])
    return text


def normalize_text(text):
    # normalize the text
    doc = expand_contractions(text)
    # lowercase the text
    doc = doc.lower()
    # remove extra newlines
    doc = re.sub(r'[\r|\n|\r\n]+', ' ', doc)
    # lemmatize text
    doc = lemmatize_text(doc)
    # remove special characters and\or digits

    # remove extra whitespace
    doc = re.sub(' +', ' ', doc)
    # remove stopwords
    doc = remove_stopwords(doc)
    return doc


def get_synonyms(word, pos):
    synonyms = []
    for syn in wordnet.synsets(word):
        if ("." + pos + ".") in syn.name():
            for l in syn.lemmas():
                synonyms.append(l.name().replace('_', ' '))
    return list(set(synonyms))


def get_select(text):
    normalized_text = normalize_text(text)
    print("Normalized text = ", normalized_text)
    words = nltk.word_tokenize(normalized_text)
    pos_tags = nltk.pos_tag(words)

    if words[0] == "when" or "day" in words or "date" in words:
        ship_syns = get_synonyms('ship', 'v')
        ship_syns.append("dispatched")
        ship_syns.append("sent")
        for ship_syn in ship_syns:
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
    except Exception as e:
        print("An exception occured: " + str(e))


def update_db(query, params):
    try:
        with connection.cursor() as cursor:
            sql = query
            cursor.execute(sql, params)
            connection.commit()
            return True
    except Exception as e:
        print("An exception occurred: " + str(e))
        return False


def fetchUserRecord():
    customer_email = input("Please enter your email: ")
    user_record = fetchOneResult("Select * from orders where customer_email=%s", (customer_email,))

    while user_record is None:
        print("User record not found!")
        customer_email = input("Please enter correct email: ")

        user_record = fetchOneResult("Select * from orders where customer_email=%s", (customer_email,))

    print("Welcome", user_record['customer_first'])
    return user_record


def get_response(select, result):
    todays_date = datetime.date.today()
    if select == "price":
        return "The price of your order is $" + str(result["price"]) + "."
    elif "count" in select:
        if result["count(*)"] == 1:
            suffix = "."
        else:
            suffix = "s."
        return "You have placed " + str(result["count(*)"]) + " order" + suffix
    elif "avg" in select:
        return "Your average order price is $" + str(result["avg(price)"]) + "."
    elif "sum" in select:
        return "The total cost of your orders is $" + str(result["sum(price)"]) + "."
    elif select == "status":
        return "Your order is currently " + result["status"].lower() + "."
    elif select == "shipping_date":
        if result["shipping_date"] > todays_date:
            return "Your order will be shipped on " + str(result["shipping_date"]) + "."
        elif result["shipping_date"] < todays_date:
            return "Your order was shipped on " + str(result["shipping_date"]) + "."
        else:
            return "Your order is being shipped today."
    elif select == "order_date":
        return "Your order was placed on " + str(result["order_date"]) + "."
    else:
        if result["arrival_date"] > todays_date:
            return "Your order will arrive on " + str(result["arrival_date"]) + "."
        elif result["arrival_date"] < todays_date:
            return "Your order arrived on " + str(result["arrival_date"]) + "."
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


def get_date(query):
    date_hyphen = (re.search(r'(\d{4}-\d{2}-\d{2})', query))
    if date_hyphen is not None:
        return date_hyphen.group(1)
    date_slash = (re.search(r'(\d{4}/\d{2}/\d{2})', query))
    if date_slash is not None:
        return date_slash.group(1)
    date = re.search(r'(\s+\d{2}\s+)', query)
    year = re.search(r'(\s+\d{4}\s*)', query)
    d = date.group(1).strip()
    y = year.group(1).strip()
    months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    months_short = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sept", "Oct", "Nov", "Dec"]
    date_month = ""
    for month in months:
        if month.lower() in query:
            return y + "-" + ("0" + str(months.index(month) + 1))[0:2] + "-" + d

    for month in months_short:
        if month.lower() in query:
            return y + "-" + ("0" + str(months_short.index(month) + 1))[0:2] + "-" + d
    return ""


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

        elif "cancel" in query:
            odate = get_date(query.lower())
            sql = "update orders set status='Canceled' where order_date='" + odate + "' and customer_email=%s"
            print(sql)
            if update_db(sql, user_record["customer_email"]):
                print("The requested order has been canceled.")

        else:
            select = get_extra_select(get_select(query.lower()), query.lower())
            sql = "select " + select + " from orders where customer_email=%s order by order_date desc"
            print(sql)
            result = fetchOneResult(sql, user_record["customer_email"])
            response = get_response(select, result)
            print(response)

        query = input("Enter your query: ")


def debug():
    print(get_date("cancel my order placed on 20 Apr 2019"))
    return


if __name__ == '__main__':
    main()
    #debug()

