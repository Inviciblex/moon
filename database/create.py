# Creating DB

CREATE_PROFILES = """CREATE TABLE IF NOT EXISTS profiles (
    user_id BIGINT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    age INTEGER NOT NULL CHECK (age >= 18 AND age <= 120),
    gender VARCHAR(20) NOT NULL,
    description TEXT,
    photo_id VARCHAR(255),
    target_gender VARCHAR(20),  -- Пол, который ищет пользователь
    last_activity VARCHAR(50),  -- Тип для временных меток
    username VARCHAR(50) UNIQUE  -- Уникальное имя пользователя
);"""

CREATE_LIKES = """CREATE TABLE IF NOT EXISTS likes (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    liked_user_id BIGINT NOT NULL,
    mutual BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES profiles (user_id) ON DELETE CASCADE,
    FOREIGN KEY (liked_user_id) REFERENCES profiles (user_id) ON DELETE CASCADE
);"""

CREATE_TARGET_GENDER = "ALTER TABLE profiles ADD COLUMN target_gender TEXT"

CREATE_LAST_ACTIVITY = "ALTER TABLE profiles ADD COLUMN last_activity TEXT"

CREATE_USERNAME = "ALTER TABLE profiles ADD COLUMN username TEXT"

CREATE_MESSAGE_COUNT = "ALTER TABLE profiles ADD COLUMN message_count INTEGER DEFAULT 0"

DELETE_LIKES = "DELETE FROM likes"

SAVE_FORM = """
INSERT INTO profiles (
    user_id, 
    name, 
    age, 
    gender, 
    description, 
    photo_id, 
    target_gender, 
    username
) 
VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
ON CONFLICT (user_id) 
DO UPDATE SET
    name = EXCLUDED.name,
    age = EXCLUDED.age,
    gender = EXCLUDED.gender,
    description = EXCLUDED.description,
    photo_id = EXCLUDED.photo_id,
    target_gender = EXCLUDED.target_gender,
    username = EXCLUDED.username
"""