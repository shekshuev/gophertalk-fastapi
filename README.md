# GopherTalk

GopherTalk is a **learning project** designed to explore the development of a lightweight social network inspired by platforms like X. This project demonstrates foundational concepts in backend development, database optimization, and performance scaling using FastAPI and PostgreSQL.

---

## 🚀 Features

- **User Profiles**: Register, log in, and view user profiles.
- **Posts**: Create, read, and delete posts.
- **Likes and Views**: Track user interactions and post popularity.
- **Optimized Database**: Utilizes techniques such as denormalization, partitioning, and replication for scalability.
- **RESTful API**: Built with Go for high performance and simplicity.

## 🛠️ Tech Stack

- **Backend**: Python ([FastAPI](https://fastapi.tiangolo.com/))
- **Database**: [PostgreSQL](https://www.postgresql.org/)

## 🧑‍💻 Getting Started

### Prerequisites

- [Python](https://www.python.org/) (v3.8 or later)
- [PostgreSQL](https://www.postgresql.org/) (v15 or later)

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/shekshuev/gophertalk-fastapi
   cd gophertalk-fastapi
   ```

2. Set up environment variables from `.env.example` file.

3. Install dependencies:

   ```bash
   poetry install
   ```

4. Run migrations:

   ```bash
   ...
   ```

5. Start the server:
   ```bash
   poetry run python src/app.py
   ```

## 🛠️ API Endpoints

### Users

#### **GET /v1.0/users**

Retrieve a list of all users.

- **Query Parameters**:
  - `limit` (optional): Maximum number of users to retrieve (default: `10`).
  - `offset` (optional): Number of users to skip (default: `0`).
- **Response**:
  ```json
  [
    {
      "id": 1,
      "user_name": "johndoe",
      "first_name": "John",
      "last_name": "Doe",
      "status": 1,
      "created_at": "2024-01-01T12:00:00Z",
      "updated_at": "2024-01-02T12:00:00Z"
    }
  ]
  ```
- **Response Codes**:
  - `200 OK`: List of users.
  - `400 Bad Request`: Error while processing the request.

### **GET /v1.0/users/{id}**

Retrieve details of a specific user.

- **Path Parameters**:
  - `id` (required): ID of the user.
- **Response**:
  ```json
  {
    "id": 1,
    "user_name": "johndoe",
    "first_name": "John",
    "last_name": "Doe",
    "status": 1,
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-02T12:00:00Z"
  }
  ```
- **Response Codes**:
  - `200 OK`: User details.
  - `404 Not Found`: User not found.

### **PUT /v1.0/users/{id}**

Update user details.

- **Path Parameters**:
  - `id` (required): ID of the user.
- **Request Body**:
  ```json
  {
    "user_name": "newusername",
    "password": "newpassword",
    "password_confirm": "newpassword",
    "first_name": "NewFirstName",
    "last_name": "NewLastName"
  }
  ```
- **Response**:
  ```json
  {
    "id": 1,
    "user_name": "newusername",
    "first_name": "NewFirstName",
    "last_name": "NewLastName",
    "status": 1,
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-02T12:00:00Z"
  }
  ```
- **Response Codes**:
  - `200 OK`: User updated successfully.
  - `422 Unprocessable Entity`: Validation error.
  - `404 Not Found`: User not found.

### **DELETE /v1.0/users/{id}**

Delete a user by ID.

- **Path Parameters**:
  - `id` (required): ID of the user.
- **Response Codes**:
  - `204 No Content`: User deleted successfully.
  - `404 Not Found`: User not found.

### Posts

### **GET /v1.0/posts**

Retrieve a list of posts.

- **Query Parameters**:
  - `limit` (optional): Maximum number of posts to retrieve (default: `10`).
  - `offset` (optional): Number of posts to skip (default: `0`).
  - `reply_to_id` (optional): Filter posts by reply ID.
  - `search` (optional): Search keyword.
- **Response**:
  ```json
  [
    {
      "id": 1,
      "text": "Hello World!",
      "reply_to_id": null,
      "user": {
        "id": 1,
        "user_name": "johndoe",
        "first_name": "John",
        "last_name": "Doe"
      },
      "created_at": "2024-01-01T12:00:00Z",
      "likes_count": 10,
      "views_count": 100,
      "user_liked": false
    }
  ]
  ```
- **Response Codes**:
  - `200 OK`: List of posts.
  - `400 Bad Request`: Error while processing the request.

### **POST /v1.0/posts**

Create a new post.

- **Request Body**:
  ```json
  {
    "text": "This is my first post!",
    "reply_to_id": 123
  }
  ```
- **Response**:
  ```json
  {
    "id": 1,
    "text": "This is my first post!",
    "reply_to_id": 123,
    "user": {
      "id": 1,
      "user_name": "johndoe",
      "first_name": "John",
      "last_name": "Doe"
    },
    "created_at": "2024-01-01T12:00:00Z",
    "likes_count": 0,
    "views_count": 0,
    "user_liked": false
  }
  ```
- **Response Codes**:
  - `201 Created`: Post created successfully.
  - `422 Unprocessable Entity`: Validation error.

### **GET /v1.0/posts/{id}**

Retrieve a specific post by ID.

- **Path Parameters**:
  - `id` (required): ID of the post.
- **Response**:
  ```json
  {
    "id": 1,
    "text": "This is my first post!",
    "reply_to_id": null,
    "user": {
      "id": 1,
      "user_name": "johndoe",
      "first_name": "John",
      "last_name": "Doe"
    },
    "created_at": "2024-01-01T12:00:00Z",
    "likes_count": 10,
    "views_count": 100,
    "user_liked": true
  }
  ```
- **Response Codes**:
  - `200 OK`: Post details.
  - `404 Not Found`: Post not found.

### **DELETE /v1.0/posts/{id}**

Delete a post by ID.

- **Path Parameters**:
  - `id` (required): ID of the post.
- **Response Codes**:
  - `204 No Content`: Post deleted successfully.
  - `404 Not Found`: Post not found.

### **POST /v1.0/posts/{id}/view**

Mark a post as viewed by the current user.

- **Path Parameters**:
  - `id` (required): ID of the post.
- **Response Codes**:
  - `201 Created`: View recorded successfully.
  - `404 Not Found`: Post not found.

### **POST /v1.0/posts/{id}/like**

Like a post.

- **Path Parameters**:
  - `id` (required): ID of the post.
- **Response Codes**:
  - `201 Created`: Post liked successfully.
  - `404 Not Found`: Post not found.

### **DELETE /v1.0/posts/{id}/like**

Remove like from a post.

- **Path Parameters**:
  - `id` (required): ID of the post.
- **Response Codes**:
  - `204 No Content`: Like removed successfully.
  - `404 Not Found`: Post not found.

### Auth

### **POST /v1.0/auth/login**

Log in a user.

- **Request Body**:
  ```json
  {
    "user_name": "johndoe",
    "password": "password123"
  }
  ```
- **Response**:
  ```json
  {
    "access_token": "your-access-token",
    "refresh_token": "your-refresh-token"
  }
  ```
- **Response Codes**:
  - `200 OK`: Login successful.
  - `401 Unauthorized`: Invalid credentials.

### **POST /v1.0/auth/register**

Register a new user.

- **Request Body**:
  ```json
  {
    "user_name": "johndoe",
    "password": "password123",
    "password_confirm": "password123",
    "first_name": "John",
    "last_name": "Doe"
  }
  ```
- **Response**:
  ```json
  {
    "access_token": "your-access-token",
    "refresh_token": "your-refresh-token"
  }
  ```
- **Response Codes**:
  - `201 Created`: User registered successfully.
  - `422 Unprocessable Entity`: Validation error.

## 📝 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE.md) file for details.

---

## ⚠️ Disclaimer

This project is for **educational purposes only**. It is not designed for production use and may contain experimental or incomplete implementations.
