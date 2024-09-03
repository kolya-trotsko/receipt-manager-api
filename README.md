## Description

This project provides a REST API for creating and viewing receipts, along with user registration and authentication. It allows users to create, retrieve, and manage receipts while maintaining user accounts and securing access via JWT-based authentication.

## Technologies

- Python 3.9+
- FastAPI
- PostgreSQL
- SQLAlchemy
- JWT for authentication
- Uvicorn for running the server

## API Endpoints

### User Registration

- **Endpoint:** `/register`
- **Method:** `POST`
- **Description:** Register a new user.
- **Request Body:**
  ```json
  {
    "name": "New User",
    "login": "newuser",
    "password": "newpass"
  }
  ```
- **Response:**
  - **Success (201 Created):** Returns user details with ID.
  - **Error (400 Bad Request):** Returns error message if registration fails.

### User Login

- **Endpoint:** `/login`
- **Method:** `POST`
- **Description:** Authenticate a user and obtain a JWT token.
- **Request Body:**
  ```json
  {
    "login": "user",
    "password": "pass"
  }
  ```
- **Response:**
  - **Success (200 OK):** Returns JWT token.
  - **Error (401 Unauthorized):** Returns error message if authentication fails.

### Create Receipt

- **Endpoint:** `/receipts`
- **Method:** `POST`
- **Description:** Create a new receipt.
- **Request Body:**
  ```json
  {
    "products": [
      {"name": "Product", "price": 10.0, "quantity": 2}
    ],
    "payment": {"type": "cash", "amount": 20.0}
  }
  ```
- **Headers:** `Authorization: Bearer <JWT_TOKEN>`
- **Response:**
  - **Success (201 Created):** Returns receipt details with ID.
  - **Error (400 Bad Request):** Returns error message if creation fails.

### Get Receipts

- **Endpoint:** `/receipts`
- **Method:** `GET`
- **Description:** Retrieve a list of receipts for the current user, with optional filters.
- **Query Parameters:**
  - `skip` (optional): Number of receipts to skip.
  - `limit` (optional): Number of receipts to retrieve.
  - `date_from` (optional): Start date for filtering.
  - `date_to` (optional): End date for filtering.
  - `min_total` (optional): Minimum total amount for filtering.
  - `max_total` (optional): Maximum total amount for filtering.
  - `payment_type` (optional): Filter by payment type.
- **Headers:** `Authorization: Bearer <JWT_TOKEN>`
- **Response:**
  - **Success (200 OK):** Returns a list of receipts.
  - **Error (401 Unauthorized):** Returns error message if authentication fails.

### Get Receipt by ID

- **Endpoint:** `/receipts/{receipt_id}`
- **Method:** `GET`
- **Description:** Retrieve a specific receipt by its ID.
- **Path Parameters:**
  - `receipt_id`: The ID of the receipt.
- **Headers:** `Authorization: Bearer <JWT_TOKEN>`
- **Response:**
  - **Success (200 OK):** Returns receipt details.
  - **Error (404 Not Found):** Returns error message if receipt is not found.
  - **Error (401 Unauthorized):** Returns error message if authentication fails.

### Public Receipt

- **Endpoint:** `/public/receipts/{receipt_id}`
- **Method:** `GET`
- **Description:** Retrieve a receipt in a public format without authentication.
- **Path Parameters:**
  - `receipt_id`: The ID of the receipt.
- **Query Parameters:**
  - `line_length` (optional): Maximum length of each line in the receipt.
- **Response:**
  - **Success (200 OK):** Returns the receipt in a formatted text.
  - **Error (404 Not Found):** Returns error message if receipt is not found.
