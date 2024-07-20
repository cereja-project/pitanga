
# Pitanga

Welcome to Pitanga, the hidden gem of your database operation toolkit in Python! Just like the pitanga fruit, our library is small, vibrant, and packed with value. Pitanga is designed to make your interactions with PostgreSQL databases more efficient, robust, and enjoyable.

## Funcionalidades

Pitanga is loaded with features that will transform the way you handle database operations:

- Efficient Connection: Utilize a connection pool to keep your operations fast and stable.
- Batch Queries: Execute SELECT queries in batches, leveraging multithreading to handle large volumes of data with ease.
- Safe Updates and Deletes: Perform UPDATE and DELETE operations with automatic commit, ensuring data integrity.
- Optimized Record Counting: Count records efficiently, even in complex queries with DISTINCT.
- Robust Error Handling: Integrated mechanisms to capture and handle errors effectively, keeping your system resilient.

## Installation

You can install the Pitanga library directly from GitHub:

```bash
pip install git+https://github.com/cereja-project/pitanga.git
```

## Usage

With Pitanga, your database operations become as easy as enjoying a fresh pitanga. Here's how:

```python
import logging
from pitanga import DatabaseOperations, DataBaseUpdateError, InvalidQueryError

# Basic logging configuration
logging.basicConfig(level=logging.INFO)

# Initialize database operations
db_operations = DatabaseOperations()

# SELECT query
try:
    results = db_operations.select("SELECT * FROM my_table", batch_size=100)
    for batch in results:
        print(batch)
except InvalidQueryError as e:
    logging.error(f"Query error: {e}")
except DataBaseUpdateError as e:
    logging.error(f"Database update error: {e}")

# UPDATE query
try:
    db_operations.update("UPDATE my_table SET column = value WHERE condition")
except InvalidQueryError as e:
    logging.error(f"Query error: {e}")
except DataBaseUpdateError as e:
    logging.error(f"Database update error: {e}")

# DELETE query
try:
    db_operations.delete("DELETE FROM my_table WHERE condition")
except InvalidQueryError as e:
    logging.error(f"Query error: {e}")
except DataBaseUpdateError as e:
    logging.error(f"Database update error: {e}")

# Close connections
db_operations.close_connection()
```

## Contribution

Pitanga is a community project and we welcome contributions! Feel free to open issues and pull requests on our GitHub repository. Together, we can make Pitanga even sweeter.

## Licença

This project is licensed under the MIT License.