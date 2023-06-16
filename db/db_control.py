import sqlite3
import sqlite3 as sq


async def db_connect() -> None:
    global db, cur

    db = sq.connect('quotations.db')
    cur = db.cursor()

    cur.execute(
        "CREATE TABLE IF NOT EXISTS quotations(sn TEXT, users TEXT)")

    db.commit()


async def db_get_users(sn) -> str:
    db_users = cur.execute("SELECT users FROM quotations WHERE sn = ?", (sn, )).fetchone()
    if db_users is not None:
        return str(db_users[0])
    else:
        return ""




async def add_quotation(sn, user) -> sqlite3.Cursor:
    new_quotation = cur.execute("INSERT INTO quotations (sn, users) VALUES (?, ?)", (sn, user))
    db.commit()
    return new_quotation


async def edit_quotation(sn, users) -> None:
    cur.execute(f"UPDATE quotations SET users = ? WHERE sn = ?", (users, sn))
    db.commit()
