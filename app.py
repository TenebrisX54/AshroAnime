from flask import Flask, render_template, request, jsonify, redirect
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
from flask_cors import CORS
import os # Keep os for MONGO_URI, as it's good practice for production

app = Flask(__name__)
CORS(app)

# --- MongoDB Atlas Configuration ---
# It's highly recommended to use environment variables for MONGO_URI in production.
# For local testing, you can temporarily hardcode it or set it as an environment variable in your terminal.
# Example: export MONGO_URI="mongodb+srv://ZenkaiWorld:GREATEMPEROR.9@zenkaiworld.5zly2up.mongodb.net/?retryWrites=true&w=majority&appName=ZenkaiWorld"
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://ZenkaiWorld:GREATEMPEROR.9@zenkaiworld.5zly2up.mongodb.net/?retryWrites=true&w=majority&appName=ZenkaiWorld")
DATABASE_NAME = "ZenkaiWorld" 

# Database connection in a try-except block
try:
    if not MONGO_URI:
        print("Warning: MONGO_URI environment variable is not set. Using hardcoded value. Please set it for production.")
    
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    anime_collection = db.ZenkaiWorld
    next_anime_collection = db.NextAnime
    comments_collection = db.Comments 
    print("MongoDB Atlas connection successful!")
except Exception as e:
    print(f"Error connecting to MongoDB Atlas: {e}")
    # In a production environment, you might want to exit the app here:
    # exit(1) 

# --- Routes ---

# 1. Render Home page
@app.route("/")
def home():
    return render_template("Home.html")

# 2. Render Watch page
@app.route("/watch")
def watch():
    return render_template("watch.html")

# 3. Render Contact page
@app.route("/contact")
def contact():
    return render_template("contact.html")

# 4. Render Admin panel
@app.route("/Admin_Moaz")
def admin_panel():
    return render_template("Admin_Moaz.html")

# --- API Endpoints ---

# 5. Get all anime
@app.route("/api/anime", methods=["GET"])
def get_all_anime():
    try:
        anime_data = list(anime_collection.find({}))
        for anime in anime_data:
            anime["_id"] = str(anime["_id"]) 
            anime["uploader_name"] = anime.get("uploader_name", "Unknown")
            anime["is_popular"] = anime.get("is_popular", False)
            anime["is_latest"] = anime.get("is_latest", False)
        return jsonify(anime_data), 200
    except Exception as e:
        print(f"Error fetching all anime: {e}")
        return jsonify({"error": "Failed to fetch anime", "details": str(e)}), 500

# 6. Get a single anime by ID
@app.route("/api/anime/<anime_id>", methods=["GET"])
def get_anime_by_id(anime_id):
    try:
        anime = anime_collection.find_one({"_id": ObjectId(anime_id)})
        if anime:
            anime["_id"] = str(anime["_id"])
            anime["uploader_name"] = anime.get("uploader_name", "Unknown")
            anime["is_popular"] = anime.get("is_popular", False)
            anime["is_latest"] = anime.get("is_latest", False)
            return jsonify(anime), 200
        return jsonify({"error": "Anime not found"}), 404
    except Exception as e:
        print(f"Error fetching anime by ID: {e}")
        return jsonify({"error": "Failed to fetch anime", "details": str(e)}), 500

# 7. Add new anime (for Admin panel or user upload)
@app.route("/api/upload_anime", methods=["POST"])
def upload_anime():
    data = request.get_json()
    required_fields = ["title", "category", "image", "download1080p", "review"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        data["created_at"] = datetime.utcnow()
        data["uploader_name"] = data.get("uploader_name", "ADMIN") 
        data["is_popular"] = data.get("is_popular", False) 
        data["is_latest"] = data.get("is_latest", False) 
        result = anime_collection.insert_one(data)
        return jsonify({"message": "Anime uploaded successfully", "id": str(result.inserted_id)}), 201
    except Exception as e:
        print(f"Error uploading anime: {e}")
        return jsonify({"error": "Failed to upload anime", "details": str(e)}), 500

# 8. Delete anime (for Admin panel)
@app.route("/api/delete_anime/<anime_id>", methods=["DELETE"])
def delete_anime(anime_id):
    try:
        result = anime_collection.delete_one({"_id": ObjectId(anime_id)})
        if result.deleted_count == 1:
            return jsonify({"message": "Anime deleted successfully"}), 200
        return jsonify({"error": "Anime not found"}), 404
    except Exception as e:
        print(f"Error deleting anime: {e}")
        return jsonify({"error": "Failed to delete anime", "details": str(e)}), 500

# 9. Update anime (for Admin panel)
@app.route("/api/update_anime/<anime_id>", methods=["PUT"])
def update_anime(anime_id):
    data = request.get_json()
    if '_id' in data: del data['_id'] 
    if 'created_at' in data: del data['created_at'] 
    if 'uploader_name' in data: del data['uploader_name']
    if 'is_popular' in data: del data['is_popular']
    if 'is_latest' in data: del data['is_latest']

    if 'download720p' in data and data['download720p'] == '':
        data['download720p'] = None
    if 'trailerUrl' in data and data['trailerUrl'] == '':
        data['trailerUrl'] = None

    try:
        result = anime_collection.update_one({"_id": ObjectId(anime_id)}, {"$set": data})
        if result.matched_count == 1:
            return jsonify({"message": "Anime updated successfully"}), 200
        return jsonify({"error": "Anime not found"}), 404
    except Exception as e:
        print(f"Error updating anime: {e}")
        return jsonify({"error": "Failed to update anime", "details": str(e)}), 500

# 10. Set Next Anime name (for Admin panel)
@app.route("/api/set_next_anime", methods=["POST"])
def set_next_anime():
    data = request.get_json()
    anime_name = data.get("anime_name")
    if not anime_name:
        return jsonify({"error": "Anime name is required"}), 400
    try:
        next_anime_collection.delete_many({})
        result = next_anime_collection.insert_one({"anime_name": anime_name, "created_at": datetime.utcnow()})
        return jsonify({"message": "Next Anime name set successfully", "id": str(result.inserted_id)}), 200
    except Exception as e:
        print(f"Error setting next anime: {e}")
        return jsonify({"error": "Failed to set next anime", "details": str(e)}), 500

# 11. Get Next Anime name (for Home.html and Admin.html)
@app.route("/api/next_anime", methods=["GET"])
def get_next_anime():
    try:
        next_anime = next_anime_collection.find_one(sort=[("created_at", -1)])
        if next_anime:
            return jsonify({"anime_name": next_anime.get("anime_name", "No Next Anime Set")}), 200
        return jsonify({"anime_name": "No Next Anime Set"}), 200
    except Exception as e:
        print(f"Error fetching next anime: {e}")
        return jsonify({"error": "Failed to fetch next anime", "details": str(e)}), 500

# 12. Clear Next Anime name (for Admin.html)
@app.route("/api/clear_next_anime", methods=["POST"])
def clear_next_anime():
    try:
        next_anime_collection.delete_many({})
        return jsonify({"message": "Next Anime cleared successfully"}), 200
    except Exception as e:
        print(f"Error clearing next anime: {e}")
        return jsonify({"error": "Failed to clear next anime", "details": str(e)}), 500

# 13. Add reaction to a comment
@app.route("/api/comments/<comment_id>/react", methods=["POST"])
def react_to_comment(comment_id):
    data = request.get_json()
    reaction_type = data.get("type") 
    
    if reaction_type not in ["like", "dislike"]:
        return jsonify({"error": "Invalid reaction type"}), 400
    
    try:
        update_field = f"{reaction_type}s" 
        result = comments_collection.update_one(
            {"_id": ObjectId(comment_id)},
            {"$inc": {update_field: 1}}
        )
        if result.modified_count == 1:
            return jsonify({"message": "Reaction added successfully"}), 200
        return jsonify({"error": "Comment not found"}), 404
    except Exception as e:
        print(f"Error reacting to comment: {e}")
        return jsonify({"error": "Failed to add reaction", "details": str(e)}), 500

# 14. Add reaction to a reply
@app.route("/api/comments/<comment_id>/replies/<reply_id>/react", methods=["POST"])
def react_to_reply(comment_id, reply_id):
    data = request.get_json()
    reaction_type = data.get("type") 
    
    if reaction_type not in ["like", "dislike"]:
        return jsonify({"error": "Invalid reaction type"}), 400
    
    try:
        update_field = f"replies.$.{reaction_type}s" 
        result = comments_collection.update_one(
            {"_id": ObjectId(comment_id), "replies._id": ObjectId(reply_id)},
            {"$inc": {update_field: 1}}
        )
        if result.modified_count == 1:
            return jsonify({"message": "Reaction added to reply successfully"}), 200
        return jsonify({"error": "Comment or reply not found"}), 404
    except Exception as e:
        print(f"Error reacting to reply: {e}")
        return jsonify({"error": "Failed to add reaction to reply", "details": str(e)}), 500

# 15. Mark anime as popular
@app.route("/api/mark_popular/<anime_id>", methods=["POST"])
def mark_popular(anime_id):
    try:
        result = anime_collection.update_one(
            {"_id": ObjectId(anime_id)},
            {"$set": {"is_popular": True}}
        )
        if result.modified_count == 1:
            return jsonify({"message": "Anime marked as popular"}), 200
        return jsonify({"error": "Anime not found"}), 404
    except Exception as e:
        print(f"Error marking anime as popular: {e}")
        return jsonify({"error": "Failed to mark anime as popular", "details": str(e)}), 500

# 16. Unmark anime as popular
@app.route("/api/unmark_popular/<anime_id>", methods=["POST"])
def unmark_popular(anime_id):
    try:
        result = anime_collection.update_one(
            {"_id": ObjectId(anime_id)},
            {"$set": {"is_popular": False}}
        )
        if result.modified_count == 1:
            return jsonify({"message": "Anime unmarked as popular"}), 200
        return jsonify({"error": "Anime not found"}), 404
    except Exception as e:
        print(f"Error unmarking anime as popular: {e}")
        return jsonify({"error": "Failed to unmark anime as popular", "details": str(e)}), 500

# 17. Mark anime as latest
@app.route("/api/mark_latest/<anime_id>", methods=["POST"])
def mark_latest(anime_id):
    try:
        result = anime_collection.update_one(
            {"_id": ObjectId(anime_id)},
            {"$set": {"is_latest": True, "created_at": datetime.utcnow()}} 
        )
        if result.modified_count == 1:
            return jsonify({"message": "Anime marked as latest"}), 200
        return jsonify({"error": "Anime not found"}), 404
    except Exception as e:
        print(f"Error marking anime as latest: {e}")
        return jsonify({"error": "Failed to mark anime as latest", "details": str(e)}), 500

# 18. Unmark anime as latest
@app.route("/api/unmark_latest/<anime_id>", methods=["POST"])
def unmark_latest(anime_id):
    try:
        result = anime_collection.update_one(
            {"_id": ObjectId(anime_id)},
            {"$set": {"is_latest": False}}
        )
        if result.modified_count == 1:
            return jsonify({"message": "Anime unmarked as latest"}), 200
        return jsonify({"error": "Anime not found"}), 404
    except Exception as e:
        print(f"Error unmarking anime as latest: {e}")
        return jsonify({"error": "Failed to unmark anime as latest", "details": str(e)}), 500

# 19. Get comments (for Contact.html)
@app.route("/api/comments", methods=["GET"])
def get_comments():
    try:
        comments = list(comments_collection.find({}).sort("created_at", -1)) 
        for comment in comments:
            comment["_id"] = str(comment["_id"])
            if "replies" in comment:
                for reply in comment["replies"]:
                    reply["_id"] = str(reply["_id"])
        return jsonify(comments), 200
    except Exception as e:
        print(f"Error fetching comments: {e}")
        return jsonify({"error": "Failed to fetch comments", "details": str(e)}), 500

# 20. Add new comment (for Contact.html)
@app.route("/api/comments", methods=["POST"])
def add_comment():
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    message = data.get("message")

    if not all([name, email, message]):
        return jsonify({"error": "Name, email, and message are required"}), 400

    try:
        comment_data = {
            "name": name,
            "email": email,
            "message": message,
            "created_at": datetime.utcnow(), 
            "likes": 0,
            "dislikes": 0,
            "replies": []
        }
        result = comments_collection.insert_one(comment_data)
        return jsonify({"message": "Comment added successfully", "id": str(result.inserted_id)}), 201
    except Exception as e:
        print(f"Error adding comment: {e}")
        return jsonify({"error": "Failed to add comment", "details": str(e)}), 500

# 21. Add reply to a comment (for Contact.html)
@app.route("/api/comments/<comment_id>/replies", methods=["POST"])
def add_reply_to_comment(comment_id):
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    message = data.get("message")

    if not all([name, email, message]):
        return jsonify({"error": "Name, email, and message are required for reply"}), 400

    try:
        reply_data = {
            "_id": ObjectId(), 
            "name": name,
            "email": email,
            "message": message,
            "created_at": datetime.utcnow(), 
            "likes": 0,
            "dislikes": 0
        }
        
        result = comments_collection.update_one(
            {"_id": ObjectId(comment_id)},
            {"$push": {"replies": reply_data}}
        )
        
        if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Use PORT from environment or default to 5000
    app.run(host="0.0.0.0", port=port)
