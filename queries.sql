-- SQLite
DELETE FROM videos
WHERE rowid = (
    SELECT rowid
    FROM videos
    WHERE channel = 'Raeleg Pony'
    LIMIT 1
);