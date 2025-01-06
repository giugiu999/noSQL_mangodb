import sys
import string
from pymongo import MongoClient
from datetime import datetime, timezone
from bson import ObjectId

db_name = "291db" 
collation = {"locale": "en", "strength": 2} # set collation for case insensitive
items_per_page = 5 # tweets per page in search tweets

def connect(port: str):
    try:
        # connect to mongodb database
        client = MongoClient(f"mongodb://localhost:{port}/")
        print(f"Successfully connected to mongodb server, port: {port}")
        db = client[db_name]  # get database
        return client, db
    except Exception as e:
        print(f"Fail to connect to database: {e}")
        sys.exit(1)

def strip_punctuation(s: str) -> str:
    """
    delete the punctuations at the front or back of the keyword
    """
    punctuation = set(string.punctuation)
    return s.strip(''.join(punctuation))

def search_tweets(db) -> None:
    """
    Search tweets which matching the keywords
    """
    searchTweetsMsg = "Please enter the keyword(s) (seperated by space): "

    keywordsStr = input(searchTweetsMsg).strip()
    if not keywordsStr:
        print("Keywords cannot be empty. Please try again.\n")
        return

    # get the keyword list and strip the punctuation
    keywords = keywordsStr.split()
    for i in range(len(keywords)):
        keywords[i] = strip_punctuation(keywords[i])
        
    searchTweetsQuery = {
        "$and": [{"content": {"$regex": rf"\b{keyword}\b", "$options": "i"}} for keyword in keywords]
    }

    # calculate tweets number in advance
    try:
        total_tweets = db.tweets.count_documents(searchTweetsQuery)
        if total_tweets == 0:
            print("No tweets found.\n")
            return
    except Exception as e:
        print(f"Error in counting tweets: {e}")
        return

    # pagination and projection to speed up
    page = 0
    projection = {"id": 1, "date": 1, "content": 1, "user.username": 1} # only considering importment attributes

    while True:
        try:
            # search tweets in current page
            tweets_cursor = db.tweets.find(
                searchTweetsQuery,
                projection=projection,
                collation=collation
            ).skip(page * items_per_page).limit(items_per_page)

            tweets = list(tweets_cursor)

        except Exception as e:
            print(f"ERROE in search tweets: {e}")
            return

        if not tweets:
            if page == 0:
                print("No tweets found.\n")
                break
            else:
                print("All tweets have been shown.\n")
                page -= 1
                continue
            
        # print the searching result
        print("----------------------------")
        print(f"PAGE -- {page + 1}")
        print("----------------------------")
        for t in tweets:
            print(f"id: {t['id']}")
            print(f"date: {t['date']}")
            print(f"content: {t['content']}")
            print(f"username: {t['user']['username']}")
            print("----------------------------\n")
        print(f"Tweets in this page: {len(tweets)}.\n")
        print(f"Total tweets found: {total_tweets}.\n")

        # user choice
        nextPageMsg = "\n1. go to the next page\n2. go to the previous page\n3. select a tweet\n4. go back\nEnter your choice: "
        while True:
            choice = input(nextPageMsg).strip()
            if choice == '1': # next page
                page += 1
            elif choice == '2': # previous page
                if page == 0:
                    print("You are already at the first page.")
                else:
                    page -= 1
            elif choice == '3': # select a tweet
                select_tweet(db, tweets)
            elif choice == '4': # go back
                return
            else:
                print("Invalid input.\n")
                continue
            break
            
def select_tweet(db, ts: list) -> None:
    """
    Help the user to select a certain tweet in search_tweets() function
    """
    selectTweetMsg = "Enter the id to select tweet (Enter -1 to go back): "
    while True:
        user_input = input(selectTweetMsg)
        if user_input == '-1':
            break
        if not user_input.isdigit():
            print("Invalid input in selectTweets(). Please check and try again.")
            continue

        user_input = int(user_input)

        # check the tweet exist
        idExist = False
        for t in ts:
            if t["id"] == user_input:
                idExist = True
                break
        if not idExist:
            print("Id does not exist. Please check other pages or search again.")
            continue

        # the tweet exists
        selectTweetQuery = {"id":user_input}
        tweet = db.tweets.find_one(selectTweetQuery, collation = collation)
        if tweet:
            print(f"id: {tweet['id']}")
            print(f"date: {tweet['date']}")
            print(f"content: {tweet['content']}")
            print(f"username: {tweet['user']['username']}")
            print("url:", tweet["url"])
            print("quoteCount:", tweet["quoteCount"])
            print("replyCount:", tweet["replyCount"])
            print("likeCount:", tweet["likeCount"])
            print("retweetCount:", tweet["retweetCount"])
            break
        print("Id does not exist. Please check and try again.")
    input("Press any key to continue: ")

def search_users(db) -> None:
    """
    Search a user by using the matching between a keyword and displayname
    """
    searchUsersMsg = "Enter a keyword to search users: "
    searchUsersCodeMsg = "1. Select a user and see his/her info\n2. Go back to the main menu\n\nEnter your choice: "

    # get the keyword and strip
    keyword = input(searchUsersMsg).strip()
    if not keyword:
        print("Keyword cannot be empty.\n")
        return
    keyword = strip_punctuation(keyword)

    # Regular expression to find the keyword as a separate word in either displayname or location
    searchUsersQuery = {
        "$or": [
            {"user.displayname": {"$regex": rf"\b{keyword}\b", "$options": "i"}},
            {"user.location": {"$regex": rf"\b{keyword}\b", "$options": "i"}}
        ]
    }
    users = db.tweets.find(searchUsersQuery, collation=collation)
    
    # Collecting unique users based on username
    unique_users = {}
    for tweet in users:
        user = tweet['user']
        if user['username'] not in unique_users:
            unique_users[user['username']] = {
                "username": user['username'],
                "displayname": user['displayname'],
                "location": user['location']
            }

    if not unique_users:
        print("There is no user matching the keyword\n\n\n")
        return

    # Displaying the users
    for user in unique_users.values():
        print(f"username: {user['username']}")
        print(f"displayname: {user['displayname']}")
        print(f"location: {user['location']}\n")
    print(f"{len(unique_users)} users found.\n")

    # User options after displaying the search results
    while True:
        choice = input(searchUsersCodeMsg)
        if choice == '1':
            select_user(db, unique_users)
            break
        elif choice == '2':
            print("\n\n\n")
            break
        print("Invalid input. Please try again.")

def select_user(db, users) -> None:
    """
    Used in search_users() to see the info of a certain user
    """
    users = {k.lower(): v for k, v in users.items()}
    selectUserMsg = "Enter the username to select the user (Enter -1 to go back to go back to the main menu): "
    while True:
        user_input = input(selectUserMsg).strip().lower()
        if user_input == '-1':
            print("\n\n\n")
            return
        if user_input not in users:
            print("Invalid input, please try again.")
            continue
        
        # Fetch and display full information about the selected user
        user_query = {"user.username": user_input}
        tweet = db.tweets.find_one(user_query, collation=collation)
        if tweet:
            user_info = tweet['user']
            print("\nFull information about the user:")
            for key, value in user_info.items():
                print(f"{key}: {value}")
            print("\n\n\n")
            return
        else:
            print("User not found, please try again.")

def list_top_tweets(db):
    """
    List top tweets in the database. The sorting standard is chosen by the user from 3 options
    """
    criteriaMsg = "Please enter the option of criteria for listing the top n tweets:\n1. retweetCount\n2. likeCount\n3. quoteCount\n"
    EnterNMsg = "Please Enter the number of tweet(s) you wanna list: "
    while True:
        criteria_choice = input(criteriaMsg).strip()
        if criteria_choice in ('1', '2', '3'):
            break
        print("Invalid input, please try again.")

    criteria_map = {'1': 'retweetCount', '2': 'likeCount', '3': 'quoteCount'}
    selected_criteria = criteria_map[criteria_choice]

    while True:
        n = input(EnterNMsg).strip()
        if n.isdigit():
            n = int(n)
            break
        print("Invalid input, please enter a positive integer.")

    # Query to get top n tweets based on selected criteria
    pipeline = [
        {"$sort": {selected_criteria: -1}},
        {"$limit": n}
    ]
    top_tweets = list(db.tweets.aggregate(pipeline))

    if not top_tweets:
        print("No tweets found.\n\n\n")
        return

    # Displaying the top tweets
    print("------------------")
    for t in top_tweets:
        print(f"id: {t['id']}")
        print(f"date: {t['date']}")
        print(f"content: {t['content']}")
        print(f"username: {t['user']['username']}\n")
        print("------------------")
    print(f"{len(top_tweets)} tweets found.\n\n\n")

    # User options after displaying the top tweets
    listTopTweetsCodeMsg = "1. Select a tweet and see its all info\n2. Go back to the main menu\n\nEnter your choice: "
    while True:
        choice = input(listTopTweetsCodeMsg).strip()
        if choice == '1':
            select_top_tweet(db, top_tweets)
            break
        elif choice == '2':
            print("\n\n\n")
            break
        print("Invalid input, please try again.")

def select_top_tweet(db, top_tweets) -> None:
    """
    Used in list_top_tweets() for browsing a certain tweet
    """
    selectTweetMsg = "Enter the id to select tweet (Enter -1 to go back to the main menu): "
    while True:
        user_input = input(selectTweetMsg).strip()
        if user_input == '-1':
            print("\n\n\n")
            return
        if not user_input.isdigit():
            print("Invalid input, please try again.")
            continue
        tweet_id = int(user_input)
        tweet = next((t for t in top_tweets if t['id'] == tweet_id), None)
        if tweet:
            print("\nFull information about the tweet:")
            for key, value in tweet.items():
                print(f"{key}: {value}")
            print("\n\n\n")
            return
        else:
            print("Id does not exist, please try again.")

def list_top_users(db):
    """
    List top n users in the database, sorting by followers count
    """
    EnterNMsg = "Please Enter the number of users you wanna check: "
    while True:
        n = input(EnterNMsg)
        if n.isdigit():
            break
        print("Invalid input. Please enter a positive integer.")
    
    # set the limit
    n = int(n)
    pipeline = [
        {"$group": {
            "_id": "$user.id",
            "user": {"$first": "$user"}
        }},
        {"$sort": {"user.followersCount": -1}},
        {"$limit": n}
    ]
    top_users = list(db.tweets.aggregate(pipeline))

    if not top_users:
        print("No users found.")
        return

    print("------------------")
    for u in top_users:
        print(f"userID: {u['_id']}")
        print(f"username: {u['user']['username']}")
        print(f"diaplayname: {u['user']['displayname']}")
        print(f"followersCount: {u['user']['followersCount']}")
        print("------------------")
    print(f"{len(top_users)} users showed.")

    # User options after displaying the top tweets
    listTopUsersCodeMsg = "1. Select a user and see its all info\n2. Go back to the main menu\n\nEnter your choice: "
    while True:
        choice = input(listTopUsersCodeMsg).strip()
        if choice == '1':
            select_top_user(db, top_users)
            break
        elif choice == '2':
            print("\n\n\n")
            break
        print("Invalid input, please try again.")

def select_top_user(db, top_users) -> None:
    """
    Used in list_top_users() for browsing a certain user's info
    """
    selectUserMsg = "Enter the id to select user (Enter -1 to go back to the main menu): "
    while True:
        user_input = input(selectUserMsg).strip()
        if user_input == '-1':
            print("\n\n\n")
            return
        if not user_input.isdigit():
            print("Invalid input, please try again.")
            continue

        user_id = int(user_input)
        user = next((u for u in top_users if u['_id'] == user_id), None)
        if user:
            print("\nFull information about the user:\n")
            print("_id:", user['_id'])
            for key, value in user['user'].items():
                print(f"{key}: {value}")
            print("\n\n\n")
            return
        else:
            print("Id does not exist, please try again.")


def compose_tweets(db):
    """
    Compose a tweet
    """
    composeTweetMsg = "Enter content: "
    while True:
        content = input(composeTweetMsg)
        if content:
            break
        print("Tweet content cannot be empty. Please try again.")
    tweet = {"url": None,
             "date": datetime.now(timezone.utc).isoformat(),
            "content": content, 
            "renderedContent": None, 
            "id": str(ObjectId()),
            "user": {"username": "291user", 
                     "displayname": None, 
                     "id": None, 
                     "description": None, 
                     "rawDescription":  None, 
                     "descriptionUrls": None, 
                     "verified": None, 
                     "created": None, 
                     "followersCount": None, 
                     "friendsCount": None, 
                     "statusesCount": None, 
                     "favouritesCount": None, 
                     "listedCount": None, 
                     "mediaCount": None, 
                     "location": None, 
                     "protected": None, 
                     "linkUrl": None, 
                     "linkTcourl": None, 
                     "profileImageUrl": None, 
                     "profileBannerUrl": None, 
                     "url": None}, 
            "outlinks": None, 
            "tcooutlinks": None, 
            "replyCount": None, 
            "retweetCount": None, 
            "likeCount": None, 
            "quoteCount": None, 
            "conversationId": None, 
            "lang": None, 
            "source": None, 
            "sourceUrl": None, 
            "sourceLabel": None, 
            "media": None, 
            "retweetedTweet": None, 
            "quotedTweet": None, 
            "mentionedUsers": None}

    result = db.tweets.insert_one(tweet)

    # check if composed successfully
    if result.acknowledged:
        print(f"Tweet successfully composed.")
    else:
        print("Failed to compose tweet. Please try again.")



def main():
    # check the arguments in command line
    if len(sys.argv) != 2:
        print("Usage: python3 main.py <port>")
        sys.exit(1)
    
    port = sys.argv[1]
    clientAndDB = connect(port)
    client = clientAndDB[0]
    db = clientAndDB[1]

    instructionMsg = "Please Enter Corresponding code:\n1. Search for tweets\n2. Search for users\
        \n3. List top tweets\n4. List top users\n5. Compose a tweet\n6. Exit"

    # main loop
    while True:
        # get the user code 
        print(instructionMsg)
        while True:
            code = input("Enter your code: ")
            if code in ('1','2','3','4','5','6'):
                break
            print("Invalid code. Please check and try again.")
        
        code = int(code)
        if code == 1: # search tweets
            search_tweets(db)
        elif code == 2: # search users
            search_users(db)
        elif code == 3: # list top tweets
            list_top_tweets(db)
        elif code == 4: # list top users
            list_top_users(db)
        elif code == 5: # compose tweet
            compose_tweets(db)
        else: # exit
            print("Exit Successfully.")
            break

    # client will close automatically, but here we do it explicitly
    client.close()
    print("Client Closed Successfully.")
    return


if __name__ == '__main__':
    main()
