# Tweet Management System_MongoDB

This project is a two-phase system for managing a MongoDB database of tweets. It provides tools for initializing the database and interacting with tweet data in a user-friendly manner.

## System Overview

### Phase 1: Database Initialization
The `load-json.py` script performs the following tasks:
- Initializes the MongoDB database.
- Creates a `tweets` collection.
- Populates the collection with data from a JSON file.
- Utilizes indexing to optimize querying.

### Phase 2: Interactive Functionalities
The `main.py` script provides the following functionalities:
- **Search tweets**: Find tweets based on keywords or criteria.
- **Find users**: Search for users in the database.
- **List top tweets/users**: Display top tweets and users based on various metrics.
- **Compose tweets**: Allow users to create and add new tweets.

This system emphasizes efficient data management, usability, and performance.

## Setup and Usage

### Prerequisites
- Python (3.x)
- MongoDB installed and running locally or on a server.
- Required Python packages (install via `pip`):
  ```bash
  pip install pymongo
  ```

### Steps to Run

1. **Load Initial Data**:
   - Place your JSON data file (e.g., `tweets.json`) in the project directory.
   - Run the `load-json.py` script to initialize the database:
     ```bash
     python load-json.py
     ```

2. **Start the Interactive Application**:
   - Run the `main.py` script to access the system's functionalities:
     ```bash
     python3 main.py
     ```

### Example Usage
- Search for tweets by keyword: `search keyword`
- List top 10 users: `list top users`
- Add a new tweet: `compose tweet`

## File Structure
- `load-json.py`: Script for initializing the database and loading JSON data.
- `main.py`: Interactive script for querying and managing tweet data.
- `tweets.json`: Example data file containing tweets (replace with your own).

## Future Improvements
- Add support for advanced filters and sorting.
- Enhance user interface with a web or GUI-based frontend.
- Implement additional analytics for tweet trends.

