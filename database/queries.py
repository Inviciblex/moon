# admin.py

ACTIVE_USERS = """
    SELECT COUNT(*) FROM profiles WHERE last_activity >= $1
"""

MESSAGES_TOTAL = """
    SELECT SUM(message_count) FROM profiles
"""

AVG_AGE = """
    SELECT AVG(age) FROM profiles
"""

ACTIVE_TIME = """
    SELECT strftime('%H:00', last_activity) AS hour, COUNT(*) FROM profiles GROUP BY hour ORDER BY COUNT(*) DESC LIMIT 1
"""

TOTAL_USERS = """
    SELECT COUNT(*) FROM profiles
"""

UPDATE_LAST_ACTIVITY = "UPDATE profiles SET last_activity = $1 WHERE user_id = $2"

# handlers.py

UPDATE_MESSAGE_COUNT = "UPDATE profiles SET message_count = message_count + 1 WHERE user_id = $1"

GET_USER_INFO = "SELECT name, age, description, photo_id FROM profiles WHERE user_id = $1"

DELETE_SELF_LIKE = "DELETE FROM likes WHERE user_id = $1"

DELETE_SEND_LIKE = "DELETE FROM likes WHERE liked_user_id = $1"

GET_ID_BY_USERNAME = "SELECT user_id FROM profiles WHERE username = $1"

GET_IDS = "SELECT user_id FROM profiles"

DELETE_FORM = "DELETE FROM profiles WHERE user_id = $1"

GET_USER_DATA = "SELECT gender, target_gender, age FROM profiles WHERE user_id = $1"

SEARCH_FORMS = """SELECT * FROM profiles 
           WHERE user_id != $1 
           AND gender = $2 
           AND target_gender = $3 
           AND age >= $4 
           AND age <= $5 
           AND last_activity >= $6
           AND user_id NOT IN ({}) 
           ORDER BY RANDOM() 
           LIMIT 1
"""

CHECK_LIKE = "SELECT * FROM likes WHERE user_id = $1 AND liked_user_id = $2"

SAVE_LIKE = "INSERT INTO likes (user_id, liked_user_id, user_name, liked_name) VALUES ($1, $2, $3, $4)"

REPORTED_USER = "SELECT name, username, gender, age, description, photo_id, target_gender FROM profiles WHERE user_id = $1"

LIKE_INFO = "SELECT user_id, liked_user_id, liked_name FROM likes WHERE liked_user_id = ?"

FORM_INFO = "SELECT name, age, description, gender, target_gender, photo_id FROM profiles WHERE user_id = $1"