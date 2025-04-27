from flask import Flask, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from flask_session import Session
import psycopg2
import logging
import os

app = Flask(__name__)
app.config["SESSION_TYPE"] = "filesystem"
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
CORS(app, supports_credentials=True)
Session(app) 
app.config["SESSION_COOKIE_SECURE"] = True  # Ensures cookies are only sent over HTTPS
app.config["SESSION_COOKIE_HTTPONLY"] = True  # Prevents client-side JS from accessing cookies
app.config["SESSION_COOKIE_SAMESITE"] = "None"  # Required for cross-site requests


ADMIN_LOGIN = os.getenv("ADMIN_LOGIN")
ADMIN_PASS = os.getenv("ADMIN_PASS")
DEV_MODE = os.getenv("DEV_MODE")

#Gets the connection
def get_db_connection():
    if DEV_MODE == "True":
        logging.info("DEV_MODE set to \"True\" in .env file, using local DB")
        try:
            conn = psycopg2.connect(
                database="postgres",
                user="postgres",
                password="password",
                host="localhost",
                port="5432"
            )
            logging.info("Connected to the database successfully.")
            return conn
        except Exception as e:
            logging.error(f"Database connection failed: {str(e)}")
            return None

    else:
        try:
            conn = psycopg2.connect(
                database="postgres",
                host="apollo-dev.postgres.database.azure.com",
                user=ADMIN_LOGIN,
                password=ADMIN_PASS,
                port="5432",
                sslmode="require"
            )
            logging.info("Connected to the database successfully.")
            return conn
        except Exception as e:
            logging.error(f"Database connection failed: {str(e)}")
            return None

## IMAGE UPLOADING STUFF

# IMAGE UPLOAD CONFIG:
UPLOAD_FOLDER = '/profilePictures'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# checks if valid filetype
# TODO: set a max size so people don't try to upload a
# 16000x16000 75.4TB png file named "THE SINNER" which is just a picture of a cat
def allowed_files(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'profilePicture' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['profilePicture']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_files(file.filename):
        filename = file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify({"message": "File uploaded successfully", "filename": filename}), 200

    return jsonify({"error": "File type not allowed"}), 400

## END OF IMAGE UPLOADING STUFF

#the route/url that is sends the post
@app.route('/add_user', methods=['POST'])
def add_user():
    #adds the user 
    try:
        logging.info("Received request to /add_user")
        # gets the data and its json object
        data = request.get_json();
        if not data:
            logging.error("No JSON received!")
            return jsonify({"error": "Invalid JSON"}), 400
        
        username=data['username']
        password=data['password']
        email=data['email']

        if not username or not password or not email:
            logging.error(f"Missing fields: {data}")
            return jsonify({"error": "Missing fields"}), 400
        

        logging.info(f"Adding user: {username}, {email}")

        conn=get_db_connection() #gets teh connection
        cursor=conn.cursor() 

         #TODO: 
        #1. Add SQL Injection prevention
        #2. Add email verification, I.e make sure the email does not exist within the db

        #inserts the user into the db 
        cursor.execute("""
            INSERT INTO users (username, password, email)
            VALUES (%s, %s, %s)
            RETURNING username, email;
        """, (username, password, email))

        new_user = cursor.fetchone(); #gets new user for debugging
        conn.commit();
        cursor.close();
        conn.close();

        #debugging
        if new_user:
            
            return jsonify({"message": "User added successfully", "user": new_user}), 201
        else:
            return jsonify({"error": "Failed to add user"}), 400
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
@app.route('/validate_user', methods=['POST'])
def validate_user():
    #adds the user 
    try:
        logging.info("Received request to /validate_user")
        # gets the data and its json object
        data = request.get_json();
        if not data:
            logging.error("No JSON received!")
            return jsonify({"error": "Invalid JSON"}), 400
        
        username_or_email=data['username_or_email']
        password=data['password']
        

        if not username_or_email or not password:
            logging.error(f"Missing fields: {data}")
            return jsonify({"error": "Missing fields"}), 400
        

       

        conn=get_db_connection() #gets teh connection
        cursor=conn.cursor() 


       


        #inserts the user into the db 
        cursor.execute("SELECT username, email FROM users WHERE (username = %s OR email = %s) AND password = %s",
                        (username_or_email, username_or_email, password))
        user = cursor.fetchone();
        

        cursor.close();
        conn.close();
    
        if user:
            session["user"] = {"username": user[0], "email": user[1]}
            session.modified = True  # Ensure session is marked as changed
            print("Session Data:", session)
            return jsonify({"message": "User validated", "user": session["user"]}), 200
        else:
            return jsonify({"error": "Invalid username or password"}), 401
        
    except Exception as e:
        logging.error(f"Error in validate_user: {str(e)}")
        return jsonify({"error": str(e)}), 400

@app.route('/update_user_data', methods=['POST'])
def update_user_data():
    try:
        logging.info("Received request to /update_user_data")

        if 'user' not in session or 'username' not in session['user']:
            logging.error("User is not logged in.")
            return jsonify({"error": "User must be logged in."}), 401

        username = session['user']['username']  # Get username from session
        data = request.get_json()
        if not data:
            logging.error("No JSON received!")
            return jsonify({"error": "Invalid JSON"}), 400

        # Extract other data from request
        phone = data.get("phone")
        github = data.get("github")
        discord = data.get("discord")
        interests = data.get("interests")
        skills = data.get("skills")
        past_projects = data.get("pastProjects")
        creativity = data.get("creativity")
        leadership = data.get("leadership")
        enthusiasm = data.get("enthusiasm")

        conn = get_db_connection()
        cursor = conn.cursor()

        # Update users table
        cursor.execute("""
            UPDATE users 
            SET interestsandhobbies = %s, skills = %s, pastprojects = %s 
            WHERE username = %s
        """, (interests, skills, past_projects, username))

        # Update or insert into personal_traits
        cursor.execute("""
            INSERT INTO personal_traits (username, creativity, leadership, enthusiasm) 
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (username) 
            DO UPDATE SET creativity = EXCLUDED.creativity, 
                          leadership = EXCLUDED.leadership, 
                          enthusiasm = EXCLUDED.enthusiasm
        """, (username, creativity, leadership, enthusiasm))

        # Update or insert into user_contacts
        cursor.execute("""
            INSERT INTO user_contacts (username, phone_number, github_link, discord_profile) 
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (username) 
            DO UPDATE SET phone_number = EXCLUDED.phone_number, 
                          github_link = EXCLUDED.github_link, 
                          discord_profile = EXCLUDED.discord_profile
        """, (username, phone, github, discord))
        conn.commit()
        # Fetch updated user data
        cursor.execute("""
            SELECT u.username, u.email, u.interestsandhobbies, u.skills, u.pastprojects, 
                   p.creativity, p.leadership, p.enthusiasm, 
                   c.phone_number, c.github_link, c.discord_profile
            FROM users u
            LEFT JOIN personal_traits p ON u.username = p.username
            LEFT JOIN user_contacts c ON u.username = c.username
            WHERE u.username = %s
        """, (username,))

        updated_user = cursor.fetchone()
        if updated_user:
            session['user'] = {
                "username": updated_user[0],
                "email": updated_user[1],
                "interests": updated_user[2],
                "skills": updated_user[3],
                "pastProjects": updated_user[4],
                "creativity": updated_user[5],
                "leadership": updated_user[6],
                "enthusiasm": updated_user[7],
                "phone": updated_user[8],
                "github": updated_user[9],
                "discord": updated_user[10]
            }
        
            cursor.close()
            conn.close()

        return jsonify({"message": "User data updated successfully"}), 200

    except Exception as e:
        logging.error(f"Error updating user data: {str(e)}")
        return jsonify({"error": str(e)}), 400


@app.route('/get_user_data', methods=['POST'])
def get_user_data():
    try:
        logging.info("Received request to /get_user_data")
        
        data = request.get_json()
        if not data or 'username' not in data:
            logging.error("Username not provided!")
            return jsonify({"error": "Username is required"}), 400

        username = data['username']

        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch user data from multiple tables
        cursor.execute("""
            SELECT u.username, u.email, u.interestsandhobbies, u.skills, u.pastprojects, 
                   p.creativity, p.leadership, p.enthusiasm, 
                   c.phone_number, c.github_link, c.discord_profile
            FROM users u
            LEFT JOIN personal_traits p ON u.username = p.username
            LEFT JOIN user_contacts c ON u.username = c.username
            WHERE u.username = %s
        """, (username,))

        user_data = cursor.fetchone()
        cursor.close()
        conn.close()

        if user_data:
            return jsonify({
                "username": user_data[0],
                "email": user_data[1],
                "interests": user_data[2],
                "skills": user_data[3],
                "pastProjects": user_data[4],
                "creativity": user_data[5],
                "leadership": user_data[6],
                "enthusiasm": user_data[7],
                "phone": user_data[8],
                "github": user_data[9],
                "discord": user_data[10]
            }), 200
        else:
            logging.warning(f"No user found with username: {username}")
            return jsonify({"error": "User not found"}), 404

    except Exception as e:
        logging.error(f"Error fetching user data: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/current_user', methods=['GET'])
def current_user():
    user = session.get("user")
    if user:
        return jsonify({"user": user})
    return jsonify({"error": "No user logged in"}), 401

@app.route('/get_compatible_users', methods=['POST'])
def get_compatible_users():
    try:
        logging.info("Received request to /get_compatible_users")
        data = request.get_json()
        if not data or 'username' not in data:
            return jsonify({"error": "Username is required"}), 400

        target_username = data['username']

        conn = get_db_connection()
        cursor = conn.cursor()

        # Get the target user's traits
        cursor.execute("""
            SELECT u.username, u.interestsandhobbies, u.skills, u.pastprojects,
                   p.creativity, p.leadership, p.enthusiasm
            FROM users u
            LEFT JOIN personal_traits p ON u.username = p.username
            WHERE u.username = %s
        """, (target_username,))
        target_user = cursor.fetchone()

        if not target_user:
            return jsonify({"error": "Target user not found"}), 404

        def parse_keywords(text):
            return set(map(str.strip, text.lower().split(','))) if text else set()

        target_interests = parse_keywords(target_user[1])
        target_skills = parse_keywords(target_user[2])
        target_projects = parse_keywords(target_user[3])
        target_traits = target_user[4:7]  # (creativity, leadership, enthusiasm)

        # Fetch all other users and their traits
        cursor.execute("""
            SELECT u.username, u.interestsandhobbies, u.skills, u.pastprojects,
                   p.creativity, p.leadership, p.enthusiasm
            FROM users u
            LEFT JOIN personal_traits p ON u.username = p.username
            WHERE u.username != %s
        """, (target_username,))
        other_users = cursor.fetchall()

        def calculate_similarity(other):
            username, interests, skills, projects, creativity, leadership, enthusiasm = other

            interests_sim = len(target_interests & parse_keywords(interests))
            skills_sim = len(target_skills & parse_keywords(skills))
            projects_sim = len(target_projects & parse_keywords(projects))

            trait_sim = 0
            if None not in (creativity, leadership, enthusiasm):
                trait_sim = 10 - abs(target_traits[0] - creativity) \
                            + 10 - abs(target_traits[1] - leadership) \
                            + 10 - abs(target_traits[2] - enthusiasm)

            # Weighted score: can be adjusted
            score = (2 * interests_sim) + (3 * skills_sim) + (1.5 * projects_sim) + (0.5 * trait_sim)
            return (username, score)

        similarities = [calculate_similarity(user) for user in other_users]
        similarities.sort(key=lambda x: x[1], reverse=True)

        top_matches = similarities[:6]
        result = [{"username": username, "compatibilityScore": score} for username, score in top_matches]

        cursor.close()
        conn.close()

        return jsonify(result), 200

    except Exception as e:
        logging.error(f"Error in /get_compatible_users: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
    
@app.route('/search_users', methods=['POST'])
def search_users():
    try:
        logging.info("Received request to /search_users")
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({"error": "Query is required"}), 400

        query = data['query'].lower()

        conn = get_db_connection()
        cursor = conn.cursor()

        # Search users whose username, interests, skills, or projects match the query
        cursor.execute("""
            SELECT u.username, u.interestsandhobbies, u.skills, u.pastprojects
            FROM users u
            WHERE LOWER(u.username) LIKE %s
               OR LOWER(u.interestsandhobbies) LIKE %s
               OR LOWER(u.skills) LIKE %s
               OR LOWER(u.pastprojects) LIKE %s
            LIMIT 10
        """, (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'))

        results = cursor.fetchall()

        users = [{"username": r[0]} for r in results]

        cursor.close()
        conn.close()

        return jsonify(users), 200

    except Exception as e:
        logging.error(f"Error in /search_users: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/logout_user', methods=['GET'])
def logout_user():
    session.clear()  # Clear the session for logout
    return jsonify({"message": "User logged out successfully"}), 200

if __name__ == '__main__':
    app.run(debug=True)

