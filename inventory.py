"""Inventory operations for Loader Store."""

from database import get_connection, initialize_database


def add_part(part_name: str, part_number: str, quantity: int, unit_price: float):
    """Add a new part to inventory."""
    if not part_name.strip() or not part_number.strip():
        raise ValueError("Part name and part number are required.")
    if quantity < 0 or unit_price < 0:
        raise ValueError("Quantity and price cannot be negative.")

    initialize_database()
    with get_connection() as connection:
        cursor = connection.execute(
            """INSERT INTO parts (part_name, part_number, quantity, unit_price)
               VALUES (?, ?, ?, ?)""",
            (part_name.strip(), part_number.strip(), quantity, unit_price),
        )
        return cursor.lastrowid


def get_all_parts():
    """Return all inventory parts as dictionaries."""
    initialize_database()
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT id, part_name, part_number, quantity, unit_price "
            "FROM parts ORDER BY part_name"
        ).fetchall()
        return [dict(row) for row in rows]


def update_quantity(part_id: int, new_quantity: int):
    """Set the available quantity for a part."""
    if new_quantity < 0:
        raise ValueError("Quantity cannot be negative.")

    initialize_database()
    with get_connection() as connection:
        cursor = connection.execute(
            "UPDATE parts SET quantity = ? WHERE id = ?",
            (new_quantity, part_id),
        )
        return cursor.rowcount == 1


def delete_part(part_id: int):
    """Delete a part by its database ID."""
    initialize_database()
    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM parts WHERE id = ?",
            (part_id,),
        )
        return cursor.rowcount == 1
