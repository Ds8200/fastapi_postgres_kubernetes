from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional, Any
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from contextlib import contextmanager, asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    init_db()
    yield
    # Shutdown (if needed in the future)

app = FastAPI(lifespan=lifespan)

# Database configuration
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
    "database": os.getenv("POSTGRES_DB", "coordinates_db"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "postgres")
}


class Coordinate(BaseModel):
    latitude: float
    longitude: float
    name: Optional[str] = None


class CoordinateResponse(BaseModel):
    id: int
    latitude: float
    longitude: float
    name: Optional[str] = None


@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)  # type: ignore[call-overload]
        yield conn
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()


def init_db():
    """Initialize database connection and create table if not exists"""
    try:
        # Test connection
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Ping the database
                cur.execute("SELECT 1")
                print("✓ Database connection successful!")

                # Create table if not exists
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS coordinates (
                        id SERIAL PRIMARY KEY,
                        latitude DOUBLE PRECISION NOT NULL,
                        longitude DOUBLE PRECISION NOT NULL,
                        name VARCHAR(255),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
                print("✓ Table 'coordinates' is ready")

    except psycopg2.OperationalError as e:
        print(f"✗ Database connection failed: {e}")
        print("Please check your database configuration and ensure PostgreSQL is running")
        raise
    except Exception as e:
        print(f"✗ Database initialization error: {e}")
        raise


@app.post("/coordinates", response_model=CoordinateResponse, status_code=status.HTTP_201_CREATED)
async def add_coordinate(coordinate: Coordinate):
    """Add a new coordinate"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    INSERT INTO coordinates (latitude, longitude, name)
                    VALUES (%s, %s, %s)
                    RETURNING id, latitude, longitude, name
                    """,
                    (coordinate.latitude, coordinate.longitude, coordinate.name)
                )
                result = cur.fetchone()
                conn.commit()
                return result
    except psycopg2.Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


@app.delete("/coordinates/{coordinate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_coordinate(coordinate_id: int):
    """Delete a coordinate by ID"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM coordinates WHERE id = %s",
                    (coordinate_id,)
                )
                if cur.rowcount == 0:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Coordinate with id {coordinate_id} not found"
                    )
                conn.commit()
    except HTTPException:
        raise
    except psycopg2.Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


@app.get("/coordinates", response_model=List[CoordinateResponse])
async def get_all_coordinates():
    """Get all coordinates"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT id, latitude, longitude, name FROM coordinates ORDER BY id"
                )
                results = cur.fetchall()
                return results
    except psycopg2.Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "Coordinates API is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
